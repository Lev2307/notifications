import uuid
from datetime import datetime, timedelta
import pytz

from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _, get_language

from .tasks import create_notification_task, create_periodic_notification_task

from core.models import UrlBase

class NotificationId(models.Model):
    # the model defining the celery task id
    notification_id = models.CharField(max_length=300) # task id

    class Meta:
        verbose_name = 'Notification task id'
        verbose_name_plural = 'Notification task id`s'

    def __str__(self):
        return self.notification_id

class NotificationStatus(models.Model):
    # a model that defines and sets the status of an notification (completed, not completed, or it has been revoked)
    class Status(models.IntegerChoices):
        # all notification statuses
        NOT_COMPLITED = 0    
        COMPLITED = 1
        REVOKED = 2
    
    id = models.UUIDField( # uuid ( for example, 3010dp5141c-7b58-4e24-94ad-f1b9oisndh1252 )
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
    )
    notification_celery_id = models.OneToOneField( # a single relationship with the model defining the task's celery id
        NotificationId,
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        verbose_name=_("Celery id")
    )
    time_stamp = models.DateTimeField( # notification execution time
        _("Time stamp"),
        blank=True, 
        null=True
    )
    done = models.IntegerField( # the status of an notification (completed, not completed, or it has been revoked)
        _("Status"),
        choices=Status.choices, 
        default=Status.NOT_COMPLITED
    )

    class Meta:
        verbose_name = 'Notification status'
        verbose_name_plural = 'Notification statuses'

    def __str__(self):
        if self.done == False:
            return 'Not complited'
        elif self.done == 2:
            return 'Revoked'
        return 'Complited'
    
class NotificationBase(models.Model):
    # The general notification model referenced by the single and periodic notifications models
    class Meta:
        ordering = ['-created_time']

    id = models.UUIDField( # uuid ( for example,  3010dp5141c-7b58-4e24-94ad-f1b9oisndh12 )
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    user = models.ForeignKey(
        'authentication.MyUser', 
        null=True, 
        on_delete=models.SET_NULL,
        verbose_name=_("User"),
    )
    created_time = models.DateTimeField( # notification creation time
        _("Created at"),
        auto_now_add=True
    )
    task_id = models.ManyToManyField( # all tasks related to the notification
        NotificationId, 
        null=True,
        blank=True,
        verbose_name=_("Tasks"),
    )
    notification_type = models.CharField( # the notification type: single or periodic
        _("Notification"),
        max_length=30
    )

    def __str__(self):
        created_date = self.created_time.date()
        created_time = self.created_time.time().replace(microsecond=0)
        if self.notification_type == 'Single':
            return f'Single Notification, создал {self.user} в {created_date} {created_time}'
        if self.notification_type == 'Periodic':
            return f'Periodic notification, создал {self.user} в {created_date} {created_time}'

    def check_all_notifications_are_complited(self):
        # checking all complited notification statuses
        if self.notification_type == 'Single':
            return self.notification_single.notification_status.done == 1
        elif self.notification_type == 'Periodic':
            return (self.notification_periodic.notification_status.filter(done=1).count() == self.notification_periodic.notification_status.all().count())


class NotificationPeriodicity(UrlBase):
    # The periodic notification model
    id = models.UUIDField( # uuid ( for example,  3010dp5141c-7b58-4e24-94ad-f1b9oisndh12 )
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    notification_category = models.ForeignKey( # notfication category
        'notification_categories.NotificationCategory', 
        null=True, 
        on_delete=models.SET_NULL,
        default='study', 
        verbose_name=_("Category"),
    )
    title = models.CharField(
        _("Title"),
        max_length=100
    )
    text = models.TextField(
        verbose_name=_("Text"),
        max_length=350, 
    )
    notification_status = models.ManyToManyField( # all statuses related to the notification
        NotificationStatus, 
        verbose_name=_("Status"), 
        related_name='notification_periodic_statuses'
    )
    notification_periodicity_num = models.IntegerField( # the number of repetitions of the notification (if the user selected `every day' when creating a periodic notification )
        _("Number of repetitions"),
        default=0, 
    )
    notification_periodic_time = models.TimeField( # the notification execution time (hours, minutes, seconds)
        _("Time"), 
        default=timezone.now
    )
    notification_type_periodicity = models.OneToOneField( # connection with general notification model
        NotificationBase, 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='notification_periodic',
        verbose_name=_("Notification type")
    )
    dates = ArrayField( # all picked notification dates ( year-month-date ) ["2023-05-14", "2024-10-18"]
        models.CharField(max_length=30),
        verbose_name=_("Dates"),
    )

    class Meta:
        verbose_name = 'Notification periodic'
        verbose_name_plural = 'Notifications periodic'

    def __str__(self):
        return f'Periodic - `{self.title.capitalize()}`'

    def get_only_not_complited(self):
        '''Getting amount of all the incomplited statuses of an notification'''
        return self.notification_status.filter(done=0).count()

    def get_all_finished_time_stamps(self):
        ''' Getting all finished ( complited ) statuses'''
        return self.notification_status.filter(done=1).order_by('time_stamp')
    
    def get_all_revoked(self):
        '''Getting all revoked statuses whose time ( time_stamp ) is greater than now'''
        all_filtered_by_revoked_status = self.notification_status.filter(done=2).order_by('time_stamp') # Queryset of all revoked statuses
        all_filtered_by_revoked_status_and_timestamp = []
        for r in all_filtered_by_revoked_status:
            if r.time_stamp > timezone.now(): # if the time of revoked notification > timezone.now()
                all_filtered_by_revoked_status_and_timestamp.append(r) # add revoked status to the list
            else:
                NotificationId.objects.delete(notification_id=r.notification_celery_id)
        return all_filtered_by_revoked_status_and_timestamp

    
    def get_url_path(self):
        return reverse_lazy("notifications:detail_periodic_notification", kwargs={"pk": self.pk})

class NotificationSingle(UrlBase):
    # The single notification model
    id = models.UUIDField( # uuid ( for example, 3010dp5141c-7b58-4e24-94ad-f1b9oisndh1344 )
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    notification_category = models.ForeignKey( # notfication category, for example, study
        'notification_categories.NotificationCategory', 
        null=True, 
        on_delete=models.SET_NULL, 
        default='study', 
        verbose_name=_("Category"),
    )
    title = models.CharField(
        _("Title"),
        max_length=100
    )
    text = models.TextField(
        _("Text"),
        max_length=350, 
    )
    notification_date = models.DateField( # the notification execution date (year, month, day)
        _("Date"),
        default=timezone.now, 
    )
    notification_time = models.TimeField( # the notification execution time (hours, minutes, seconds)
        _("Time"),
        default=timezone.now, 
    )
    notification_status = models.OneToOneField( # connection with the status model
        NotificationStatus, 
        null=True,
        on_delete=models.CASCADE, 
        verbose_name=_("Status")
    )
    notification_type_single = models.OneToOneField( # connection with general notification model
        NotificationBase, 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='notification_single',
        verbose_name=_("Notification type")
    )

    class Meta:
        verbose_name = 'Notification single'
        verbose_name_plural = 'Notifications single'

    def __str__(self):
        return f'Single - `{self.title.capitalize()}`'

    def get_url_path(self):
        return reverse_lazy("notifications:detail_single_notification", kwargs={"pk": self.pk})

def create_task(instance, time):
    '''
        Input: instance -> notification model (single or periodic), time -> notification execution time
    '''
    timezone_now = timezone.now().strptime(timezone.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S') # time - now
    timezone_now = timezone.localtime(timezone.make_aware(timezone_now))
    if type(instance) == NotificationSingle:
        difference_seconds = (time - timezone_now).total_seconds() # the difference in seconds between the time of a single notification and now
        task = create_notification_task.apply_async(args=(instance.id, get_language()), eta=timezone_now + timedelta(seconds=difference_seconds)) # creating celery task, which will be executed via difference_seconds ( eta argument )

        model = NotificationId.objects.create(notification_id=task.id) # creating task model
        instance.notification_type_single.task_id.add(model) # adding task to the general model
        
        notif_status = NotificationStatus.objects.get(id=instance.notification_status.id) #search for a status model by id
        notif_status.notification_celery_id = model
        notif_status.save() # save status model 

    elif type(instance) == NotificationPeriodicity:
        notif_status = NotificationStatus.objects.create(time_stamp=time) # creating a notification status model with the time_stamp argument - the notification execution time
        task = create_periodic_notification_task.apply_async(args=(instance.id, notif_status.id, get_language()), eta=time) #  creating celery task, which will be executed in argument time 
        instance.notification_status.add(notif_status) # adding this status to the model

        model = NotificationId.objects.create(notification_id=task.id) # creating task model
        instance.notification_type_periodicity.task_id.add(model) # adding task to the general model
        notif_status.notification_celery_id = model 
        notif_status.save() # save status model 

@receiver(post_save, sender=NotificationSingle)
def post_created_single(sender, instance, **kwargs):
    '''After saving a single notification, the post_save method is executed, receiving its model as an argument'''
    notification_date = instance.notification_date
    notification_time = instance.notification_time
    two_times = str(notification_date) + ' ' + str(notification_time)
    two_times = datetime.strptime(two_times, '%Y-%m-%d %H:%M:%S') # save time in readable format
    two_times = timezone.localtime(timezone.make_aware(two_times), timezone=pytz.timezone(str(timezone.get_current_timezone())))
    create_task(instance, two_times)

@receiver(post_save, sender=NotificationPeriodicity)
def post_created_periodic(sender, instance, **kwargs):
    '''After saving a periodic notification, the post_save method is executed, receiving its model as an argument'''
    model = NotificationPeriodicity.objects.get(id=instance.id) # get periodic model
    for date in range(len(model.dates)):
        time = model.dates[date] + ' ' + f'{model.notification_periodic_time}'
        time = timezone.make_aware(datetime.strptime(time, '%Y-%m-%d %H:%M:%S'))
        time = timezone.localtime(time, timezone=pytz.timezone(str(timezone.get_current_timezone())))
        create_task(instance, time)
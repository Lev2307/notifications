import inspect
import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.conf import settings

import notifications.send_notifications as send_notifications


class UserTelegram(models.Model):
    id = models.UUIDField( # uuid ( for example,  3010dp5141c-7b58-4e24-94ad-f1b9oisndh12 )
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    telegram_user = models.CharField( # user tg account nickname
        _("User`s telegram username"),
        null=True, 
        blank=True, 
        max_length=150
    )
    chat_id = models.CharField( # telegram chat id
        _("Chat id"),
        null=True, 
        blank=True,
        max_length=10
    )
    started_time = models.DateTimeField( # the time of linking telegram to user
        _("Added at"),
        null=True, 
        blank=True
    )

    class Meta:
        verbose_name = 'User telegram account'
        verbose_name_plural = 'User telegram accounts'

    def __str__(self):
        return self.telegram_user

class ChooseSendingNotifications(models.Model):
    id = models.UUIDField( # uuid ( for example,  3010dp5141c-7b58-4e24-94ad-f1b9oisndh12 )
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    user = models.ForeignKey( # user
        'MyUser', 
        null=True, 
        on_delete=models.CASCADE
    )
    sender = models.CharField( # social network, which will be used to send notifications
        _("Social network"),
        max_length=25
    )
    active = models.BooleanField( # is this network active or not ( used or not )
        _("Active"),
        default=False
    )
    linked_network = models.BooleanField( # is this network attached to user
        _("Provided network"),
        default=False
    )
    slug = models.SlugField(
        _("Slug"),
        max_length=25, 
        null=True, 
        blank=True
    )

    class Meta:
        ordering = ['user', '-sender']
        verbose_name = 'Sending Network'
        verbose_name_plural = 'Sending Networks'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.sender)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f'User: {self.user}, network: {self.sender}'

class UserManager(BaseUserManager):
    def create_user(self, username="", email="", password="", **extra_fields):
        if not email:
            raise ValueError(_("Enter an email address"))
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username="", email="", password=""):
        user = self.create_user(email=email, password=password, username=username)
        user.is_superuser = True
        user.is_staff = True
        user.tz = settings.TZ_CHOICES[0][0]
        user.save(using=self._db)
        email = ChooseSendingNotifications.objects.create(sender='email', user=user)
        telegram = ChooseSendingNotifications.objects.create(sender='telegram', user=user)
        user.choose_sending.add(email)
        user.choose_sending.add(telegram)
        return user


class MyUser(AbstractUser):
    id = models.UUIDField( # uuid ( for example,  3010dp5141c-7b58-4e24-94ad-f1b9oisndh12 )
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    is_subscribed = models.BooleanField(
        _("Subscribed"),
        default=False,
    )
    choose_sending = models.ManyToManyField( # social networks through which notifications will be sent to the user
        ChooseSendingNotifications,
        verbose_name=_("Social networks"),
    )
    users_telegram = models.OneToOneField( # user attached telegram account
        UserTelegram, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        verbose_name=_("User tg"),
    )
    tz = models.CharField(
        _("Timezone"),
        choices=settings.TZ_CHOICES,
        max_length=100,    
        help_text=_("If you don`t know your timezone, please google it! This field is important for sending notifications correctly."),
    )

    objects = UserManager()
    
    def save(self, *args, **kwargs):
        from notification_categories.models import NotificationCategory
        super().save(*args, **kwargs)
        NotificationCategory.objects.get_or_create(name_type='study', color='#107a8b', slug='study')
        NotificationCategory.objects.get_or_create(name_type='work', color='#ba2121', slug='work')
        NotificationCategory.objects.get_or_create(name_type='sport', color='#e0c45c', slug='sport')

    def get_all_active_and_attached_networks(self):
        return [chosen.sender for chosen in self.choose_sending.all() if chosen.linked_network == True and chosen.active == True]

    def get_only_inactive_networks(self):
        return [chosen.sender for chosen in self.choose_sending.all() if chosen.active == False]

    def sender_functions(self):
        return [f for f in vars(send_notifications).values() if inspect.isfunction(f)]

    def get_timezone_name(self):
        for tz, name in settings.TZ_CHOICES:
            if self.tz == tz:
                return name

@receiver(pre_save, sender=MyUser)
def check_user_tz(sender, instance, **kwargs):
    user_tz = instance._meta.get_field('tz')
    user_tz.editable = False


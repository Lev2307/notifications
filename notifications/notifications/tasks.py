import pytz
from django.utils import timezone

from celery import shared_task
from celery.utils.log import get_task_logger



logger = get_task_logger(__name__)

@shared_task()
def create_notification_task(instance_id): 
   from .models import NotificationSingle, NotificationStatus

   notif_status_id = NotificationSingle.objects.get(id=instance_id).notification_status.id
   notification_status = NotificationStatus.objects.get(id=notif_status_id)
   if notification_status.done == False:
      notification_status.done = True
      notification_status.save()
   NotificationSingle.objects.filter(id=instance_id).update(notification_status=notification_status)

   user = NotificationSingle.objects.get(id=instance_id).notification_type_single.user
   all_notification_sender_types = user.get_all_active_and_attached_networks()
   all_sender_functions = user.sender_functions()
   if len(all_notification_sender_types) > 0:
      for f in all_sender_functions:
         if (f.__name__) in all_notification_sender_types:
            f(instance_id, model='single')

@shared_task()
def create_periodic_notification_task(instance_id, notification_status_id):
   from .models import NotificationPeriodicity, NotificationStatus
   notification_status = NotificationStatus.objects.get(id=notification_status_id)

   if notification_status.done == False:
      notification_status.done = True
   notification_status.save()
   
   user = NotificationPeriodicity.objects.get(id=instance_id).notification_type_periodicity.user
   all_notification_sender_types = user.get_all_active_and_attached_networks()
   all_sender_functions = user.sender_functions()
   if len(all_notification_sender_types) > 0:
      for f in all_sender_functions:
         if (f.__name__) in all_notification_sender_types:
            f(instance_id, model='periodic', notification_status_id=notification_status_id)

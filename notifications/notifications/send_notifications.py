import pytz
from datetime import datetime
import requests

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.conf import settings
from django.utils import timezone

def telegram(instance_id, model, notification_status_id=None):
    from .models import NotificationSingle, NotificationPeriodicity   
    if model == 'single':
        notification_single = NotificationSingle.objects.get(id=instance_id)
        time = (datetime.combine(notification_single.notification_date, notification_single.notification_time)).strftime('%B %d, %Y %H:%M:%S %p')
        user = NotificationSingle.objects.get(id=instance_id).notification_type_single.user
        welcome = _(f"👋 Hi, you have received a new notification!")
        category = str(_("Category")) + ": " + notification_single.notification_category.name_type
        title = str(_("Title"))+ ": " + notification_single.title
        text = str(_("Text"))+ ": " + notification_single.text
        time_str = str(_("Time"))+ ": " + str(time)
        message = welcome + '\n' + category + '\n' + title + '\n' + text + '\n' + time_str + '\n'
        return requests.post(url=settings.TELEGRAM_API_SENDING_MESSAGE, data={'chat_id': user.users_telegram.chat_id, 'text': message})
    elif model == 'periodic':
        user = NotificationPeriodicity.objects.get(id=instance_id).notification_type_periodicity.user
        notification_periodicity = NotificationPeriodicity.objects.get(id=instance_id)

        time_stamp = notification_periodicity.notification_status.get(id=notification_status_id).time_stamp
        time_stamp = timezone.localtime(time_stamp, timezone=pytz.timezone(str(timezone.get_current_timezone())))
        time_stamp = time_stamp.strftime('%B %d, %Y %H:%M:%S %p')
        
        welcome = _(f"👋 Hi, you have received a new notification!")
        category = str(_("Category")) + ": " + notification_periodicity.notification_category.name_type
        title = str(_("Title"))+ ": " + notification_periodicity.title
        text = str(_("Text"))+ ": " + notification_periodicity.text
        time_stamp_str = str(_("Time"))+ ": " + str(time_stamp)
        message = welcome + '\n' + category + '\n' + title + '\n' + text + '\n' + time_stamp_str + '\n'
        return requests.post(url=settings.TELEGRAM_API_SENDING_MESSAGE, data={'chat_id': user.users_telegram.chat_id, 'text': message})

def email(instance_id, model, notification_status_id=None):
    from .models import NotificationSingle, NotificationPeriodicity   
    if model == 'single':
        notification = NotificationSingle.objects.get(id=instance_id)
        user = NotificationSingle.objects.get(id=instance_id).notification_type_single.user
        email = user.email
        time = (datetime.combine(notification.notification_date, notification.notification_time)).strftime('%B %d, %Y %H:%M:%S %p')
        verificate_message = render_to_string('auth/email/notifications/email_new_single_notification.html', {
                                                                                    'user': user,
                                                                                    'notification': notification,
                                                                                    'time': time
                                                                                    })
        msg = EmailMessage(_('New notification'), verificate_message, to=[email])
        msg.content_subtype = "html"
        msg.send()
    elif model == 'periodic':
        notification_periodicity = NotificationPeriodicity.objects.get(id=instance_id)

        time_stamp = notification_periodicity.notification_status.get(id=notification_status_id).time_stamp
        time_stamp = timezone.localtime(time_stamp, timezone=pytz.timezone(str(timezone.get_current_timezone())))
        time_stamp = time_stamp.strftime('%B %d, %Y %H:%M:%S %p')

        user = NotificationPeriodicity.objects.get(id=instance_id).notification_type_periodicity.user
        email = user.email
        verificate_message = render_to_string('auth/email/notifications/email_new_periodic_notification.html', {
                                                                                    'user': user,
                                                                                    'notification': notification,
                                                                                    'time_stamp': time_stamp,
                                                                                    })
        msg = EmailMessage(_('New notification'), verificate_message, to=[email])
        msg.content_subtype = "html"
        msg.send()
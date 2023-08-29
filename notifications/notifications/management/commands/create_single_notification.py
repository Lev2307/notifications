from django.core.management.base import BaseCommand
from notifications.models import NotificationSingle, NotificationBase, NotificationPeriodicity, NotificationType, NotificationStatus
from authentication.models import MyUser
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create single notification object =3'
    def handle(self, *args, **options):
        timezone_now = timezone.now().strptime(timezone.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
        notification_status = NotificationStatus.objects.create()
        notification_type_single = NotificationBase.objects.create(user=MyUser.objects.get(username='admin'))
        create_single_task = NotificationSingle.objects.create(
            notification_task_type=NotificationType.objects.get(name_type='work'),
            text='created work single notification',
            notification_date=timezone_now.date(),
            notification_time=timezone_now.time().replace(microsecond=0),
            notification_status=notification_status,
            notification_type_single=notification_type_single,
        )
        self.stdout.write(self.style.SUCCESS('Successfully created new notification single object "%s"' % create_single_task))
        self.stdout.write(f'''
        notification task type - {create_single_task.notification_task_type},
        notification text - {create_single_task.text},
        notification date - {create_single_task.notification_date},
        notification time - {create_single_task.notification_time},
        notification status - {create_single_task.notification_status},
        notification base - {create_single_task.notification_type_single}
        ''')

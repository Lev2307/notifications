from django.core.management.base import BaseCommand
from notifications.models import NotificationSingle

class Command(BaseCommand):
    help = 'Delete all single notifications'

    def handle(self, *args, **options):
        NotificationSingle.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted all single notifications =3'))
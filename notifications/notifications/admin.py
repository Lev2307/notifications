from django.contrib import admin
from django.utils.html import format_html_join, format_html

from .models import NotificationSingle, NotificationPeriodicity, NotificationStatus, NotificationBase, NotificationId


# # Register your models here.
admin.site.register(NotificationId)
admin.site.register(NotificationStatus)
admin.site.register(NotificationSingle)
admin.site.register(NotificationPeriodicity)


@admin.register(NotificationBase)
class AdminNotificationBase(admin.ModelAdmin):
    list_display = ('__str__', 'get_notification_periodic_status', 'get_notification_single_status')

    def get_notification_periodic_status(self, obj):
        if obj.notification_periodic:
            return format_html_join(
                '\n', "<li><a href='/admin/notifications/notificationstatus/{}/change/'>{}</a></li>",
                ((notif_status.id, f"Status type `{notif_status}`") for notif_status in obj.notification_periodic.notification_status.all())
            )

    def get_notification_single_status(self, obj):
        if obj.notification_single:
            return format_html(
                "<li><a href='/admin/notifications/notificationstatus/{}/change/'>{}</a></li>",
                obj.notification_single.notification_status.id,
                f"Status type `{obj.notification_single.notification_status}`"
            )
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs
    
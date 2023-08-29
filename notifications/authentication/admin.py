from django.contrib import admin

from .models import MyUser, UserTelegram, ChooseSendingNotifications


# Register your models here.
admin.site.register(UserTelegram)
admin.site.register(ChooseSendingNotifications)

@admin.register(MyUser)
class AdminNotificationBase(admin.ModelAdmin):
    readonly_fields = ('tz', )
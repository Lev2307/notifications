from datetime import datetime

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from rest_framework import serializers

from notification_categories.models import NotificationCategory
from ..models import NotificationBase, NotificationSingle, NotificationPeriodicity, NotificationStatus
from .fields import NotificationCategoryFilteredPrimaryKeyRelatedField

def timezone_today_date():
    return timezone.localtime(timezone.now()).date()

class NotificationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationBase
        exclude = ("task_id", )


class NotificationSingleSerializer(serializers.ModelSerializer):  
    notification_category = NotificationCategoryFilteredPrimaryKeyRelatedField(queryset=NotificationCategory.objects.all())

    class Meta:
        model = NotificationSingle
        exclude = ('notification_status', 'notification_type_single')

    def validate(self, attrs):
        notification_date = attrs['notification_date']
        notification_time = attrs['notification_time']
        two_times = str(notification_date) + ' ' + str(notification_time)
        notif_time = datetime.strptime(two_times, '%Y-%m-%d %H:%M:%S')
        notif_time = timezone.localtime(timezone.make_aware(notif_time))
        created_time = timezone.localtime(timezone.now())
        if created_time >= notif_time:
            raise serializers.ValidationError(_('Notification date cannot be in the past!!!'))
        return super().validate(attrs)
        
class NotificationPeriodicSerializer(serializers.Serializer):
    notification_category = NotificationCategoryFilteredPrimaryKeyRelatedField(queryset=NotificationCategory.objects.all())
    title = serializers.CharField(max_length=100)
    text = serializers.CharField(max_length=350)
    notification_periodicity_num = serializers.IntegerField(initial=1, max_value=15, min_value=1)
    notification_periodic_time = serializers.TimeField(default=timezone.localtime(timezone.now()))
    dates = serializers.CharField(required=False, style={'base_template': 'input.html'}, initial='', help_text=_("Enter dates in appropriate format (yyyy-mm-dd), for example, 2023-08-15,2023-12-15 without any spaces!!!!!!!!"))
    dates_type = serializers.ChoiceField(choices=['Every day', 'Your own dates'])

    def validate(self, attrs):
        if attrs['dates_type'] == 'Every day':
            if attrs.get('dates'):
                raise serializers.ValidationError(_("If you want to enter your dates, you should choose `Your own dates`"))
        if attrs['dates_type'] == 'Your own dates':
            if not attrs.get('dates'):
                raise serializers.ValidationError(_("If you`ve chosen `your own dates`, please enter your dates in the field `dates`"))
            user_dates = attrs['dates'].split(',')
            for date in user_dates:
                try:
                    date = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    raise serializers.ValidationError(_("ENTER DATES IN APPROPRIATE FORMAT"))

                if date > datetime.strptime("2040-12-31", "%Y-%m-%d"):
                    raise serializers.ValidationError(_(f'This date {date.date()} is too late. Please enter a date no later than 2040 year =3'))

                if date.date() <= datetime.now().date():
                    raise serializers.ValidationError(_(f'This date {date.date()} should be in the future (not in the past and present =/ ) =3'))

        return super().validate(attrs)

class NotificationPeriodicListSerializer(serializers.ModelSerializer):
    notification_category = NotificationCategoryFilteredPrimaryKeyRelatedField(queryset=NotificationCategory.objects.all())

    class Meta:
        model = NotificationPeriodicity
        exclude = ('notification_status', 'notification_type_periodicity')


class NotificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationStatus
        fields = '__all__'
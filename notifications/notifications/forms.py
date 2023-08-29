from datetime import datetime, timedelta
import pytz

from django import forms
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from notification_categories.models import NotificationCategory
from config.celery import app

from .models import NotificationSingle, NotificationPeriodicity, NotificationId, NotificationStatus

class NotificationCreateForm(forms.ModelForm):
    notification_category = forms.ModelChoiceField(label=_("Category"), queryset=NotificationCategory.objects.all(), initial='study')
    notification_date = forms.DateField(label=_("Date"), widget=forms.SelectDateWidget())
    notification_time = forms.TimeField(label=_("Time"), widget=forms.TimeInput(attrs={'type': 'time'}))
    class Meta:
        model = NotificationSingle
        fields = ['notification_category', 'title', 'text', 'notification_date', 'notification_time']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['notification_category'].queryset = NotificationCategory.objects.filter(Q(user=self.user) | Q(user=None))
        self.fields['notification_date'].initial = timezone.localtime(timezone.now()).date()
        self.fields['notification_time'].initial = timezone.localtime(timezone.now()).time()

    def clean(self):
        cleaned_data = super().clean()
        notification_date = cleaned_data['notification_date']
        notification_time = cleaned_data['notification_time']
        two_times = str(notification_date) + ' ' + str(notification_time)
        notif_time = datetime.strptime(two_times, '%Y-%m-%d %H:%M:%S')
        notif_time = timezone.localtime(timezone.make_aware(notif_time))
        created_time = timezone.localtime(timezone.now())
        if created_time >=  notif_time:
            raise forms.ValidationError(_('Notification date cannot be in the past!!!'))

class NotificationSingleEditForm(forms.ModelForm):
    notification_category = forms.ModelChoiceField(label=_("Category"), queryset=NotificationCategory.objects.all(), initial='study')
    notification_date = forms.DateField(label=_("Date"), widget=forms.SelectDateWidget())
    notification_time = forms.TimeField(label=_("Time"), widget=forms.TimeInput(attrs={'type': 'time'}))
    class Meta:
        model = NotificationSingle
        fields = ['notification_category', 'title', 'text', 'notification_date', 'notification_time']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.notification_kwargs = kwargs.pop('notification_kwargs')

        super().__init__(*args, **kwargs)
        self.fields['notification_category'].queryset = NotificationCategory.objects.filter(Q(user=self.request.user) | Q(user=None))
        self.fields['notification_date'].initial = timezone.localtime(timezone.now()).date()
        self.fields['notification_time'].initial = timezone.localtime(timezone.now()).time()

    def clean(self):
        cleaned_data = super().clean()
        notification_date = cleaned_data['notification_date']
        notification_time = cleaned_data['notification_time']
        two_times = str(notification_date) + ' ' + str(notification_time)
        notif_time = datetime.strptime(two_times, '%Y-%m-%d %H:%M:%S')
        notif_time = timezone.localtime(timezone.make_aware(notif_time))
        created_time = timezone.localtime(timezone.now())
        if created_time >= notif_time:
            raise forms.ValidationError(_('Notification date cannot be in the past!!!'))

class PeriodicalNotificationCreateForm(forms.ModelForm):
    notification_category = forms.ModelChoiceField(label=_("Category"), queryset=NotificationCategory.objects.all(), initial='study')
    notification_periodicity_num = forms.IntegerField(label=_("Number of repetitions"), initial=1, min_value=1, max_value=15)
    class Meta:
        model = NotificationPeriodicity
        fields = ['notification_category', 'title', 'text', 'notification_periodic_time', 'notification_periodicity_num']
        widgets = {
            'notification_periodic_time' : forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')

        super().__init__(*args, **kwargs)
        self.fields['notification_category'].queryset = NotificationCategory.objects.filter(Q(user=self.request.user) | Q(user=None))
        self.fields['notification_periodic_time'].initial = timezone.localtime(timezone.now()).time()
    
    def clean(self):
        request_data = self.request.POST
        for value in request_data.values():
            if value == 'Every day':
                if request_data.get('dates'):
                    raise forms.ValidationError(_("If you want to enter your dates, you should choose `Your own dates`"))
            elif value == 'Your own dates':
                if not request_data.get('dates'):
                    raise forms.ValidationError(_("If you`ve chosen `Your own dates`, please enter your dates in the field `your own dates`"))
                user_dates = request_data.get('dates').split(',')
                for date in user_dates:
                    try:
                        date = datetime.strptime(date, "%Y-%m-%d")
                    except ValueError:
                        raise forms.ValidationError(_("ENTER DATES IN APPROPRIATE FORMAT"))
                    if date > datetime.strptime("2040-12-31", "%Y-%m-%d"):
                        raise forms.ValidationError(_(f'This date {date.date()} is too late. Please enter a date no later than 2040 year =3'))

class NotificationPeriodicEditForm(forms.ModelForm):
    notification_category = forms.ModelChoiceField(label=_("Category"), queryset=NotificationCategory.objects.all(), initial='study')
    notification_periodicity_num = forms.IntegerField(label=_("Number of repetitions"), initial=1, min_value=0, max_value=15)
    class Meta:
        model = NotificationPeriodicity
        fields = ['notification_category', 'title', 'text', 'notification_periodic_time', 'notification_periodicity_num']
        widgets = {
            'notification_periodic_time' : forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.notification_periodic_kwargs = kwargs.pop('notification_periodic_kwargs')

        super().__init__(*args, **kwargs)
        self.fields['notification_category'].queryset = NotificationCategory.objects.filter(Q(user=self.request.user) | Q(user=None))
        self.fields['notification_periodic_time'].initial = timezone.localtime(timezone.now()).time()
    
    def clean(self):
        request_data = self.request.POST
        for value in request_data.values():
            if value == 'Every day':
                if request_data.get('dates'):
                    raise forms.ValidationError(_("If you want to enter your dates, you should choose `Your own dates`"))
            if value == 'Your own dates':
                if not request_data.get('dates'):
                    raise forms.ValidationError(_("If you`ve chosen `Your own dates`, please enter your dates in the field `your own dates`"))
                user_dates = request_data.get('dates').split(',')
                for date in user_dates:
                    try:
                        date = datetime.strptime(date, "%Y-%m-%d")
                    except ValueError:
                        raise forms.ValidationError(_("ENTER DATES IN APPROPRIATE FORMAT"))
                    if date > datetime.strptime("2040-12-31", "%Y-%m-%d"):
                        raise forms.ValidationError(_(f'This date {date.date()} is too late. Please enter a date no later than 2040 year =3'))
    
    def save(self, commit=True):
        res = super().save(commit)
        for notification_status in res.notification_status.all():
            NotificationStatus.objects.get(id=notification_status.id).delete()

        for task in res.notification_type_periodicity.task_id.all():
            app.control.revoke(str(task), terminate=True, signal='SIGKILL')
            NotificationId.objects.get(notification_id=task).delete()

        current_date = timezone.localtime(timezone.now()).date()
        for value in self.request.POST.values():                       
            if value == 'Every day':
                dates = []
                for _ in range(self.cleaned_data.get('notification_periodicity_num')):
                    current_date = current_date + timedelta(days=1)
                    dates.append((current_date))
                res.dates = dates
            elif value == 'Your own dates':
                dates = self.request.POST.get('dates').split(',')
                dates = sorted(dates, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
                res.dates = dates
        res.save()

        return res
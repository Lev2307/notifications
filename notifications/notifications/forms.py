from datetime import datetime, timedelta

from django import forms
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.forms import SimpleArrayField

from crispy_forms import helper, layout

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

        notification_category_field = layout.Field(
            "notification_category", css_class="form-control w-25"
        )
        title_field = layout.Field(
            "title", css_class="form-control", placeholder=_("Title")
        )
        text_field = layout.Field(
            "text", css_class="form-control", placeholder=_("Text")
        )
        time_field = layout.Field(
            "notification_time", css_class="form-control"
        )
        submit_button = layout.Submit('submit', _('Create'), css_class='btn btn-primary mt-2')

        self.helper = helper.FormHelper()
        self.helper.form_class = 'form-vertical w-75'
        self.helper.form_method = 'post'
        self.helper.layout = layout.Layout(
            notification_category_field,
            layout.Div(title_field, css_class="mt-3"),
            layout.Div(text_field, css_class="mt-3"),
            layout.Row(
                layout.Column('notification_date', css_class="form-group col-6 mb-0"),
                layout.Column(time_field, css_class="form-group col-6 mb-0"),
                css_class="row mt-3"
            ),
            submit_button
        )

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

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['notification_category'].queryset = NotificationCategory.objects.filter(Q(user=self.user) | Q(user=None))
        self.fields['notification_date'].initial = timezone.localtime(timezone.now()).date()
        self.fields['notification_time'].initial = timezone.localtime(timezone.now()).time()

        notification_category_field = layout.Field(
            "notification_category", css_class="form-control w-25"
        )
        title_field = layout.Field(
            "title", css_class="form-control", placeholder=_("Title")
        )
        text_field = layout.Field(
            "text", css_class="form-control", placeholder=_("Text")
        )
        time_field = layout.Field(
            "notification_time", css_class="form-control"
        )
        submit_button = layout.Submit('submit', _('Edit'), css_class='btn btn-warning mt-2')

        self.helper = helper.FormHelper()
        self.helper.form_class = 'form-vertical w-75'
        self.helper.form_method = 'post'
        self.helper.layout = layout.Layout(
            notification_category_field,
            layout.Div(title_field, css_class="mt-3"),
            layout.Div(text_field, css_class="mt-3"),
            layout.Row(
                layout.Column('notification_date', css_class="form-group col-6 mb-0"),
                layout.Column(time_field, css_class="form-group col-6 mb-0"),
                css_class="row mt-3"
            ),
            submit_button
        )

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
    dates_type = forms.ChoiceField(
        label=_("Select dates"), 
        choices=[('Every day', _('Every day')), ('Your own dates', _('Your own dates'))], 
        initial="Every day", 
        widget=forms.RadioSelect(attrs={'onchange': 'check()'})
    )
    dates = SimpleArrayField(forms.CharField(max_length=30), label='', required=False)
    class Meta:
        model = NotificationPeriodicity
        fields = ['notification_category', 'title', 'text', 'notification_periodic_time', 'notification_periodicity_num', 'dates']
        widgets = {
            'notification_periodic_time' : forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        self.fields['notification_category'].queryset = NotificationCategory.objects.filter(Q(user=self.request.user) | Q(user=None))
        self.fields['notification_periodic_time'].initial = timezone.localtime(timezone.now()).time()

        notification_category_field = layout.Field(
            "notification_category", css_class="form-control w-25"
        )
        title_field = layout.Field(
            "title", css_class="form-control", placeholder=_("Title")
        )
        text_field = layout.Field(
            "text", css_class="form-control", placeholder=_("Text")
        )
        time_field = layout.Field(
            "notification_periodic_time", css_class="form-control"
        )
        notification_periodicity_num_field = layout.Field(
            "notification_periodicity_num", css_class="form-control"
        )
        dates_field = layout.Field(
            "dates", css_class="form-control d-none"
        )
        dates_type_field = layout.Div(
            layout.Field('dates_type', css_class="form-control"),
            css_class="myclass mt-2"
        )
        submit_button = layout.ButtonHolder(
            layout.Submit('submit', _('Create'), css_class='btn btn-primary mt-2')
        )
        self.helper = helper.FormHelper()
        self.helper.form_class = 'form-inline w-75'
        self.helper.form_method = 'post'
        self.helper.layout = layout.Layout(
            notification_category_field,
            layout.Div(title_field, css_class="mt-3"),
            layout.Div(text_field, css_class="mt-3"),
            time_field,
            notification_periodicity_num_field,
            dates_type_field,
            dates_field,
            submit_button
        )
    
    def clean(self):
        value = self.cleaned_data.get('dates_type')
        if value == 'Every day':
            if self.cleaned_data.get('dates'):
                raise forms.ValidationError(_("If you want to enter your dates, you should choose `Your own dates`"))
        elif value == 'Your own dates':
            if not self.cleaned_data.get('dates'):
                raise forms.ValidationError(_("If you`ve chosen `Your own dates`, please enter your dates in the field `your own dates`"))
            user_dates = self.cleaned_data.get('dates')
            for date in user_dates:
                try:
                    date = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    raise forms.ValidationError(_("ENTER DATES IN APPROPRIATE FORMAT"))
                if date > datetime.strptime("2040-12-31", "%Y-%m-%d"):
                    raise forms.ValidationError(_(f'This date {date.date()} is too late. Please enter a date no later than 2040 year =3'))

class NotificationPeriodicEditForm(forms.ModelForm):
    notification_category = forms.ModelChoiceField(label=_("Category"), queryset=NotificationCategory.objects.all(), initial='study')
    notification_periodicity_num = forms.IntegerField(label=_("Number of repetitions"), initial=1, min_value=1, max_value=15)
    dates_type = forms.ChoiceField(
        label=_("Select dates"), 
        choices=[('Every day', _('Every day')), ('Your own dates', _('Your own dates'))], 
        initial="Every day", 
        widget=forms.RadioSelect(attrs={'onchange': 'check()'})
    )
    dates = SimpleArrayField(forms.CharField(max_length=30), label='', required=False)
    class Meta:
        model = NotificationPeriodicity
        fields = ['notification_category', 'title', 'text', 'notification_periodic_time', 'notification_periodicity_num', 'dates']
        widgets = {
            'notification_periodic_time' : forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.notification_periodic_kwargs = kwargs.pop('notification_periodic_kwargs')

        super().__init__(*args, **kwargs)
        self.fields['notification_category'].queryset = NotificationCategory.objects.filter(Q(user=self.request.user) | Q(user=None))
        self.fields['notification_periodic_time'].initial = timezone.localtime(timezone.now()).time()

        notification_category_field = layout.Field(
            "notification_category", css_class="form-control w-25"
        )
        title_field = layout.Field(
            "title", css_class="form-control", placeholder=_("Title")
        )
        text_field = layout.Field(
            "text", css_class="form-control", placeholder=_("Text")
        )
        time_field = layout.Field(
            "notification_periodic_time", css_class="form-control"
        )
        notification_periodicity_num_field = layout.Field(
            "notification_periodicity_num", css_class="form-control"
        )
        dates_field = layout.Field(
            "dates", css_class="form-control d-none"
        )
        dates_type_field = layout.Div(
            layout.Field('dates_type', css_class="form-control"),
            css_class="myclass mt-2"
        )
        submit_button = layout.ButtonHolder(
            layout.Submit('submit', _('Edit'), css_class='btn btn-warning mt-2')
        )

        self.helper = helper.FormHelper()
        self.helper.form_class = 'form-inline w-75'
        self.helper.form_method = 'post'
        self.helper.layout = layout.Layout(
            notification_category_field,
            layout.Div(title_field, css_class="mt-3"),
            layout.Div(text_field, css_class="mt-3"),
            time_field,
            notification_periodicity_num_field,
            dates_type_field,
            dates_field,
            submit_button
        )
    
    def clean(self):
            value = self.cleaned_data.get('dates_type')
            if value == 'Every day':
                if self.cleaned_data.get('dates'):
                    raise forms.ValidationError(_("If you want to enter your dates, you should choose `Your own dates`"))
            elif value == 'Your own dates':
                if not self.cleaned_data.get('dates'):
                    raise forms.ValidationError(_("If you`ve chosen `Your own dates`, please enter your dates in the field `your own dates`"))
                user_dates = self.cleaned_data.get('dates')
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
        value = self.cleaned_data.get('dates_type')                     
        if value == 'Every day':
            dates = []
            for _ in range(self.cleaned_data.get('notification_periodicity_num')):
                current_date = current_date + timedelta(days=1)
                dates.append((current_date))
            res.dates = dates
        elif value == 'Your own dates':
            dates = self.cleaned_data.get('dates')
            dates = sorted(dates, key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
            res.dates = dates
        res.save()

        return res
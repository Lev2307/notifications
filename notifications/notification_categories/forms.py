from django import forms
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import NotificationCategory

class AddNotificationCategoryForm(forms.ModelForm):
    class Meta:
        model = NotificationCategory
        fields = ['name_type', 'color']        
        labels = {
            'name_type' : _('Category name'),
        }
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'})
        }
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def clean(self):
        name_type = self.cleaned_data['name_type']
        color = self.cleaned_data['color']
        if NotificationCategory.objects.filter(Q(user=self.request.user) | Q(user=None)).filter(Q(name_type=name_type) | Q(color=color)).exists():
            raise forms.ValidationError(_('Choose a different color or a different name for the notification type as it already exists'))

class EditNotificationCategoryForm(forms.ModelForm):
    class Meta:
        model = NotificationCategory
        fields = ['name_type', 'color']        
        labels = {
            'name_type' : _('Category name'),
        }
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'})
        }
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def clean(self):
        name_type = self.cleaned_data['name_type']
        color = self.cleaned_data['color']
        if NotificationCategory.objects.filter(Q(user=self.request.user) | Q(user=None)).filter(Q(name_type=name_type) | Q(color=color)).exists():
            raise forms.ValidationError(_('Choose a different color or a different name for the notification type as it already exists'))
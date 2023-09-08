from django import forms
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from crispy_forms import helper, layout

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
        name_type_field = layout.Field(
            'name_type', css_class="form-group", placeholder=_("Category name"),
        )
        color_field = layout.Field(
            'color', css_class="form-group mt-1",
        )
        submit_button = layout.Submit('submit', _('Create category'), css_class='btn btn-primary mt-2')

        self.helper = helper.FormHelper()
        self.helper.form_class = 'form-inline w-25'
        self.helper.form_method = 'post'
        self.helper.layout = layout.Layout(
            layout.Row(
                layout.Column(name_type_field, css_class="form-group col-9 mb-0"),
                layout.Column(color_field, css_class="form-group col-3 mb-0"),
                css_class="row"
            ),
            submit_button
        )

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
        name_type_field = layout.Field(
            'name_type', css_class="form-group", placeholder=_("Category name"),
        )
        color_field = layout.Field(
            'color', css_class="form-group mt-1",
        )
        submit_button = layout.Submit('submit', _('Edit category'), css_class='btn btn-primary mt-2')

        self.helper = helper.FormHelper()
        self.helper.form_class = 'form-inline w-25'
        self.helper.form_method = 'post'
        self.helper.layout = layout.Layout(
            layout.Row(
                layout.Column(name_type_field, css_class="form-group col-9 mb-0"),
                layout.Column(color_field, css_class="form-group col-3 mb-0"),
                css_class="row"
            ),
            submit_button
        )


    def clean(self):
        name_type = self.cleaned_data['name_type']
        color = self.cleaned_data['color']
        if NotificationCategory.objects.filter(Q(user=self.request.user) | Q(user=None)).filter(Q(name_type=name_type) | Q(color=color)).exists():
            raise forms.ValidationError(_('Choose a different color or a different name for the notification type as it already exists'))
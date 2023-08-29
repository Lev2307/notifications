from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm

from .models import MyUser


class RegisterForm(UserCreationForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        if MyUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_('This mail already exists'))
        return email
        
    class Meta:
        model = MyUser
        fields = ['username', 'email', 'password1', 'password2', 'tz']

class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False) 

class ChangeUserEmail(forms.ModelForm):
    password1 = forms.CharField(label=_("Your password"), strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    class Meta:
        model = MyUser
        fields = ['email', 'password1']
        labels = {
            'email': _('Your new email'),
        }

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs.pop('kwargs')
        super().__init__(*args, **kwargs)

    def clean(self):
        user = MyUser.objects.get(id=self.kwargs['pk'])
        if not user.check_password(self.cleaned_data['password1']) or MyUser.objects.filter(email=self.cleaned_data['email']).exists():
            raise forms.ValidationError(_('Your password is wrong or this email already exists'))

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm


from crispy_forms import helper, layout
from .models import MyUser


class RegisterForm(UserCreationForm):
    class Meta:
        model = MyUser
        fields = ['username', 'email', 'password1', 'password2', 'tz']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        username_field = layout.Field(
            "username", css_class="form-control", placeholder=_("Username")
        )
        email_field = layout.Field(
            "email", css_class="form-control", placeholder=_("Email")
        )
        password1_field = layout.Field(
            "password1", css_class="form-control",  placeholder=_("Password")
        )
        password2_field = layout.Field(
            "password2", css_class="form-control",  placeholder=_("Password confirmation")
        )
        tz_field = layout.Field(
            "tz", css_class="form-control"
        )
        submit_button = layout.Submit('submit', _('Create account'), css_class='btn btn-primary mt-2')

        self.helper = helper.FormHelper()
        self.helper.form_class = 'form-inline w-75'
        self.helper.form_method = 'post'
        self.helper.layout = layout.Layout(
            layout.Row(
                layout.Column(username_field, css_class="form-group col-6 mb-0"),
                layout.Column(email_field, css_class="form-group col-6 mb-0"),
                css_class="row"
            ),
            layout.Row(
                layout.Column(password1_field, css_class="form-group col-6 mb-0"),
                layout.Column(password2_field, css_class="form-group col-6 mb-0"),
                css_class="row mt-3"
            ),
            tz_field,
            submit_button
        )

    def clean_email(self):
        email = self.cleaned_data['email']
        if MyUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_('This mail already exists'))
        return email

class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(label=_("Remember me"), required=False) 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        username_field = layout.Field(
            "username", css_class="form-control", placeholder=_("Username")
        )
        password_field = layout.Field(
            "password", css_class="form-control", placeholder=_("Password")
        )
        submit_button = layout.Submit('submit', _('Log in'), css_class='btn btn-primary mt-2')

        self.helper = helper.FormHelper()
        self.helper.form_class = 'form-inline w-50'
        self.helper.form_method = 'post'
        self.helper.layout = layout.Layout(
            layout.Div(username_field, css_class='mt-2'),
            layout.Div(password_field, css_class='mt-2'),
            'remember_me',
            submit_button
        )

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
        email_field = layout.Field(
            "email", css_class="form-control", placeholder=_("Email")
        )
        password_field = layout.Field(
            "password1", css_class="form-control", placeholder=_("Password")
        )
        submit_button = layout.Submit('submit', _('Change mail'), css_class='btn btn-primary mt-2')

        self.helper = helper.FormHelper()
        self.helper.form_class = 'form-inline w-50'
        self.helper.form_method = 'post'
        self.helper.layout = layout.Layout(
            layout.Div(email_field, css_class='mt-2'),
            layout.Div(password_field, css_class='mt-2'),
            submit_button
        )

    def clean(self):
        user = MyUser.objects.get(id=self.kwargs['pk'])
        if not user.check_password(self.cleaned_data['password1']) or MyUser.objects.filter(email=self.cleaned_data['email']).exists():
            raise forms.ValidationError(_('Your password is wrong or this email already exists'))

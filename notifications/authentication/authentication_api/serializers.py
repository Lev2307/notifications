from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import authenticate
from django.conf import settings

from rest_framework import serializers


from ..models import MyUser

class RegistrationSerializer(serializers.ModelSerializer):
    error_messages = {
        'password_mismatch': _('The two password fields didn’t match.'),
    }
    tz = serializers.ChoiceField(
        help_text=_('If you don`t know your timezone, please google it! This field is important for sending notifications correctly.'),
        label=_('Timezone'),
        choices=settings.TZ_CHOICES,
        required=True
    )
    password1 = serializers.CharField(
        label=_("Password"),
        style={"input_type": "password"}, 
        write_only=True
    )
    password2 = serializers.CharField(
        label=_("Password confirmation"),
        help_text=_("Enter the same password as before, for verification."),
        style={"input_type": "password"}, 
        write_only=True
    )
    class Meta:
        model = MyUser
        fields = ['username', 'email', 'password1', 'password2', 'tz']

    def validate(self, attrs):
        password1 = attrs["password1"]
        password2 = attrs["password2"]
        if password1 and password2 and password1 != password2:
            raise serializers.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return attrs
    
    def validate_email(self, email):
        if MyUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(_('This mail already exists'))
        return email

    def save(self, **kwargs):
        user = MyUser(
            username=self.validated_data['username'], 
            email=self.validated_data['email'], 
            tz=self.validated_data['tz'], 
        )
        password = self.validated_data['password1']
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        if username and password:
            user = authenticate(request=self.context.get('request'), username=username, password=password)
            if not user:
                msg = _('Access denied: wrong username or password.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Both "username" and "password" are required.')
            raise serializers.ValidationError(msg, code='authorization')
        attrs['user'] = user
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        exclude = ("id", "first_name", "last_name", "password", "groups", "choose_sending", "user_permissions")
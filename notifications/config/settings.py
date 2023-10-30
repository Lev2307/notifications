"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 4.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = int(os.environ.get('DEBUG')) # False for prod

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS').split(' ')


# Application definition
INSTALLED_APPS = [
    #django applications
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # third party
    'django_celery_results',
    'rest_framework',
    'social_django',
    'crispy_forms',
    
    # my appilications
    'authentication',
    'notifications',
    'notification_categories'
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "core.middleware.ThreadLocalMiddleware",
    "core.middleware.TimezoneMiddleware",
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('POSTGRES_ENGINE'),
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_DB_HOST'),
        'PORT': os.environ.get('POSTGRES_DB_PORT'),
        'CONN_MAX_AGE': 600,
    }
}
# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'authentication.MyUser'

from django.urls import reverse_lazy

LOGIN_REDIRECT_URL = reverse_lazy('notifications:notification_list')
LOGOUT_REDIRECT_URL = reverse_lazy('auth:login')

LOCALE_PATHS = [BASE_DIR / 'locale']

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

from django.utils.translation import gettext_lazy as _

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGE_CODE = "ru"

LANGUAGES = [
    ("ru", _("Russian")),
    ("en", _("English")),
    ("de", _("German")),
]

TZ_CHOICES = [
    ('Atlantic/Reykjavik', _('UTC 00:00 ( for example Reykjavik, Lisbon )')),
    ('Europe/London', _('UTC +01:00 ( for example, London, Dublin )')),
    ('Europe/Kaliningrad', _('UTC +02:00 ( for example, Kaliningrad, Berlin, Paris, Warsaw, Zagreb )')), 
    ('Europe/Moscow', _('UTC +03:00 ( for example, Moscow, Riga, Saint Petersburg, Minsk, Volgograd, Kirov )')), 
    ('Europe/Samara', _('UTC +04:00 ( for example, Baku, Tbilisi, Yerevan, Samara, Ulyanovsk )')), 
    ('Asia/Kabul', _('UTC +04:30 ( for example, Kabul )')), 
    ('Asia/Yekaterinburg', _('UTC +05:00 ( for example, Yekaterinburg, Tashkent )')), 
    ('Asia/Almaty', _('UTC +06:00 ( for example, Almaty, Omsk, Bishkek )')), 
    ('Asia/Krasnoyarsk', _('UTC +07:00 ( for example, Novosibirsk, Krasnoyarsk, Novokuznetsk, Bangkok, Hanoi, Jakarta )')), 
    ('Asia/Irkutsk', _('UTC +08:00 ( for example, Irkutsk, Beijing, Hong Kong, Singapore )')), 
    ('Asia/Yakutsk', _('UTC +09:00 ( for example, Yakutsk, Tokyo, Osaka )')), 
    ('Asia/Vladivostok', _('UTC +10:00 ( for example, Vladivostok, Canberra, Melbourne, Sydney )')), 
    ('Asia/Magadan', _('UTC +11:00 ( for example, Magadan, Solomon Islands, New Caledonia )')), 
    ('Asia/Kamchatka', _('UTC +12:00 ( for example, Fiji Islands, Kamchatka, Marshall Islands )')), 
    ('EST', _('UTC -05:00 ( Eastern US )')),
    ('US/Central', _('UTC -06:00 ( for example, Central America )')),
    ('US/Arizona', _('UTC -07:00 ( for example, Arizona )')),
    ('US/Alaska', _('UTC -08:00 ( for example, Alaska )')),
    ('US/Hawaii', _('UTC -10:00 ( for example, Hawaii )')),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ]
}

CELERY_BROKER_URL = 'redis://redis:6379'

# SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLICK_KEY = os.environ.get('STRIPE_PUBLICK_KEY')

WEBSITE_URL = os.environ.get('WEBSITE_URL')
TELEGRAM_API_SENDING_MESSAGE = os.environ.get('TELEGRAM_API_SENDING_MESSAGE')
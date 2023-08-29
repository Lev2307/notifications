"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

from notifications.views import redirect_user_view

urlpatterns = i18n_patterns(
    path('', redirect_user_view, name="redirect_user_view"),
    path('admin/', admin.site.urls),

    # api notifications
    path('api_notifications/', include(('notifications.notifications_api.urls', 'notifications_api'), namespace="notifications_api")),

    # Notifications
    path('notifications/', include(('notifications.urls', 'notifications'), namespace='notifications')),

    # Notification Categories
    path('notification_categories/', include(('notification_categories.urls', 'notification_categories'), namespace='notification_categories')),

    # api notification categories
    path('api_notification_categories/', include(
            ('notification_categories.notification_categories_api.urls', 'notification_categories_api'),
            namespace='notification_categories_api'
        )
    ),

    # Auth
    path('api-auth/', include(('authentication.authentication_api.urls', 'api-auth'), namespace="api-auth")),


    path('auth/', include(('authentication.urls', 'auth'), namespace='auth')),

)  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

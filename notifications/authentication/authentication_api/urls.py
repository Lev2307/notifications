from django.urls import path, include

from .api_views import RegisterApiView, LoginApiView, logoutApiView, UserProfileApiView

app_name = "api-auth"

urlpatterns = [
    path('registration-api', RegisterApiView.as_view(), name="registration_api"),
    path('login-api', LoginApiView.as_view(), name="login_api"),
    path('logout-api', logoutApiView, name="logout_api"),
    path('profile-api/<uuid:pk>/', UserProfileApiView.as_view(), name="user_profile_api")
]
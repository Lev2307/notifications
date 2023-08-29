from django.urls import path
from django.contrib.auth.views import PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView


from .views import (RegisterView,
                    UserLoginView,
                    UserLogoutView,
                    UserProfileView,
                    attaching_telegram_account_dispetcher,
                    dispetcher_providing_networks,
                    SenderInformationView,
                    activate_sender_network,
                    delete_telegram,
                    ChangeUserEmail,
                    verificate_user_email,
                    activate_user_email,
                    )     

app_name = 'auth'

urlpatterns = [
    path('registration/', RegisterView.as_view(), name="registration"),
    path('login/', UserLoginView.as_view(), name="login"),
    path('logout/', UserLogoutView.as_view(), name="logout"),
    path('profile/', UserProfileView.as_view(), name="profile"),
    path('telegram/', attaching_telegram_account_dispetcher, name="register_tg"),
    path('profile/dispetcher_providing_networks/<slug:slug>/', dispetcher_providing_networks, name="dispetcher_providing_networks"),
    path('profile/sender_info/<slug:slug>/', SenderInformationView.as_view(), name="sender_information"),
    path('profile/activate/<uuid:pk>/', activate_sender_network, name="activate_sender_network"),
    path('profile/delete_telegram/<uuid:pk>/', delete_telegram, name='delete_telegram'),
    path('profile/change_user_email/<uuid:pk>/', ChangeUserEmail.as_view(), name='changing_user_email'),
    path('profile/verificate_user_email/', verificate_user_email, name='verificate_user_email'),
    path('activate_user_email/<uidb64>/<token>/', activate_user_email, name='activate_user_email'),
    path('reset_password/', PasswordResetView.as_view(template_name='auth/email/reset_password/reset_password.html',
                                                                 html_email_template_name='auth/email/reset_password/reset_password_email.html'),
                                                                 name="password_reset"),
    path('reset_password_sent/', PasswordResetDoneView.as_view(template_name='auth/email/reset_password/reset_password_done.html'), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='auth/email/reset_password/reset_password_confirm.html'),name="password_reset_confirm"),
    path('reset_password_complete/', PasswordResetCompleteView.as_view(template_name='auth/email/reset_password/reset_password_complete.html'),name="password_reset_complete"),

]
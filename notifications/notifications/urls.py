from django.urls import path
from .views import (
    NotificationListView,
    NotificationSingleCreateView,
    NotificationSingleEditView, 
    NotificationSingleDeleteView,
    NotificationSingleDetailView, 
    PeriodicalNotificationCreateView,
    NotificationPeriodicDetailView,
    NotificationPeriodicListTimeStampsView,
    NotificationPeriodicRevokeCertainTimeStampView,
    NotificationPeriodicRevokeAllTimeStampsView,
    notificatePeriodicNotificationOnlyForAdmin,
    notificateSingleNotificationOnlyForAdmin,
    NotificationPeriodicDeleteView,
    NotificationPeriodicEditView,
    NotificationFinishedListView,
    change_notification_status_from_revoke_to_incomplete,
    SearchNotificationView
)

app_name = 'notifications'

urlpatterns = [
    path('read/', NotificationListView.as_view(), name="notification_list"),
    path('finished/', NotificationFinishedListView.as_view(), name="notification_archive_list"),

    path('create/', NotificationSingleCreateView.as_view(), name="create_notification"),
    path('create_periodical_notification/', PeriodicalNotificationCreateView.as_view(), name="create_periodical_notification"),
    path('edit/<uuid:pk>/', NotificationSingleEditView.as_view(), name="edit_notification"),
    path('edit_periodic/<uuid:pk>/', NotificationPeriodicEditView.as_view(), name="edit_periodic_notification"),
    path('delete/<uuid:pk>/', NotificationSingleDeleteView.as_view(), name="delete_notification"),
    path('delete_periodic/<uuid:pk>/', NotificationPeriodicDeleteView.as_view(), name="delete_periodic_notification"),
    path('single/<uuid:pk>/', NotificationSingleDetailView.as_view(), name="detail_single_notification"),
    path('periodic/<uuid:pk>/', NotificationPeriodicDetailView.as_view(), name="detail_periodic_notification"),

    path('notification_periodic_time_stamps_list/<uuid:pk>/', NotificationPeriodicListTimeStampsView.as_view(), name="notification_periodic_time_stamps_list"),
    path('revoke_certain_time_stamp/detail/<uuid:pk>/', NotificationPeriodicRevokeCertainTimeStampView.as_view(), name="notification_periodic_revoke_certain_time_stamp"),
    path('revoke_all_time_stamps/<uuid:pk>/', NotificationPeriodicRevokeAllTimeStampsView.as_view(), name="notification_periodic_revoke_all_time_stamps"),

    path('notificate_periodic_notification_only_for_admin/<uuid:pk>/', notificatePeriodicNotificationOnlyForAdmin, name="notificate_periodic_notification_only_for_admin"),
    path('notificate_single_notification_only_for_admin/<uuid:pk>/', notificateSingleNotificationOnlyForAdmin, name="notificate_single_notification_only_for_admin"),

    path('change_notification_status_from_revoke_to_incomplete/<uuid:pk>/', change_notification_status_from_revoke_to_incomplete, name="change_notification_status_from_revoke_to_incomplete"),

    path('search/', SearchNotificationView.as_view(), name='search_results'),

]
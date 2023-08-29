from django.urls import path

from .api_views import (
    NotificationListApiView,
    NotificationFinishedListApiView,

    NotificationSingleDetailApiView, 
    NotificationSingleCreateApiView, 
    NotificationSingleEditApiView, 
    NotificationSingleDeleteApiView,

    NotificationPeriodicDetailApiView, 
    NotificationPeriodicCreateApiView,
    NotificationPeriodicDeleteApiView, 
    NotificationPeriodicEditApiView,

    NotificationPeriodicTimeStampsListApiView,
    NotificationPeriodicRevokeCertainTimeStampApiView,
    NotificationPeriodicRevokeAllTimeStampsApiView,

    ChangeNotificationStatusFromRevokeToIncompleteApi
)

app_name = "notifications_api"

urlpatterns = [
    path('notifications_list/', NotificationListApiView.as_view(), name='notifications_list_api'),
    path('finished_notifications_list/', NotificationFinishedListApiView.as_view(), name='finished_notifications_list_api'),

    path('create_notification_single/', NotificationSingleCreateApiView.as_view(), name='create_notification_single_api'),
    path('edit_notification_single/<uuid:pk>/', NotificationSingleEditApiView.as_view(), name='edit_notification_single_api'),
    path('delete_notification_single/<uuid:pk>/', NotificationSingleDeleteApiView.as_view(), name='delete_notification_single_api'),
    path('single/<uuid:pk>/', NotificationSingleDetailApiView.as_view(), name='notification_single_detail_api'),

    path('create_notification_periodic/', NotificationPeriodicCreateApiView.as_view(), name='create_notification_periodic_api'),
    path('delete_notification_periodic/<uuid:pk>/', NotificationPeriodicDeleteApiView.as_view(), name='delete_notification_periodic_api'),
    path('edit_notification_periodic/<uuid:pk>/', NotificationPeriodicEditApiView.as_view(), name='edit_notification_periodic_api'),
    path('periodic/<uuid:pk>/', NotificationPeriodicDetailApiView.as_view(), name='notification_periodic_detail_api'),

    path('notification_periodic_time_stamps_list/<uuid:pk>/', NotificationPeriodicTimeStampsListApiView.as_view(), name='notification_periodic_time_stamps_list_api'),
    path('revoke_certain_notification_time_stamp/<uuid:pk>/', NotificationPeriodicRevokeCertainTimeStampApiView.as_view(), name='notification_periodic_revoke_certain_time_stamp_api'),
    path('revoke_all_notification_time_stamp/<uuid:pk>/', NotificationPeriodicRevokeAllTimeStampsApiView.as_view(), name='notification_periodic_revoke_all_time_stamps_api'),

    path('change_notification_status_from_revoke_to_incomplete/<uuid:pk>/', ChangeNotificationStatusFromRevokeToIncompleteApi.as_view(), name='change_notification_status_from_revoke_to_incomplete_api')

]
from django.urls import path

from .api_views import AddNotificationCategoryApiView, NotificationCategoryEditApiView, NotificationCategoryDeleteApiView

app_name = "notification_categories_api"

urlpatterns = [
    path('create_notification_category_api/', AddNotificationCategoryApiView.as_view(), name='create_notification_category_api'),
    path('edit_notification_category_api/<str:slug>/', NotificationCategoryEditApiView.as_view(), name='edit_notification_category_api'),
    path('delete_notification_category_api/<str:slug>/', NotificationCategoryDeleteApiView.as_view(), name='delete_notification_category_api'),

]
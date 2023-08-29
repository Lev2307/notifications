from django.urls import path

from .views import (
    AddNotificationCategoryView,
    EditNotificationCategoryView,
    DeleteNotificationCategoryView,

)
app_name = 'notification_categories'
urlpatterns = [
    path('add_notification_category/', AddNotificationCategoryView.as_view(), name="add_notification_category"),
    path('edit_notification_category/<str:slug>/', EditNotificationCategoryView.as_view(), name="edit_notification_category"),
    path('delete_notification_category/<str:slug>/', DeleteNotificationCategoryView.as_view(), name="delete_notification_category"),
]
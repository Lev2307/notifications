from django.db.models import Q

from rest_framework import generics, permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from .serializers import NotificationCategorySerilizer
from ..models import NotificationCategory

class AddNotificationCategoryApiView(generics.CreateAPIView):
    queryset = NotificationCategory.objects.all()
    serializer_class = NotificationCategorySerilizer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

class NotificationCategoryEditApiView(generics.UpdateAPIView):
    queryset = NotificationCategory.objects.all()
    serializer_class = NotificationCategorySerilizer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    lookup_field = 'slug'

class NotificationCategoryDeleteApiView(generics.DestroyAPIView):
    queryset = NotificationCategory.objects.all()
    serializer_class = NotificationCategorySerilizer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    lookup_field = 'slug'
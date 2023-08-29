
import json

from django.db.models import Q

from rest_framework import serializers

from notification_categories.models import NotificationCategory

class NotificationCategoryFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context.get('request', None)
        return NotificationCategory.objects.filter(Q(user=request.user) | Q(user=None))


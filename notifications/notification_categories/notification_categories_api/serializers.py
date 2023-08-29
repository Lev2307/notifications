from rest_framework import serializers


from ..models import NotificationCategory

class NotificationCategorySerilizer(serializers.ModelSerializer):
    class Meta:
        model = NotificationCategory
        exclude = ('user', 'slug')

    def create(self, validated_data):
        return NotificationCategory.objects.create(user=self.context['user'], **validated_data)
from rest_framework import serializers
from .models import Alarm


class AlarmSerializer(serializers.ModelSerializer):
    """
    Alarm 모델을 직렬화하는 Serializer
    """

    class Meta:
        model = Alarm
        fields = [
            "id",
            "recipient",
            "sender",
            "alarm_type",
            "message",
            "created_at",
            "related_object_id",
        ]
        read_only_fields = fields

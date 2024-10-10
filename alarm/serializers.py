from rest_framework import serializers
from alarm.models import Alarm


class AlarmSerializer(serializers.ModelSerializer):
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

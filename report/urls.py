from rest_framework import serializers
from .models import Report
from django.contrib.contenttypes.models import ContentType


class ReportCreateSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField()
    object_id = serializers.IntegerField()

    class Meta:
        model = Report
        fields = ["content_type", "object_id", "reason", "description"]

    def validate_content_type(self, value):
        try:
            return ContentType.objects.get(model=value)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Invalid content type")

    def create(self, validated_data):
        validated_data["reporter"] = self.context["request"].user
        return super().create(validated_data)

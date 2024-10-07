from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from .models import Report


class ReportCreateSerializer(serializers.ModelSerializer):
    """
    신고할 객체를 신고할 때, content_type, object_id, reason, description 필드를 전달
    """

    content_type = serializers.CharField()
    object_id = serializers.IntegerField()

    class Meta:
        model = Report
        fields = ["content_type", "object_id", "reason", "description"]

    def validate(self, data):
        content_type = data.get("content_type")
        object_id = data.get("object_id")

        try:
            model_class = ContentType.objects.get(model=content_type).model_class()
            model_class.objects.get(id=object_id)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Invalid content type")
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Object does not exist")

        return data

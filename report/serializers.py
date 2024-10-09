from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from .models import Report


class ReportCreateSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField()
    object_id = serializers.IntegerField()

    class Meta:
        model = Report
        fields = ["content_type", "object_id", "reason", "description"]

    def validate(self, data):
        content_type = data.get("content_type")
        object_id = data.get("object_id")

        try:
            app_label, model = content_type.split(".")
            model_class = apps.get_model(app_label, model)
            obj = model_class.objects.get(id=object_id)
        except (ValueError, LookupError):
            raise serializers.ValidationError("Invalid content type")
        except model_class.DoesNotExist:
            raise serializers.ValidationError("Object does not exist")

        # ContentType 객체를 가져와서 데이터에 저장
        data["content_type"] = ContentType.objects.get_for_model(model_class)
        return data

    def create(self, validated_data):
        reporter = self.context["request"].user
        return Report.objects.create(reporter=reporter, **validated_data)

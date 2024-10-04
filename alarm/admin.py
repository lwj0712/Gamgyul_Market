from django.contrib import admin
from .models import Alarm


@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sender",
        "recipient",
        "alarm_type",
        "message",
        "created_at",
    )
    search_fields = ("recipient__username", "sender__username", "message")
    ordering = ("-created_at",)

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class Alarm(models.Model):
    ALARM_TYPE_CHOICES = (
        ("message", "메시지"),
        ("follow", "팔로우"),
        ("comment", "댓글"),
        ("like", "좋아요"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, related_name="alarms", on_delete=models.CASCADE)
    sender = models.ForeignKey(
        User, related_name="sent_alarms", on_delete=models.CASCADE
    )
    alarm_type = models.CharField(max_length=20, choices=ALARM_TYPE_CHOICES)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.UUIDField(null=True, blank=True)  # 리디렉션 용

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_alarm_type_display()} - {self.recipient.username}에게"

    def get_redirect_url(self):
        if self.alarm_type == "message":
            # 메시지의 관련된 채팅방으로 이동 (예: 채팅방 상세 페이지)
            return reverse(
                "chat:room_detail", kwargs={"room_id": self.related_object_id}
            )

        elif self.alarm_type == "follow":
            # 팔로우한 사용자의 프로필 페이지로 이동
            return reverse(
                "accounts:profile", kwargs={"username": self.sender.username}
            )

        elif self.alarm_type == "comment" or self.alarm_type == "like":
            # 댓글이 달리거나 좋아요가 눌린 게시물로 이동
            return reverse(
                "posts:post_detail", kwargs={"post_id": self.related_object_id}
            )

        # 기본적으로 리디렉션 URL을 None으로 설정
        return None

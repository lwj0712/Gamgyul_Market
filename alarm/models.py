import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class Alarm(models.Model):
    """
    알림을 저장하는 모델
    """

    ALARM_TYPE_CHOICES = (
        ("message", "메시지"),
        ("follow", "팔로우"),
        ("comment", "댓글"),
        ("like", "좋아요"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User, related_name="alarms", on_delete=models.CASCADE
    )  # 알림을 받는 사용자
    sender = models.ForeignKey(
        User, related_name="sent_alarms", on_delete=models.CASCADE
    )  # 알림을 발생시킨 사용자
    alarm_type = models.CharField(max_length=20, choices=ALARM_TYPE_CHOICES)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.UUIDField(
        null=True, blank=True
    )  # 연관된 객체의 ID, 리디렉션 용

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_alarm_type_display()} - {self.recipient.username}에게"

    def get_redirect_url(self):
        """
        알림을 클릭했을 때, 해당 알림에 맞는 URL로 리디렉션
        """
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

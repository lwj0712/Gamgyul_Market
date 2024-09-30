import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatRoom(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )  # UUID로 방 ID 설정
    participants = models.ManyToManyField(
        User, related_name="chat_rooms"
    )  # 사용자와의 다대다 관계 설정
    name = models.CharField(max_length=255, blank=True)  # 채팅방 이름 필드 추가
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 채팅방 이름이 없을 경우 자동으로 생성
        if not self.name:
            participant_names = " & ".join(
                [participant.username for participant in self.participants.all()]
            )
            self.name = f"{participant_names}의 대화"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Message(models.Model):
    chat_room = models.ForeignKey(
        ChatRoom, related_name="messages", on_delete=models.CASCADE
    )  # 어느 채팅방의 메시지인지
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to="static/chat_images/", blank=True, null=True
    )  # 임시 저장 위치
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}님의 메시지"

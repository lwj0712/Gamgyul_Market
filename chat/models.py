import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name="chat_rooms")
    name = models.CharField(max_length=255, blank=True)
    room_key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # 객체를 저장하여 채팅방 ID가 생성되도록
        # 채팅방 이름 자동 생성
        if not self.name and self.participants.count() == 2:
            participant_names = ", ".join(
                [user.username for user in self.participants.all()]
            )
            self.name = f"{participant_names}의 대화"
            super().save(*args, **kwargs)  # 채팅방 이름이 설정된 후 다시 저장

    def __str__(self):
        return self.name


class Message(models.Model):
    """
    임시 이미지 저장 경로
    """

    chat_room = models.ForeignKey(
        ChatRoom, related_name="messages", on_delete=models.CASCADE
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="static/chat_images/", blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}님의 메시지"

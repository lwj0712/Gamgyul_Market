import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True)
    participants = models.ManyToManyField(User, related_name="chat_rooms")
    room_key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat Room"
        verbose_name_plural = "Chat Rooms"

    def save(self, *args, **kwargs):
        """
        채팅방 이름이 없고, 참여자가 두 명일 때 이름을 자동으로 생성
        """
        super().save(*args, **kwargs)
        if not self.name and self.participants.count() == 2:
            participant_names = ", ".join(
                [user.username for user in self.participants.all()]
            )
            self.name = f"{participant_names}의 대화"
            super().save(*args, **kwargs)

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
    image = models.ImageField(upload_to="chat_images/", blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.sender.username}님의 메시지"


class WebSocketConnection(models.Model):
    """
    WebSocket 연결 정보를 저장
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="ws_connections"
    )
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    connected_at = models.DateTimeField(auto_now_add=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} in {self.chat_room} - connected at {self.connected_at}"

    def mark_disconnected(self):
        self.disconnected_at = timezone.now()
        self.save()

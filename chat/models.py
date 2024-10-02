import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatRoom(models.Model):
    """
    사용자 간의 채팅방을 나타내는 모델
    - UUID를 primary key로 사용
    - 두 명의 사용자가 참가
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name="chat_rooms")
    name = models.CharField(max_length=255, blank=True)
    room_key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat Room"
        verbose_name_plural = "Chat Rooms"

    def save(self, *args, **kwargs):
        """
        채팅방 저장 시 이름 자동 생성
        - 이름이 없고, 참여자가 두 명일 때 이름을 자동으로 생성
        """
        super().save(*args, **kwargs)  # 객체를 저장하여 채팅방 ID가 생성되도록
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
    채팅방 내에서 전송된 메시지를 나타내는 모델
    - 텍스트 또는 이미지 메시지 가능
    - 임시 이미지 저장 경로
    """

    chat_room = models.ForeignKey(
        ChatRoom, related_name="messages", on_delete=models.CASCADE
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="static/chat_images/", blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.sender.username}님의 메시지"

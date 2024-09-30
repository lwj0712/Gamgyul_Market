from rest_framework import serializers
from .models import ChatRoom, Message
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = serializers.SlugRelatedField(
        many=True,
        slug_field="username",
        queryset=User.objects.all(),
        required=False,
    )

    class Meta:
        model = ChatRoom
        fields = ["id", "participants", "created_at"]

    def create(self, validated_data):
        participants = validated_data.pop("participants", [])
        chat_room = ChatRoom.objects.create(**validated_data)

        if participants:
            chat_room.participants.set(participants)
        return chat_room


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    image = serializers.ImageField(
        max_length=None, allow_empty_file=True, use_url=True, required=False
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "chat_room",
            "sender",
            "content",
            "image",
            "sent_at",
            "is_read",
        ]

    read_only_fields = ["id", "sender", "sent_at", "is_read"]

    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "이미지의 크기는 5MB를 넘지 않아야 합니다."
            )
        return value

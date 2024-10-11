from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import ChatRoom, Message

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        ref_name = "ChatAppUser"  # Serializer 충돌 방지


class ChatRoomSerializer(serializers.ModelSerializer):

    participants = serializers.SlugRelatedField(
        many=True,
        slug_field="username",
        queryset=User.objects.all(),
        required=True,
    )
    name = serializers.CharField(read_only=True)

    class Meta:
        model = ChatRoom
        fields = ["id", "participants", "name", "created_at"]

    def create(self, validated_data):
        """
        새로운 채팅방을 생성하는 로직. 참여자가 2명이어야 하며, 중복된 채팅방을 허용하지 않음
        참가자 ID를 정렬하여 room_key 생성
        """
        participants = validated_data.pop("participants")

        if len(participants) != 2:
            raise serializers.ValidationError("1대1 채팅만 가능합니다.")

        participant_ids = sorted([str(participant.id) for participant in participants])
        room_key = "_".join(participant_ids)

        if ChatRoom.objects.filter(room_key=room_key).exists():
            raise serializers.ValidationError("이미 이 사용자와의 채팅방이 존재합니다.")

        chat_room = ChatRoom.objects.create(room_key=room_key)
        chat_room.participants.set(participants)

        participant_usernames = ", ".join(
            sorted([participant.username for participant in participants])
        )
        chat_room.name = f"{participant_usernames}의 대화"
        chat_room.save()

        return chat_room


class MessageSerializer(serializers.ModelSerializer):
    """
    텍스트 또는 이미지로 메시지 전송 가능
    """

    sender = UserSerializer(read_only=True)
    image = serializers.ImageField(
        max_length=None, allow_empty_file=True, use_url=True, required=False
    )
    sent_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%fZ", read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "content",
            "image",
            "sent_at",
            "is_read",
        ]
        read_only_fields = ["id", "sender", "sent_at", "is_read"]

    def validate(self, data):
        content = data.get("content")
        image = data.get("image")
        if not content and not image:
            raise serializers.ValidationError(
                "메시지는 텍스트 또는 이미지를 포함해야 합니다."
            )
        return data

    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "이미지의 크기는 5MB를 넘지 않아야 합니다."
            )
        return value

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
        required=True,
    )
    name = serializers.CharField(read_only=True)

    class Meta:
        model = ChatRoom
        fields = ["id", "participants", "name", "created_at"]

    def create(self, validated_data):
        participants = validated_data.pop("participants")

        if len(participants) != 2:
            raise serializers.ValidationError("자신과의 채팅은 할 수 없습니다.")

        # 참가자 ID를 정렬하여 room_key 생성
        participant_ids = sorted([str(participant.id) for participant in participants])
        room_key = "_".join(participant_ids)

        # 중복 채팅방 체크
        if ChatRoom.objects.filter(room_key=room_key).exists():
            raise serializers.ValidationError("이미 이 사용자와의 채팅방이 존재합니다.")

        # 새로운 채팅방 생성
        chat_room = ChatRoom.objects.create(room_key=room_key)
        chat_room.participants.set(participants)

        # 채팅방 이름 생성
        participant_usernames = ", ".join(
            sorted([participant.username for participant in participants])
        )
        chat_room.name = f"{participant_usernames}의 대화"
        chat_room.save()

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

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from django.contrib.auth import get_user_model
from django.db.models import Count


User = get_user_model()


class ChatRoomListView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 현재 사용자가 속한 채팅방만 보여줌
        return self.request.user.chat_rooms.all()


class ChatRoomCreateView(generics.CreateAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ChatRoom.objects.all()

    def create(self, request, *args, **kwargs):
        participants = request.data.get("participants")
        if not participants:
            return Response({"error": "참여자 username이 필요합니다."}, status=400)

        if isinstance(participants, str):
            participants = participants.split(",")

        # 요청 보낸 사용자도 참가자로 포함
        participants = list(set(participants + [request.user.username]))

        if len(participants) != 2:
            return Response({"error": "1대1 채팅만 가능합니다."}, status=400)

        # 새로운 채팅방 생성
        serializer = self.get_serializer(data={"participants": participants})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=201)


class ChatRoomDetailView(generics.RetrieveAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        # 채팅방을 가져오고, 참가자 여부 확인
        chat_room = get_object_or_404(
            ChatRoom, id=self.kwargs["room_id"], participants=self.request.user
        )

        # 채팅방에 입장할 때 메시지 읽음 처리
        self.mark_all_messages_as_read(chat_room)

        return chat_room

    def mark_all_messages_as_read(self, chat_room):
        """
        채팅방에 입장할 때 해당 채팅방의 모든 안 읽은 메시지를 읽음 처리합니다.
        """
        messages = Message.objects.filter(chat_room=chat_room, is_read=False).exclude(
            sender=self.request.user
        )
        for message in messages:
            message.is_read = True
            message.save()


class ChatRoomLeaveView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        # 채팅방 나가기
        chat_room = get_object_or_404(
            ChatRoom, id=self.kwargs["room_id"], participants=self.request.user
        )
        chat_room.participants.remove(self.request.user)

        # 채팅방에 참여자가 없을 경우 삭제
        if not chat_room.participants.exists():
            chat_room.delete()

        return Response({"message": "채팅방에서 나갔습니다."}, status=204)


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 특정 채팅방의 메시지 목록 반환
        return Message.objects.filter(
            chat_room_id=self.kwargs["room_id"],
            chat_room__participants=self.request.user,
        )


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # 메시지 생성 시 현재 사용자를 발신자로 설정
        chat_room = get_object_or_404(
            ChatRoom, id=self.kwargs["room_id"], participants=self.request.user
        )
        # chat_room을 명시적으로 전달하지 않고 URL에서 가져와 처리
        serializer.save(sender=self.request.user, chat_room=chat_room)


class MessageReadView(generics.UpdateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, request, *args, **kwargs):
        # 메시지를 읽었을 때 is_read 상태를 True로 변경
        message = get_object_or_404(
            Message, id=self.kwargs["message_id"], chat_room_id=self.kwargs["room_id"]
        )

        # 메시지 발신자와 현재 요청한 사용자가 다를 때만 is_read 업데이트
        if message.sender != request.user:
            message.is_read = True
            message.save()
            return Response({"status": "읽음 표시됨"}, status=200)
        else:
            return Response(
                {"error": "자신이 보낸 메시지는 읽음 상태로 변경할 수 없습니다."},
                status=400,
            )

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer


User = get_user_model()


def get_chat_room_or_404(request, room_id):
    """
    참여자로 로그인한 사용자와 room_id를 기준으로 채팅방을 가져오는 함수
    """

    return get_object_or_404(ChatRoom, id=room_id, participants=request.user)


class ChatRoomListView(generics.ListAPIView):
    """
    현재 사용자가 속한 채팅방의 목록을 반환
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.chat_rooms.all()


class ChatRoomCreateView(generics.CreateAPIView):
    """
    요청한 사용자와 다른 1명의 사용자로 1대1 채팅방을 생성
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ChatRoom.objects.all()

    def create(self, request, *args, **kwargs):
        participants = request.data.get("participants", [])

        if not participants:
            return Response({"error": "참여자 username이 필요합니다."}, status=400)

        if isinstance(participants, str):
            participants = [p.strip() for p in participants.split(",")]

        participants.append(request.user.username)
        participants = list(set(participants))

        if len(participants) != 2:
            return Response({"error": "1대1 채팅만 가능합니다."}, status=400)

        serializer = self.get_serializer(data={"participants": participants})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(serializer.data, status=201)


class ChatRoomDetailView(generics.RetrieveAPIView):
    """
    요청한 사용자가 해당 채팅방의 참여자라면 채팅방을 가져옴
    채팅방에 입장할 때 읽지 않은 메세지 읽음 처리
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_object(self):
        chat_room = get_chat_room_or_404(self.request, self.kwargs["room_id"])
        self.mark_all_messages_as_read(chat_room)
        return chat_room

    def mark_all_messages_as_read(self, chat_room):
        """
        메시지의 읽음 상태를 한번에 업데이트
        """

        Message.objects.filter(chat_room=chat_room, is_read=False).exclude(
            sender=self.request.user
        ).update(is_read=True)


class ChatRoomLeaveView(generics.DestroyAPIView):
    """
    요청한 사용자가 채팅방을 나가고, 남은 참여자가 없으면 채팅방 삭제
    """

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        chat_room = get_chat_room_or_404(request, self.kwargs["room_id"])
        chat_room.participants.remove(request.user)

        if chat_room.participants.count() == 0:
            chat_room.delete()

        return Response({"message": "채팅방에서 나갔습니다."}, status=204)


class MessageListView(generics.ListAPIView):
    """
    요청한 사용자가 해당 채팅방의 참여자일 때만 메시지 목록 반환
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            chat_room_id=self.kwargs["room_id"],
            chat_room__participants=self.request.user,
        )


class MessageCreateView(generics.CreateAPIView):
    """
    메시지 생성 시 현재 사용자를 발신자로 설정
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        chat_room = get_chat_room_or_404(self.request, self.kwargs["room_id"])
        serializer.save(sender=self.request.user, chat_room=chat_room)

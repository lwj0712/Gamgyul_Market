from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
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
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="채팅방 목록 조회",
        description="현재 로그인한 사용자가 속한 채팅방의 목록을 반환합니다.",
        responses={200: ChatRoomSerializer(many=True)},
        tags=["chatroom"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Swagger 스키마 생성 시 오류 방지
        if getattr(self, "swagger_fake_view", False):
            return ChatRoom.objects.none()
        return self.request.user.chat_rooms.all()


class ChatRoomCreateView(generics.CreateAPIView):
    """
    요청한 사용자와 다른 1명의 사용자로 1대1 채팅방을 생성
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    queryset = ChatRoom.objects.all()

    @extend_schema(
        summary="채팅방 생성",
        description="요청한 사용자와 다른 1명의 사용자로 1대1 채팅방을 생성합니다.",
        request=ChatRoomSerializer,
        responses={
            201: ChatRoomSerializer,
            400: {
                "description": "잘못된 요청입니다.",
                "status": status.HTTP_400_BAD_REQUEST,
            },
        },
        examples=[
            OpenApiExample(
                "채팅방 생성 예시",
                summary="기본 채팅방 생성",
                description="사용자1과 사용자2가 1대1 채팅방을 생성하는 예시",
                value={
                    "participants": ["user2"],
                },
                request_only=True,
            ),
        ],
        tags=["chatroom"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

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
    채팅방에 입장할 때 읽지 않은 메시지 읽음 처리
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    @extend_schema(
        summary="채팅방 상세 조회",
        description="채팅방 ID를 기준으로 채팅방 정보를 반환합니다. 입장 시 읽지 않은 메시지를 모두 읽음으로 처리합니다.",
        responses={
            200: ChatRoomSerializer,
            404: {
                "description": "채팅방을 찾을 수 없습니다.",
                "status": status.HTTP_404_NOT_FOUND,
            },
        },
        tags=["chatroom"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

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

    permission_classes = [IsAuthenticated]
    serializer_class = None  # DestroyAPIView에서는 명시적으로 None으로 설정해야함

    @extend_schema(
        summary="채팅방 나가기",
        description="요청한 사용자가 채팅방에서 나가며, 남은 참여자가 없으면 채팅방을 삭제합니다.",
        responses={
            204: None,
            404: {
                "description": "채팅방을 찾을 수 없습니다.",
                "status": status.HTTP_404_NOT_FOUND,
            },
        },
        tags=["chatroom"],
    )
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
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="채팅방 메시지 목록 조회",
        description="해당 채팅방의 메시지 목록을 반환합니다.",
        responses={
            200: MessageSerializer(many=True),
            404: {
                "description": "채팅방을 찾을 수 없습니다.",
                "status": status.HTTP_404_NOT_FOUND,
            },
        },
        tags=["message"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Swagger 스키마 생성 시 오류 방지
        if getattr(self, "swagger_fake_view", False):
            return Message.objects.none()
        return Message.objects.filter(
            chat_room_id=self.kwargs["room_id"],
            chat_room__participants=self.request.user,
        )


class MessageCreateView(generics.CreateAPIView):
    """
    메시지 생성 시 현재 사용자를 발신자로 설정
    """

    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="채팅방 메시지 생성",
        description="메시지 생성 시 현재 사용자를 발신자로 설정합니다.",
        request=MessageSerializer,
        responses={
            201: MessageSerializer,
            404: {
                "description": "채팅방을 찾을 수 없습니다.",
                "status": status.HTTP_404_NOT_FOUND,
            },
        },
        tags=["message"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        chat_room = get_chat_room_or_404(self.request, self.kwargs["room_id"])
        serializer.save(sender=self.request.user, chat_room=chat_room)


class MessageSearchView(generics.ListAPIView):
    """
    주어진 키워드를 포함하는 메시지를 검색
    검색 결과가 없을 경우 빈 배열을 반환
    검색 결과가 있을 경우 직렬화하여 응답 반환
    """

    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="채팅방 메시지 검색",
        description="주어진 키워드를 포함하는 메시지를 검색합니다.",
        parameters=[
            OpenApiParameter(
                name="q", description="검색어", required=False, type=OpenApiTypes.STR
            ),
        ],
        responses={200: MessageSerializer(many=True)},
        tags=["message"],
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"message": "검색된 메시지가 없습니다.", "results": []},
                status=status.HTTP_200_OK,
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        # Swagger 스키마 생성 시 오류 방지
        if getattr(self, "swagger_fake_view", False):
            return Message.objects.none()

        chat_room = get_chat_room_or_404(self.request, self.kwargs["room_id"])
        query = self.request.query_params.get("q")
        if query:
            return Message.objects.filter(chat_room=chat_room, content__icontains=query)
        return Message.objects.filter(chat_room=chat_room)

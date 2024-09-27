from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import ChatRoom, Message, ChatParticipant
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model


User = get_user_model()


# 채팅방 뷰 (메시지 포함)
class ChatRoomView(LoginRequiredMixin, TemplateView):
    template_name = "chat/room.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_name = self.kwargs["room_name"]
        room = get_object_or_404(ChatRoom, name=room_name)
        messages = Message.objects.filter(room=room).order_by("sent_at")
        participant = (
            ChatParticipant.objects.filter(room=room)
            .exclude(user=self.request.user)
            .first()
        )
        context["room_name"] = f"{participant.user.username}님과의 대화"
        context["room"] = room
        context["messages"] = messages
        return context


# 채팅방 생성 뷰
class CreateChatRoomView(LoginRequiredMixin, View):
    template_name = "chat/create_room.html"
    success_url = reverse_lazy("chat:chatroom_list")

    def post(self, request, *args, **kwargs):
        target_user = request.POST.get(
            "target_user"
        )  # 상대방 유저 ID 또는 username 받아오기
        if not target_user:
            return render(
                request, self.template_name, {"error": "상대방을 선택해야 합니다."}
            )

        try:
            # 존재하는 사용자인지 확인
            target_user_instance = User.objects.get(username=target_user)
        except User.DoesNotExist:
            # 존재하지 않는 사용자인 경우 템플릿에 에러 메시지 전달
            return render(
                request, self.template_name, {"error": "존재하지 않는 사용자입니다."}
            )

        # 사용자 간 고유한 방을 만들기 위해 이름 생성
        sorted_users = sorted(
            [self.request.user.username, target_user_instance.username]
        )
        room_name = f"chat_{sorted_users[0]}_{sorted_users[1]}"

        # 방이 이미 존재하는지 확인
        room, created = ChatRoom.objects.get_or_create(name=room_name)

        # 새 방이 생성되었으면, 참여자 추가
        if created:
            ChatParticipant.objects.create(room=room, user=self.request.user)
            ChatParticipant.objects.create(room=room, user=target_user_instance)

        # 채팅방으로 리디렉션
        return redirect("chat:room", room_name=room.name)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


# 사용자가 참여한 채팅방 목록
class ChatRoomListView(LoginRequiredMixin, ListView):
    template_name = "chat/chatroom_list.html"
    context_object_name = "chat_rooms"

    def get_queryset(self):
        # 사용자가 참여한 채팅방을 가져오는지 확인
        chat_participants = ChatParticipant.objects.filter(
            user=self.request.user
        ).select_related("room")

        chat_rooms = []
        for participant in chat_participants:
            room = participant.room
            # 상대방의 이름을 찾기
            other_user = [
                p.user.username
                for p in room.chatparticipant_set.exclude(user=self.request.user)
            ]
            # 상대방의 이름이 존재할 경우
            if other_user:
                chat_rooms.append(
                    {
                        "room": room,
                        "room_name": f"{other_user[0]}님과의 대화",
                    }
                )

        return chat_rooms


# 메시지 생성 API (POST 요청)
class CreateMessageView(LoginRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_name):
        room = get_object_or_404(ChatRoom, name=room_name)

        # 사용자가 해당 방에 참여 중인지 확인
        if not ChatParticipant.objects.filter(room=room, user=request.user).exists():
            return Response({"error": "Access denied"}, status=403)

        content = request.data.get("message")
        if content:
            Message.objects.create(room=room, content=content, user=request.user)
            return Response({"message": "Message created successfully"}, status=201)

        return Response({"error": "Message content is required"}, status=400)


# 사용자가 참여한 방 목록 가져오기 API (GET 요청)
class GetUserRoomsView(LoginRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rooms = ChatParticipant.objects.filter(user=request.user).select_related("room")
        data = [
            {"room_name": room.room.name, "room_id": room.room.id} for room in rooms
        ]
        return Response(data)


# 특정 방의 메시지 목록 가져오기 API (GET 요청)
class GetChatMessagesView(LoginRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_name):
        room = get_object_or_404(ChatRoom, name=room_name)

        # 사용자가 해당 방에 참여 중인지 확인
        if not ChatParticipant.objects.filter(room=room, user=request.user).exists():
            return Response({"error": "Access denied"}, status=403)

        # 메시지 불러오기
        messages = Message.objects.filter(room=room).order_by("sent_at")[
            :50
        ]  # 최근 50개 메시지
        data = [
            {
                "user": message.user.username,
                "message": message.content,
                "sent_at": message.sent_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for message in messages
        ]
        return Response(data)


# 채팅방 나가기 기능
class LeaveRoomView(LoginRequiredMixin, View):
    def post(self, request, room_name):
        room = get_object_or_404(ChatRoom, name=room_name)

        participant = get_object_or_404(ChatParticipant, room=room, user=request.user)

        participant.delete()

        return redirect("chat:chatroom_list")

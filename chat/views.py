from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render, redirect, get_object_or_404
from .models import ChatRoom, Message, ChatParticipant
from django.contrib.auth.decorators import login_required


@login_required
def room(request, room_name):
    room = get_object_or_404(ChatRoom, name=room_name)
    messages = Message.objects.filter(room=room).order_by("sent_at")
    return render(request, "chat/room.html", {"room": room, "messages": messages})


@login_required
def create_room(request):
    if request.method == "POST":
        room_name = request.POST.get("room_name")
        if room_name:
            new_room = ChatRoom(name=room_name)
            new_room.save()

            ChatParticipant.objects.create(room=new_room, user=request.user)

            return redirect("chatroom_list")
    return render(request, "chat/create_room.html")


@login_required
def chatroom_list(request):

    chat_rooms = ChatParticipant.objects.filter(user=request.user).select_related(
        "room"
    )

    return render(request, "chat/chatroom_list.html", {"chat_rooms": chat_rooms})


@login_required
def create_message(request, room_name):
    if request.method == "POST":
        room = get_object_or_404(ChatRoom, name=room_name)

        if not ChatParticipant.objects.filter(room=room, user=request.user).exists():
            return redirect("chatroom_list")

        content = request.POST.get("message")
        if content:
            Message.objects.create(room=room, content=content, user=request.user)

    return redirect("room", room_name=room_name)


@api_view(["GET"])
@login_required
def get_user_rooms(request):
    user = request.user
    rooms = ChatParticipant.objects.filter(user=user).select_related("room")
    data = [{"room_name": room.room.name, "room_id": room.room.id} for room in rooms]
    return Response(data)


@api_view(["GET"])
@login_required
def get_chat_messages(request, room_name):
    try:
        room = ChatRoom.objects.get(name=room_name)

        if not ChatParticipant.objects.filter(room=room, user=request.user).exists():
            return Response({"error": "Access denied"}, status=403)

        messages = Message.objects.filter(room=room).order_by("sent_at")[
            :50
        ]  # 최근 50개 메시지
        data = [
            {
                "user": message.user.username if message.user else "Anonymous",
                "message": message.content,
                "sent_at": message.sent_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for message in messages
        ]
        return Response(data)
    except ChatRoom.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)

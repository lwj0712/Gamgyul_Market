from django.shortcuts import render, redirect, get_object_or_404
from .models import ChatRoom, Message


def room(request, room_name):
    room = get_object_or_404(ChatRoom, name=room_name)
    messages = Message.objects.filter(room=room).order_by("sent_at")
    return render(request, "chat/room.html", {"room": room, "messages": messages})


def create_room(request):
    if request.method == "POST":
        room_name = request.POST.get("room_name")
        if room_name:
            new_room = ChatRoom(name=room_name)
            new_room.save()
            return redirect("chatroom_list")
    return render(request, "chat/create_room.html")


def chatroom_list(request):
    chat_rooms = ChatRoom.objects.all()
    return render(request, "chat/chatroom_list.html", {"chat_rooms": chat_rooms})


def create_message(request, room_name):
    if request.method == "POST":
        room = get_object_or_404(ChatRoom, name=room_name)
        content = request.POST.get("message")
        if content:
            Message.objects.create(room=room, content=content)
    return redirect("room", room_name=room_name)

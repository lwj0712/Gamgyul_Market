from django.shortcuts import render, redirect


def room(request, room_name):
    return render(request, "chat/room.html", {"room_name": room_name})


def create_room(request):
    if request.method == "POST":
        room_name = request.POST.get("room_name")
        return redirect("room", room_name=room_name)
    return render(request, "chat/create_room.html")

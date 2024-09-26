from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("room/<str:room_name>/", views.ChatRoomView.as_view(), name="room"),
    path("create/", views.CreateChatRoomView.as_view(), name="create_room"),
    path("", views.ChatRoomListView.as_view(), name="chatroom_list"),
    path(
        "room/<str:room_name>/leave/", views.LeaveRoomView.as_view(), name="leave_room"
    ),
    # API endpoints
    path("api/user_rooms/", views.GetUserRoomsView.as_view(), name="get_user_rooms"),
    path(
        "api/chat_messages/<str:room_name>/",
        views.GetChatMessagesView.as_view(),
        name="get_chat_messages",
    ),
    path(
        "api/message/<str:room_name>/",
        views.CreateMessageView.as_view(),
        name="create_message",
    ),
]

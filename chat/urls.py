from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.ChatRoomListView.as_view(), name="room_list"),
    path("create/", views.ChatRoomCreateView.as_view(), name="room_create"),
    path("<uuid:room_id>/", views.ChatRoomDetailView.as_view(), name="room_detail"),
    path(
        "<uuid:room_id>/leave/",
        views.ChatRoomLeaveView.as_view(),
        name="room_leave",
    ),
    path(
        "<uuid:room_id>/messages/",
        views.MessageListView.as_view(),
        name="message_list",
    ),
    path(
        "<uuid:room_id>/messages/send/",
        views.MessageCreateView.as_view(),
        name="message_create",
    ),
    path(
        "<uuid:room_id>/messages/search/",
        views.MessageSearchView.as_view(),
        name="message_search",
    ),
]

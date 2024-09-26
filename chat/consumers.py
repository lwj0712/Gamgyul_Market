import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, ChatRoom
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    # 웹소켓 연결할 때 실행
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # 방 그룹에 참가
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    # 웹소켓 끊을 때 실행
    async def disconnect(self, close_code):
        # 방 그룹에서 탈퇴
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # 클라이언트로부터 웹소켓으로 메세지 받을 때 실행
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        user = self.scope["user"]
        room = await self.get_room(self.room_name)

        # 메시지 저장
        await self.save_message(room, user, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "user": user.username,
            },
        )

    # 그룹에서 메세지 받은 뒤 실행
    async def chat_message(self, event):
        message = event["message"]
        user = event["user"]

        await self.send(text_data=json.dumps({"message": message, "user": user}))

    @database_sync_to_async
    def get_room(self, room_name):
        return ChatRoom.objects.get(name=room_name)

    @database_sync_to_async
    def save_message(self, room, user, message):
        Message.objects.create(room=room, user=user, content=message)

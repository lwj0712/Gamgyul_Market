import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import ChatRoom

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    # 웹소켓 연결할 때 실행
    async def connect(self):
        # 채팅방에 연결
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        # 채팅방 권한 검사
        if await self.is_user_in_room(self.room_id, self.scope["user"]):
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    # 웹소켓 끊을 때 실행
    async def disconnect(self, close_code):
        # 방 그룹에서 나가기
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # 클라이언트로부터 웹소켓으로 메세지 받을 때 실행
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # 그룹에 메시지 전송
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", "message": message}
        )

    # 그룹에서 메세지 받은 뒤 실행
    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))

    @database_sync_to_async
    def is_user_in_room(self, room_id, user):
        try:
            chat_room = ChatRoom.objects.get(id=room_id)
            return chat_room.participants.filter(id=user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

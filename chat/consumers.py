import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import ChatRoom, Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    # 웹소켓 연결할 때 실행
    async def connect(self):
        try:
            # 채팅방에 연결
            self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
            self.room_group_name = f"chat_{self.room_id}"

            # 인증되지 않은 사용자 처리
            if not self.scope["user"].is_authenticated:
                await self.close()
                return

            # 채팅방 권한 검사
            if await self.is_user_in_room(self.room_id, self.scope["user"]):
                await self.channel_layer.group_add(
                    self.room_group_name, self.channel_name
                )
                await self.accept()
            else:
                await self.close()
        except KeyError:
            await self.close()

    # 웹소켓 끊을 때 실행
    async def disconnect(self, close_code):
        # 방 그룹에서 나가기
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message")
        message_id = text_data_json.get("message_id")

        if message:
            # 메시지 전송 처리
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat_message", "message": message}
            )

        if message_id:
            # 메시지 읽음 처리
            await self.mark_message_as_read(message_id)
            # 읽음 상태를 상대방에게 실시간으로 전송
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "message_read", "message_id": message_id, "is_read": True},
            )

    async def chat_message(self, event):
        # 그룹에서 수신한 메시지를 클라이언트에 전송
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))

    async def message_read(self, event):
        # 읽음 상태 업데이트 메시지 전송
        message_id = event["message_id"]
        is_read = event["is_read"]

        await self.send(
            text_data=json.dumps({"message_id": message_id, "is_read": is_read})
        )

    @database_sync_to_async
    def is_user_in_room(self, room_id, user):
        try:
            chat_room = ChatRoom.objects.get(id=room_id)
            return chat_room.participants.filter(id=user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            if not message.is_read:
                message.is_read = True
                message.save()
            return message
        except Message.DoesNotExist:
            return None

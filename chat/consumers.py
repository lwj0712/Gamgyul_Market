import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import ChatRoom, Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    # 웹소켓 연결할 때 실행
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        # 사용자 인증 여부 확인
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        # 채팅방 참여 여부 확인
        if await self.is_user_in_room(self.room_id, self.scope["user"]):
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
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
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "message_id": message_id,
                    "status": "received",
                },
            )

        if message_id:
            # 메시지 읽음 처리
            await self.mark_message_as_read(message_id)
            # 읽음 상태를 상대방에게 실시간으로 전송
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "message_read", "message_id": message_id, "is_read": True},
            )

    # 그룹에서 수신한 메시지를 클라이언트에 전송
    async def chat_message(self, event):
        message = event.get("message", None)
        message_id = event.get("message_id", None)

        if message_id is None:
            print(f"Error: message_id is None. event: {event}")

        # 클라이언트에게 메시지 전송
        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "message_id": message_id,
                    "status": "received",
                }
            )
        )

    async def message_read(self, event):
        message_id = event["message_id"]
        is_read = event["is_read"]

        # 메시지 ID와 읽음 상태를 클라이언트에 전송
        await self.send(
            text_data=json.dumps(
                {"message_id": message_id, "is_read": is_read, "status": "read"}
            )
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

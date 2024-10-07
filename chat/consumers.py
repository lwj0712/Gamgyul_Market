import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import ChatRoom, Message, WebSocketConnection

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    채팅방에서 WebSocket 연결 및 메시지 수신/송신을 처리하는 Consumer
    """

    async def connect(self):
        """
        클라이언트가 WebSocket에 연결할 때 호출
        - 사용자 인증 여부를 확인한 후, 채팅방 참여 여부를 검증
        - 참여 중인 경우 WebSocket 연결을 허용하고 그룹에 추가
        """
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

            # WebSocket 연결 정보를 저장
            await self.record_connection(self.scope["user"], self.room_id)
        else:
            await self.close()

    async def disconnect(self, close_code):
        """
        클라이언트가 WebSocket 연결을 끊을 때 호출
        - 그룹에서 사용자 제거
        - WebSocketConnection 모델을 사용해 연결 종료 시간 기록
        """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # WebSocket 연결 종료 시간 기록
        await self.mark_connection_as_disconnected(self.scope["user"], self.room_id)

    async def receive(self, text_data):
        """
        클라이언트로부터 메시지를 수신했을 때 호출
        - 메시지를 그룹에 전송하여 다른 참여자에게 전달
        - 메시지 ID가 포함된 경우 읽음 상태로 처리
        """
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
            # 읽음 상태를 실시간으로 그룹에 전송
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "message_read", "message_id": message_id, "is_read": True},
            )

    async def chat_message(self, event):
        """
        그룹으로부터 수신한 메시지를 클라이언트로 전송
        - 메시지 ID가 없으면 에러 출력
        """
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
        """
        읽음 상태를 그룹으로부터 수신하여 클라이언트에 전송
        """
        message_id = event["message_id"]
        is_read = event["is_read"]

        await self.send(
            text_data=json.dumps(
                {"message_id": message_id, "is_read": is_read, "status": "read"}
            )
        )

    @database_sync_to_async
    def is_user_in_room(self, room_id, user):
        """
        데이터베이스에서 사용자가 해당 채팅방에 참여 중인지 확인
        """
        try:
            chat_room = ChatRoom.objects.get(id=room_id)
            return chat_room.participants.filter(id=user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def record_connection(self, user, room_id):
        """
        WebSocket 연결 정보를 기록
        """
        chat_room = ChatRoom.objects.get(id=room_id)
        WebSocketConnection.objects.create(user=user, chat_room=chat_room)

    @database_sync_to_async
    def mark_connection_as_disconnected(self, user, room_id):
        """
        WebSocket 연결 종료 시간을 기록
        """
        chat_room = ChatRoom.objects.get(id=room_id)
        connection = (
            WebSocketConnection.objects.filter(user=user, chat_room=chat_room)
            .order_by("-connected_at")
            .first()
        )
        if connection:
            connection.mark_disconnected()

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """
        메시지를 읽음 상태로 업데이트
        """
        try:
            message = Message.objects.get(id=message_id)
            if not message.is_read:
                message.is_read = True
                message.save()
            return message
        except Message.DoesNotExist:
            return None

from channels.testing import WebsocketCommunicator
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase
from channels.routing import URLRouter
from asgiref.sync import async_to_sync, sync_to_async
from django.urls import re_path
from .models import ChatRoom, Message
from .consumers import ChatConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.auth import AuthMiddlewareStack
import json, uuid, asyncio

User = get_user_model()


class MockChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message = data.get("message")
        message_id = data.get("message_id")

        # 메시지의 is_read 상태를 업데이트
        if message_id:
            await sync_to_async(Message.objects.filter(id=message_id).update)(
                is_read=True
            )

        await self.send(
            text_data=json.dumps(
                {"message": message, "message_id": message_id, "status": "received"}
            )
        )

    async def disconnect(self, close_code):
        pass


# WebSocket 라우팅
application = AuthMiddlewareStack(
    URLRouter(
        [
            re_path(r"ws/chat/(?P<room_id>[0-9a-f-]+)/$", ChatConsumer.as_asgi()),
        ]
    )
)


class ChatRoomTestCase(APITestCase):
    def setUp(self):
        # 테스트에 사용할 사용자 계정 생성
        self.user1 = User.objects.create_user(
            username="user1", password="password123", nickname="user1_nickname"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="password123", nickname="user2_nickname"
        )
        self.user3 = User.objects.create_user(
            username="user3", password="password123", nickname="user3_nickname"
        )

        # 로그인 및 인증 설정
        self.client = APIClient()
        self.client.login(username="user1", password="password123")

    def test_chatroom_creation(self):
        """
        채팅방 생성 테스트: 새로운 채팅방이 성공적으로 생성되는지 검증합니다.
        """

        url = reverse("chat:room_create")
        data = {"participants": ["user2"]}  # user1은 자동으로 추가됨
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChatRoom.objects.count(), 1)
        self.assertIn("user1, user2의 대화", response.data["name"])

    def test_duplicate_chatroom_creation(self):
        """
        중복 채팅방 생성 방지 테스트: 동일한 참가자로 두 번째 채팅방 생성 시도를 막는지 검증합니다.
        """

        url = reverse("chat:room_create")
        data = {"participants": ["user2"]}

        # 첫 번째 방 생성
        self.client.post(url, data, format="json")

        # 같은 참가자로 또 생성 시도
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0], "이미 이 사용자와의 채팅방이 존재합니다.")

    def test_invalid_participants(self):
        """
        유효하지 않은 참가자 처리 테스트: 참가자가 두 명이 아닐 때 에러를 반환하는지 검증합니다.
        """

        url = reverse("chat:room_create")
        data = {"participants": ["user2", "user3"]}  # 세 명 이상일 때

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "1대1 채팅만 가능합니다.")

    def test_chatroom_leave(self):
        """
        채팅방 나가기 테스트: 사용자가 채팅방에서 성공적으로 나갈 수 있는지 검증합니다.
        """

        chatroom = ChatRoom.objects.create()
        chatroom.participants.set([self.user1, self.user2])

        url = reverse("chat:room_leave", kwargs={"room_id": chatroom.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(self.user1, chatroom.participants.all())

    def test_message_read_on_chatroom_entry(self):
        """
        채팅방 입장 시 메시지 읽음 처리 테스트: 채팅방에 입장하면 기존 메시지가 읽음으로 표시되는지 검증합니다.
        """

        chatroom = ChatRoom.objects.create()
        chatroom.participants.set([self.user1, self.user2])
        message = Message.objects.create(
            chat_room=chatroom, sender=self.user1, content="Hello!"
        )
        self.client.login(username="user2", password="password123")
        url = reverse("chat:room_detail", kwargs={"room_id": chatroom.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message.refresh_from_db()
        self.assertTrue(message.is_read)


class ChatRoomWebSocketTestCase(TransactionTestCase):
    def setUp(self):
        # 테스트에 사용할 사용자 계정 생성
        self.user1 = User.objects.create_user(
            username="user1", password="password123", nickname=f"user1_{uuid.uuid4()}"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="password123", nickname=f"user2_{uuid.uuid4()}"
        )

        # 채팅방 생성 및 참가자 설정
        self.chat_room = ChatRoom.objects.create()
        self.chat_room.participants.set([self.user1, self.user2])

        # 사용자1이 메시지를 보냄
        self.message = Message.objects.create(
            chat_room=self.chat_room, sender=self.user1, content="Hello!"
        )

        # Django 테스트 클라이언트를 사용하여 세션 생성 및 로그인
        self.client = Client()
        self.client.force_login(self.user1)
        self.session_key = self.client.cookies["sessionid"].value

    async def test_message_read_websocket(self):
        """
        WebSocket 메시지 읽음 처리 테스트: WebSocket을 통해 메시지를 수신하면 메시지가 읽음으로 표시되는지 검증합니다.
        """

        websocket_url = f"/ws/chat/{self.chat_room.id}/"

        # 세션 키를 헤더에 포함
        headers = [(b"cookie", f"sessionid={self.session_key}".encode("ascii"))]

        # WebSocketCommunicator 생성 시 헤더 전달
        communicator = WebsocketCommunicator(
            application, websocket_url, headers=headers
        )

        # WebSocket 연결
        connected, _ = await communicator.connect()
        self.assertTrue(
            connected, f"WebSocket 연결에 실패했습니다. 경로: {websocket_url}"
        )

        # 메시지 전송
        await communicator.send_json_to(
            {
                "message": "Test message",
                "message_id": self.message.id,
            }
        )

        # 응답 수신 및 검증
        response = await communicator.receive_json_from(timeout=60)
        print(f"WebSocket 수신 메시지: {response}")

        self.assertIn("message_id", response, "message_id가 수신되지 않았습니다.")
        self.assertEqual(response["message_id"], self.message.id)

        # 메시지의 is_read 상태 확인
        await sync_to_async(self.message.refresh_from_db)()
        self.assertTrue(self.message.is_read, "메시지가 읽음 처리되지 않았습니다.")

        await communicator.disconnect()

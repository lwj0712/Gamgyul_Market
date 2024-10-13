import json, uuid
from channels.testing import WebsocketCommunicator
from django.urls import reverse, re_path
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase
from channels.routing import URLRouter
from asgiref.sync import async_to_sync, sync_to_async
from channels.auth import AuthMiddlewareStack
from .models import ChatRoom, Message
from .consumers import ChatConsumer
from channels.generic.websocket import AsyncWebsocketConsumer

User = get_user_model()


class MockChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket 연결을 테스트하기 위한 MockChatConsumer.
    메시지 수신 시 읽음 상태로 업데이트
    """

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

        # 메시지 전송
        await self.send(
            text_data=json.dumps(
                {"message": message, "message_id": message_id, "status": "received"}
            )
        )

    async def disconnect(self, close_code):
        pass


# WebSocket 라우팅 설정
application = AuthMiddlewareStack(
    URLRouter(
        [
            re_path(r"ws/chat/(?P<room_id>[0-9a-f-]+)/$", ChatConsumer.as_asgi()),
        ]
    )
)


class ChatRoomTestCase(APITestCase):
    """
    ChatRoom API 관련 테스트
    """

    def setUp(self):
        """
        테스트용 사용자 생성 및 로그인 처리
        """
        # 데이터 초기화
        ChatRoom.objects.all().delete()
        Message.objects.all().delete()

        # 사용자 생성
        self.user1 = User.objects.create_user(
            email="newuser1@example.com",
            password="newpassword123",
            username="user1",
        )
        self.user2 = User.objects.create_user(
            email="newuser2@example.com",
            password="newpassword123",
            username="user2",
        )
        self.user3 = User.objects.create_user(
            email="newuser3@example.com",
            password="newpassword123",
            username="user3",
        )

        # 로그인 설정
        self.client = APIClient()
        self.client.login(email="newuser1@example.com", password="newpassword123")

    def test_chatroom_creation(self):
        """
        채팅방 생성 테스트: 새로운 채팅방이 성공적으로 생성되는지 검증
        """
        url = reverse("chat:room_create")
        data = {"participants": ["user2"]}  # user1은 자동으로 추가됨
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChatRoom.objects.count(), 1)
        self.assertIn("user1, user2의 대화", response.data["name"])

    def test_duplicate_chatroom_creation(self):
        """
        중복 채팅방 생성 방지 테스트: 동일한 참가자로 두 번째 채팅방 생성 시도 금지
        """
        url = reverse("chat:room_create")
        data = {"participants": ["user2"]}

        # 첫 번째 방 생성
        self.client.post(url, data, format="json")

        # 같은 참가자로 두 번째 생성 시도
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0], "이미 이 사용자와의 채팅방이 존재합니다.")

    def test_invalid_participants(self):
        """
        유효하지 않은 참가자 처리 테스트: 두 명이 아닌 참가자가 있을 경우 오류 발생.
        """
        url = reverse("chat:room_create")
        data = {"participants": ["user2", "user3"]}  # 세 명 이상일 때

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "1대1 채팅만 가능합니다.")

    def test_chatroom_leave(self):
        """
        채팅방 나가기 테스트: 사용자가 채팅방에서 성공적으로 나갈 수 있는지 검증
        """
        chatroom = ChatRoom.objects.create()
        chatroom.participants.set([self.user1, self.user2])

        url = reverse("chat:room_leave", kwargs={"room_id": chatroom.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(self.user1, chatroom.participants.all())

    def test_message_read_on_chatroom_entry(self):
        """
        채팅방 입장 시 메시지 읽음 처리 테스트: 입장 시 기존 메시지가 읽음으로 표시되는지 검증
        """
        chatroom = ChatRoom.objects.create()
        chatroom.participants.set([self.user1, self.user2])
        message = Message.objects.create(
            chat_room=chatroom, sender=self.user1, content="Hello!"
        )

        # user2로 로그인하고 채팅방 입장
        self.client.login(email="newuser2@example.com", password="newpassword123")
        url = reverse("chat:room_detail", kwargs={"room_id": chatroom.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 메시지가 읽음 처리되었는지 확인
        message.refresh_from_db()
        self.assertTrue(message.is_read)

    def test_message_search(self):
        """
        채팅방 메시지 검색 테스트: 키워드를 포함하는 메시지가 반환되는지 검증
        존재하지 않는 키워드로 검색 시 '검색된 메시지가 없습니다' 반환
        """
        chatroom = ChatRoom.objects.create()
        chatroom.participants.set([self.user1, self.user2])

        # 검색할 메시지 생성
        Message.objects.create(
            chat_room=chatroom, sender=self.user1, content="안녕하세요"
        )

        url = reverse("chat:message_search", kwargs={"room_id": chatroom.id})

        # 키워드 '안녕'으로 검색하여 '안녕하세요' 메시지를 찾는 테스트
        response = self.client.get(url, {"q": "안녕"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["content"], "안녕하세요")

        # 존재하지 않는 메시지를 검색
        response = self.client.get(url, {"q": "없는 메시지"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "검색된 메시지가 없습니다.")


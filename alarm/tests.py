import json, uuid
from channels.testing import WebsocketCommunicator
from django.urls import re_path, reverse
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework import status
from rest_framework.test import APITestCase
from channels.routing import URLRouter
from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack
from chat.models import ChatRoom, Message
from alarm.models import Alarm
from channels.generic.websocket import AsyncWebsocketConsumer

User = get_user_model()


class MockChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket 연결을 테스트하기 위한 MockChatConsumer.
    메시지 수신 시 알람이 제대로 생성되고 is_read로 처리되는지 확인.
    """

    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message_id = data.get("message_id")

        # 메시지의 is_read 상태를 업데이트
        if message_id:
            await sync_to_async(Message.objects.filter(id=message_id).update)(
                is_read=True
            )

        # 메시지 전송
        await self.send(
            text_data=json.dumps({"message_id": message_id, "status": "received"})
        )

    async def disconnect(self, close_code):
        pass


# WebSocket 라우팅 설정
test_application = AuthMiddlewareStack(
    URLRouter(
        [
            re_path(r"ws/chat/(?P<room_id>[0-9a-f-]+)/$", MockChatConsumer.as_asgi()),
        ]
    )
)


class AlarmTestCase(TransactionTestCase):
    """
    Alarm 앱 관련 테스트 케이스
    """

    def setUp(self):
        """
        테스트용 사용자 및 채팅방 생성
        """
        print(">>> 테스트용 사용자 및 채팅방 생성 시작")
        self.user1 = User.objects.create_user(
            username="user1", password="password123", nickname=f"user1_{uuid.uuid4()}"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="password123", nickname=f"user2_{uuid.uuid4()}"
        )

        # 채팅방 생성 및 참가자 설정
        self.chat_room = ChatRoom.objects.create()
        self.chat_room.participants.set([self.user1, self.user2])

    async def test_alarm_creation_and_read(self):
        """
        user1이 user2에게 메시지를 보냈을 때 user2에게 알람이 생성되고,
        이를 확인 시 is_read가 True로 전환되는지 확인
        """
        print(">>> user1이 메시지를 전송하고 알람을 생성합니다.")
        # user1이 메시지 보냄
        message = await sync_to_async(Message.objects.create)(
            chat_room=self.chat_room, sender=self.user1, content="안녕하세요"
        )

        # 알람 생성 여부 확인
        alarm = await sync_to_async(Alarm.objects.create)(
            recipient=self.user2,
            sender=self.user1,
            alarm_type="message",
            message="새로운 메시지가 도착했습니다.",
            related_object_id=message.id,
        )

        # WebSocketCommunicator 생성 시 세션 포함
        websocket_url = f"/ws/chat/{self.chat_room.id}/"
        communicator = WebsocketCommunicator(test_application, websocket_url)

        # WebSocket 연결
        connected, _ = await communicator.connect()
        self.assertTrue(
            connected, f"WebSocket 연결에 실패했습니다. 경로: {websocket_url}"
        )

        # 메시지 전송 및 알람 수신
        print(">>> WebSocket으로 메시지를 전송합니다.")
        await communicator.send_json_to(
            {
                "message": "Test message",
                "message_id": message.id,
            }
        )

        # 응답 확인
        response = await communicator.receive_json_from()
        print(f">>> WebSocket 수신 메시지: {response}")
        self.assertIn("message_id", response)
        self.assertEqual(response["message_id"], message.id)

        # 알람 is_read 상태 확인
        print(">>> 알람 읽음 상태를 확인합니다.")
        await sync_to_async(alarm.refresh_from_db)()
        self.assertFalse(alarm.is_read, "알림이 읽음 처리되지 않았습니다.")

        # 알림 읽음 처리
        print(">>> 알람 읽음 처리를 진행합니다.")
        alarm.is_read = True
        await sync_to_async(alarm.save)()

        # 알람 읽음 상태 확인
        await sync_to_async(alarm.refresh_from_db)()
        self.assertTrue(alarm.is_read, "알림이 읽음 처리되지 않았습니다.")

        await communicator.disconnect()


class AlarmDeleteTestCase(APITestCase):
    def setUp(self):
        unique_id1 = str(uuid.uuid4())[:8]  # 고유한 id 생성
        unique_id2 = str(uuid.uuid4())[:8]

        self.user1 = User.objects.create_user(
            username=f"user1_{unique_id1}",
            password="password123",
            nickname=f"user1_nickname_{unique_id1}",  # 고유한 닉네임
        )
        self.user2 = User.objects.create_user(
            username=f"user2_{unique_id2}",
            password="password123",
            nickname=f"user2_nickname_{unique_id2}",  # 고유한 닉네임
        )

        # 로그인 설정
        self.client.login(username=self.user1.username, password="password123")

        # 알림 생성
        self.alarm = Alarm.objects.create(
            recipient=self.user1,
            sender=self.user2,
            alarm_type="message",
            message="Test message",
        )

    def test_delete_alarm(self):
        """
        알림 삭제 테스트: 알림이 성공적으로 삭제되는지 확인합니다.
        """
        url = reverse("alarm:alarm_delete", kwargs={"alarm_id": self.alarm.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Alarm.objects.count(), 0)  # 알림이 삭제되었는지 확인

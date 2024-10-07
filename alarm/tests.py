import json
from django.urls import reverse, re_path
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from alarm.models import Alarm
from chat.models import ChatRoom, Message, WebSocketConnection
from accounts.models import Follow
from insta.models import Post, Comment, Like
from .consumers import AlarmConsumer

User = get_user_model()


class MockAlarmConsumer(AlarmConsumer):
    """
    WebSocket 연결을 테스트하기 위한 MockAlarmConsumer.
    알림 수신 시 WebSocket이 올바르게 작동하는지 확인합니다.
    """

    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        alarm = data.get("alarm")

        # 알림 메시지 수신 후 전송
        await self.send(text_data=json.dumps({"alarm": alarm, "status": "received"}))

    async def disconnect(self, close_code):
        pass


# WebSocket 라우팅 설정
test_application = AuthMiddlewareStack(
    URLRouter(
        [
            re_path(r"ws/alarm/$", MockAlarmConsumer.as_asgi()),
        ]
    )
)


class AlarmTestCase(TransactionTestCase):
    """
    Alarm 앱 테스트 케이스
    """

    def setUp(self):
        """
        테스트용 사용자 및 게시글 생성
        """
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="newuser1@example.com",
            password="newpassword123",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="newuser2@example.com",
            password="newpassword456",
        )

        self.client = APIClient()
        self.client.login(email=self.user1.email, password="newpassword123")

        # Post 객체 생성
        self.post = Post.objects.create(
            content="테스트용 게시글입니다.", user=self.user1
        )

        # 채팅방 생성 및 참가자 설정
        self.chat_room = ChatRoom.objects.create()
        self.chat_room.participants.set([self.user1, self.user2])

    async def test_like_alarm_creation(self):
        """
        내 게시글에 좋아요가 달렸을 때 알림 생성 및 WebSocket 전송 테스트
        """
        print(">>> 좋아요 알림 생성 및 WebSocket 전송 테스트 시작")

        # 좋아요 생성
        await sync_to_async(Like.objects.create)(post=self.post, user=self.user2)

        # 알림 생성 확인
        alarm = await sync_to_async(
            Alarm.objects.filter(recipient=self.user1, alarm_type="like").first
        )()
        self.assertIsNotNone(alarm, "알림이 생성되지 않았습니다.")

        # WebSocket 전송 확인
        websocket_url = f"/ws/alarm/"
        communicator = WebsocketCommunicator(test_application, websocket_url)

        connected, _ = await communicator.connect()
        self.assertTrue(
            connected, f"WebSocket 연결에 실패했습니다. 경로: {websocket_url}"
        )

        # WebSocket 메시지 전송 및 알람 수신 확인
        await communicator.send_json_to({"alarm": alarm.message})
        response = await communicator.receive_json_from()
        print(f"WebSocket 수신 알림: {response}")

        self.assertIn("alarm", response, "알림 메시지가 수신되지 않았습니다.")
        self.assertEqual(response["alarm"], alarm.message)

        await communicator.disconnect()

    async def test_comment_alarm_creation(self):
        """
        내 게시글에 댓글이 달렸을 때 알림 생성 및 WebSocket 전송 테스트
        """
        print(">>> 댓글 알림 생성 및 WebSocket 전송 테스트 시작")

        # 댓글 생성
        await sync_to_async(Comment.objects.create)(
            post=self.post, user=self.user2, content="테스트용 댓글"
        )

        # 알림 생성 확인
        alarm = await sync_to_async(
            Alarm.objects.filter(recipient=self.user1, alarm_type="comment").first
        )()
        self.assertIsNotNone(alarm, "댓글 알림이 생성되지 않았습니다.")

        # WebSocket 전송 확인
        websocket_url = f"/ws/alarm/"
        communicator = WebsocketCommunicator(test_application, websocket_url)

        connected, _ = await communicator.connect()
        self.assertTrue(
            connected, f"WebSocket 연결에 실패했습니다. 경로: {websocket_url}"
        )

        # WebSocket 메시지 전송 및 알람 수신 확인
        await communicator.send_json_to({"alarm": alarm.message})
        response = await communicator.receive_json_from()
        print(f"WebSocket 수신 알림: {response}")

        self.assertIn("alarm", response, "댓글 알림 메시지가 수신되지 않았습니다.")
        self.assertEqual(response["alarm"], alarm.message)

        await communicator.disconnect()

    async def test_follow_alarm_creation(self):
        """
        다른 사용자가 나를 팔로우할 때 알림 생성 및 WebSocket 전송 테스트
        """
        print(">>> 팔로우 알림 생성 및 WebSocket 전송 테스트 시작")

        # 팔로우 생성
        await sync_to_async(Follow.objects.create)(
            follower=self.user2, following=self.user1
        )

        # 알림 생성 확인
        alarm = await sync_to_async(
            Alarm.objects.filter(recipient=self.user1, alarm_type="follow").first
        )()
        self.assertIsNotNone(alarm, "팔로우 알림이 생성되지 않았습니다.")

        # WebSocket 전송 확인
        websocket_url = f"/ws/alarm/"
        communicator = WebsocketCommunicator(test_application, websocket_url)

        connected, _ = await communicator.connect()
        self.assertTrue(
            connected, f"WebSocket 연결에 실패했습니다. 경로: {websocket_url}"
        )

        # WebSocket 메시지 전송 및 알람 수신 확인
        await communicator.send_json_to({"alarm": alarm.message})
        response = await communicator.receive_json_from()
        print(f"WebSocket 수신 알림: {response}")

        self.assertIn("alarm", response, "팔로우 알림 메시지가 수신되지 않았습니다.")
        self.assertEqual(response["alarm"], alarm.message)

        await communicator.disconnect()

    async def test_message_alarm_creation(self):
        """
        다른 사용자가 나에게 메시지를 보냈을 때 알림 생성 및 WebSocket 전송 테스트
        """
        print(">>> 메시지 전송 및 알림 생성 테스트 시작")

        # user2가 메시지를 보냄
        await sync_to_async(Message.objects.create)(
            chat_room=self.chat_room, sender=self.user2, content="Hello!"
        )

        # 알림 생성 확인
        alarm = await sync_to_async(
            Alarm.objects.filter(recipient=self.user1, alarm_type="message").first
        )()
        self.assertIsNotNone(alarm, "메시지 알림이 생성되지 않았습니다.")

        # WebSocket 전송 확인
        websocket_url = f"/ws/alarm/"
        communicator = WebsocketCommunicator(test_application, websocket_url)

        connected, _ = await communicator.connect()
        self.assertTrue(
            connected, f"WebSocket 연결에 실패했습니다. 경로: {websocket_url}"
        )

        # WebSocket 메시지 전송 및 알람 수신 확인
        await communicator.send_json_to({"alarm": alarm.message})
        response = await communicator.receive_json_from()
        print(f"WebSocket 수신 알림: {response}")

        self.assertIn("alarm", response, "메시지 알림 메시지가 수신되지 않았습니다.")
        self.assertEqual(response["alarm"], alarm.message)

        await communicator.disconnect()

    async def test_message_alarm_based_on_websocket_disconnect(self):
        """
        WebSocket 연결 종료 시간을 기준으로 메시지 알림이 생성되는지 테스트
        """
        print(">>> WebSocket 연결 종료 시간에 따른 알림 생성 테스트 시작")

        # user1이 WebSocket 연결한 후 즉시 연결 종료
        ws_connection = await sync_to_async(WebSocketConnection.objects.create)(
            user=self.user1, chat_room=self.chat_room
        )
        await sync_to_async(ws_connection.mark_disconnected)()

        # user2가 메시지 전송
        await sync_to_async(Message.objects.create)(
            chat_room=self.chat_room, sender=self.user2, content="안녕하세요"
        )

        # 연결 종료 시간 이후에 메시지가 전송되었기 때문에 알림이 생성되어야 함
        alarm = await sync_to_async(
            Alarm.objects.filter(recipient=self.user1, alarm_type="message").first
        )()
        self.assertIsNotNone(alarm, "메시지 알림이 생성되지 않았습니다.")

        # WebSocket 전송 확인
        websocket_url = f"/ws/alarm/"
        communicator = WebsocketCommunicator(test_application, websocket_url)

        connected, _ = await communicator.connect()
        self.assertTrue(
            connected, f"WebSocket 연결에 실패했습니다. 경로: {websocket_url}"
        )

        # WebSocket 메시지 전송 및 알람 수신 확인
        await communicator.send_json_to({"alarm": alarm.message})
        response = await communicator.receive_json_from()
        print(f"WebSocket 수신 알림: {response}")

        self.assertIn("alarm", response, "메시지 알림 메시지가 수신되지 않았습니다.")
        self.assertEqual(response["alarm"], alarm.message)

        await communicator.disconnect()

    async def test_message_no_alarm_if_user_connected(self):
        """
        WebSocket 연결이 유지된 경우 알림이 생성되지 않는지 테스트
        """
        print(">>> WebSocket 연결 유지 시 알림 미생성 테스트 시작")

        # user1이 WebSocket 연결을 유지 중
        await sync_to_async(WebSocketConnection.objects.create)(
            user=self.user1, chat_room=self.chat_room, disconnected_at=None
        )

        # WebSocketConnection이 제대로 생성되었는지 확인
        websocket_connection = await sync_to_async(
            WebSocketConnection.objects.filter(
                user=self.user1, chat_room=self.chat_room, disconnected_at=None
            ).exists
        )()
        self.assertTrue(
            websocket_connection, "WebSocket 연결이 정상적으로 생성되지 않았습니다."
        )

        # user2가 메시지 전송
        await sync_to_async(Message.objects.create)(
            chat_room=self.chat_room, sender=self.user2, content="안녕하세요"
        )

        # user1이 여전히 WebSocket에 연결되어 있으므로 알림이 생성되지 않아야 함
        alarm_exists = await sync_to_async(
            Alarm.objects.filter(recipient=self.user1, alarm_type="message").exists
        )()
        self.assertFalse(alarm_exists, "WebSocket 연결 중에도 알림이 생성되었습니다.")

    def test_delete_alarm(self):
        """
        알림 삭제 테스트: 알림이 성공적으로 삭제되는지 확인합니다.
        """
        print(">>> 개별 알림 삭제 테스트 시작")

        # 알림 생성
        alarm = Alarm.objects.create(
            recipient=self.user1,
            sender=self.user2,
            alarm_type="message",
            message="Test message",
        )

        # 삭제 요청
        url = reverse("alarm:alarm_delete", kwargs={"alarm_id": alarm.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Alarm.objects.count(), 0, "알림이 삭제되지 않았습니다.")

    def test_bulk_delete_alarms(self):
        """
        알림 일괄 삭제 테스트: 모든 알림이 성공적으로 삭제되는지 확인합니다.
        """
        print(">>> 알림 일괄 삭제 테스트 시작")

        # 알림 여러 개 생성
        Alarm.objects.create(
            recipient=self.user1,
            sender=self.user2,
            alarm_type="message",
            message="Test message 1",
        )
        Alarm.objects.create(
            recipient=self.user1,
            sender=self.user2,
            alarm_type="follow",
            message="Test message 2",
        )

        # 삭제 요청
        url = reverse("alarm:alarm_bulk_delete")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Alarm.objects.count(), 0, "알림이 일괄 삭제되지 않았습니다.")

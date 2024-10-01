from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import ChatRoom

User = get_user_model()


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
        # 채팅방 생성 테스트
        url = reverse("chat:room_create")
        data = {"participants": ["user2"]}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChatRoom.objects.count(), 1)
        self.assertIn("user1, user2의 대화", response.data["name"])

    def test_duplicate_chatroom_creation(self):
        # 중복 채팅방 생성 방지 테스트
        url = reverse("chat:room_create")
        data = {"participants": ["user2"]}

        # 첫 번째 방 생성
        self.client.post(url, data, format="json")

        # 같은 참가자로 또 생성 시도
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 리스트의 첫 번째 요소로 에러 메시지 확인
        self.assertEqual(response.data[0], "이미 이 사용자와의 채팅방이 존재합니다.")

    def test_invalid_participants(self):
        # 참가자가 두 명 이상일 때 에러 처리
        url = reverse("chat:room_create")
        data = {"participants": ["user2", "user3"]}  # 세 명 이상일 때

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "자신과의 채팅은 할 수 없습니다.")

    def test_chatroom_leave(self):
        # 채팅방 나가기 테스트
        chatroom = ChatRoom.objects.create()
        chatroom.participants.set([self.user1, self.user2])

        url = reverse("chat:room_leave", kwargs={"room_id": chatroom.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(self.user1, chatroom.participants.all())

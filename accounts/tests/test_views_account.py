from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()


class AccountViewsTest(APITestCase):
    def setUp(self):
        # 테스트를 위한 사용자 생성
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            nickname="TestUser",
        )

        # 테스트 클라이언트 로그인
        self.client.login(username="testuser", password="testpassword123")

    def test_signup_view(self):
        # 회원가입 뷰 테스트
        url = reverse("accounts:signup")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "nickname": "NewUser",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_login_view(self):
        # 로그인 뷰 테스트
        url = reverse("accounts:login")
        data = {"username": "testuser", "password": "testpassword123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_logout_view(self):
        # 로그아웃 뷰 테스트
        url = reverse("accounts:logout")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_change_view(self):
        # 비밀번호 변경 뷰 테스트
        url = reverse("accounts:change_password")
        data = {"old_password": "testpassword123", "new_password": "newtestpassword123"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_deactivate_view(self):
        # 계정 비활성화 뷰 테스트
        url = reverse("accounts:user_deactivate")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.get(username="testuser").is_active)

    def test_request_reactivation_view(self):
        # 계정 재활성화 요청 뷰 테스트
        self.user.is_active = False
        self.user.save()
        url = reverse("accounts:request_reactivation")
        data = {"email": "test@example.com"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)  # 이메일이 전송되었는지 확인

    def test_activate_account_view(self):
        # 계정 활성화 뷰 테스트
        self.user.is_active = False
        self.user.save()
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse(
            "accounts:activate_account", kwargs={"uidb64": uid, "token": token}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_user_delete_view(self):
        # 계정 삭제 뷰 테스트
        url = reverse("accounts:user_delete")
        data = {"confirmation": "DELETE"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(username="testuser").exists())

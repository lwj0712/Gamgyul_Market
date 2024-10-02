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

    def test_signup_view_duplicate_username(self):
        # 중복되는 username 회원가입 시 에러
        url = reverse("accounts:signup")
        data = {
            "username": "testuser",  # 이미 존재하는 사용자 이름
            "email": "newuser@example.com",
            "password": "newpassword123",
            "nickname": "NewUser",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_view(self):
        # 로그인 뷰 테스트
        url = reverse("accounts:login")
        data = {"username": "testuser", "password": "testpassword123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_login_view_invalid_credentials(self):
        # 잘못된 패스워드 입력 시 에러 테스트
        url = reverse("accounts:login")
        data = {"username": "testuser", "password": "wrongpassword"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_view_inactive_account(self):
        # 비활성화된 계정 로그인 시 에러 테스트
        self.user.is_active = False
        self.user.save()
        url = reverse("accounts:login")
        data = {"username": "testuser", "password": "testpassword123"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertEqual(
            response.data["detail"],
            "계정이 비활성화되어 있습니다. 재활성화하시겠습니까?",
        )
        self.assertTrue(response.data.get("inactive_account"))
        self.assertEqual(response.data.get("email"), "test@example.com")

    def test_logout_view(self):
        # 로그아웃 뷰 테스트
        url = reverse("accounts:logout")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_view_unauthenticated(self):
        # 인증되지 않은 유저 로그아웃 시 에러 테스트
        self.client.logout()
        url = reverse("accounts:logout")
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful_password_change(self):
        # 패스워드 변경 테스트
        data = {"old_password": "testpassword123", "new_password": "newpassword123"}
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "패스워드가 올바르게 변경되었습니다. 다시 로그인해주세요.",
        )

        # 새 비밀번호로 로그인이 가능한지 확인
        self.client.logout()
        self.assertTrue(
            self.client.login(username="testuser", password="newpassword123")
        )

    def test_wrong_old_password(self):
        # 이전 비밀번호가 다를 경우 테스트
        data = {"old_password": "wrongpassword", "new_password": "newpassword456"}
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "이전 비밀번호가 올바르지 않습니다.", str(response.data["old_password"])
        )

    def test_new_password_same_as_old(self):
        # 새 비밀번호가 이전 비밀번호와 같은 경우 테스트
        data = {"old_password": "testpassword123", "new_password": "testpassword123"}
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "새 비밀번호는 이전 비밀번호와 달라야 합니다.",
            str(response.data["non_field_errors"]),
        )

    def test_new_password_too_short(self):
        # 장고 기초 비밀번호 유효성 검사 테스트
        data = {"old_password": "testpassword123", "new_password": "short"}
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("이 비밀번호는 너무 짧습니다", str(response.data["new_password"]))

    def test_unauthenticated_user(self):
        # 인증되지 않은 사용자 패스워드 변경 시 에러 테스트
        self.client.logout()
        data = {"old_password": "testpassword123", "new_password": "newpassword123"}
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_fields(self):
        # 필수 필드 누락 시 에러 테스트
        data = {"old_password": "testpassword123"}  # new_password 누락
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

        data = {"new_password": "newpassword123"}  # old_password 누락
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("old_password", response.data)

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

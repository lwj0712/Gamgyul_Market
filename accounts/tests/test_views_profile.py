from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import Follow, PrivacySettings

User = get_user_model()


class BaseProfileTestCase(APITestCase):
    """
    기본 세팅 유저
    """

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="testuser1@example.com",
            password="testpassword123",
            nickname="TestUser1",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="testuser2@example.com",
            password="testpassword123",
            nickname="TestUser2",
        )
        self.client.force_authenticate(user=self.user1)


class ProfileDetailViewTestCase(BaseProfileTestCase):
    """
    프로필 조회 및 존재하지 않는 프로필 요청 테스트
    """

    def test_profile_detail_view(self):
        # 프로필 조회 테스트
        url = reverse(
            "accounts:profile_detail", kwargs={"username": self.user2.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user2.username)

    def test_profile_detail_view_not_found(self):
        # 존재하지 않는 프로필 요청 테스트
        url = reverse("accounts:profile_detail", kwargs={"username": "nonexistent"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProfileUpdateViewTestCase(BaseProfileTestCase):
    """
    프로필 수정 테스트
    전체 업데이트 및 부분 업데이트 테스트
    """

    def test_profile_update_view(self):
        # 전체 업데이트(put request) 테스트
        url = reverse("accounts:profile_update")
        data = {"nickname": "UpdatedNickname", "bio": "Updated bio"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nickname"], "UpdatedNickname")

    def test_profile_partial_update_view(self):
        # 부분 업데이트(patch request) 테스트
        url = reverse("accounts:profile_update")
        data = {"bio": "Partially updated bio"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["bio"], "Partially updated bio")


class PrivacySettingsViewTestCase(BaseProfileTestCase):
    """
    프로필 정보 보호 설정 조회 및 수정 테스트
    """

    def test_privacy_settings_get(self):
        # 프로필 보호 설정 조회 테스트
        url = reverse("accounts:privacy_settings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_privacy_settings_update(self):
        # 프로필 보호 설정 수정 테스트
        url = reverse("accounts:privacy_settings")
        data = {
            "follower_can_see_email": True,
            "others_can_see_posts": False,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["follower_can_see_email"], True)
        self.assertEqual(response.data["others_can_see_posts"], False)


class FollowViewTestCase(BaseProfileTestCase):
    """
    팔로우 기능 테스트
    """

    def test_follow_user(self):
        # 팔로우 테스트
        url = reverse("accounts:follow", kwargs={"pk": self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_follow_self(self):
        # 자기 자신을 팔로우하려는 경우 에러
        url = reverse("accounts:follow", kwargs={"pk": self.user1.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "자기 자신을 팔로우할 수 없습니다.")

    def test_follow_nonexistent_user(self):
        # 존재하지 않는 사용자를 팔로우하려는 경우 에러
        url = reverse("accounts:follow", kwargs={"pk": 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_follow_already_following(self):
        # 이미 팔로우한 사용자를 팔로우하려는 경우 에러
        Follow.objects.create(follower=self.user1, following=self.user2)
        url = reverse("accounts:follow", kwargs={"pk": self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "이미 팔로우한 사용자입니다.")


class UnfollowViewTestCase(BaseProfileTestCase):
    """
    언팔로우 기능 테스트
    """

    def setUp(self):
        # 팔로우 세팅
        super().setUp()
        Follow.objects.create(follower=self.user1, following=self.user2)

    def test_unfollow_user(self):
        # 언팔로우 테스트
        url = reverse("accounts:unfollow", kwargs={"pk": self.user2.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unfollow_not_following(self):
        # 언팔로우할 사용자가 팔로우하지 않은 경우 에러
        Follow.objects.filter(follower=self.user1, following=self.user2).delete()
        url = reverse("accounts:unfollow", kwargs={"pk": self.user2.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "현재 유저를 팔로우하고 있지 않습니다."
        )

    def test_unfollow_nonexistent_user(self):
        # 존재하지 않는 사용자를 언팔로우하려는 경우 에러
        url = reverse("accounts:unfollow", kwargs={"pk": 9999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProfileSearchViewTestCase(BaseProfileTestCase):
    """
    프로필 검색 기능 테스트
    """

    def test_profile_search(self):
        # 프로필 검색 테스트
        url = reverse("accounts:profile_search")
        response = self.client.get(url, {"q": "testuser"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 두 명의 사용자가 검색되어야 함

    def test_profile_search_no_query(self):
        # 쿼리가 없는 경우 빈 결과 반환 테스트
        url = reverse("accounts:profile_search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # 쿼리가 없으면 빈 결과를 반환해야 함

    def test_profile_search_no_results(self):
        # 쿼리에 일치하는 사용자가 없는 경우 빈 결과 반환 테스트
        url = reverse("accounts:profile_search")
        response = self.client.get(url, {"q": "nonexistent"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # 결과가 없어야 함

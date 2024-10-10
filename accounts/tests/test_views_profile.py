from django.urls import reverse
from rest_framework.test import APITransactionTestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import Follow, PrivacySettings

User = get_user_model()


class ProfileDetailViewTestCase(APITransactionTestCase):
    """
    프로필 조회 및 존재하지 않는 프로필 요청 테스트
    """

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="testuser1@example.com",
            password="testpassword123",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="testuser2@example.com",
            password="testpassword123",
        )
        self.client.force_authenticate(user=self.user1)

    def test_profile_detail_view(self):
        """프로필 조회 테스트"""
        url = reverse(
            "accounts:profile_detail", kwargs={"username": self.user2.username}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user2.username)

    def test_profile_detail_view_not_found(self):
        """존재하지 않는 프로필 요청 테스트"""
        url = reverse("accounts:profile_detail", kwargs={"username": "nonexistent"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProfileUpdateViewTestCase(APITransactionTestCase):
    """
    프로필 수정 테스트
    전체 업데이트 및 부분 업데이트 테스트
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword123",
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_update_view(self):
        """전체 업데이트(put request) 테스트"""
        url = reverse("accounts:profile_update")
        data = {"username": "UpdatedUsername", "bio": "Updated bio"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "UpdatedUsername")

    def test_profile_partial_update_view(self):
        """부분 업데이트(patch request) 테스트"""
        url = reverse("accounts:profile_update")
        data = {"bio": "Partially updated bio"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["bio"], "Partially updated bio")


class PrivacySettingsViewTestCase(APITransactionTestCase):
    """
    프로필 정보 보호 설정 조회 및 수정 테스트
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpassword123",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse(
            "accounts:privacy_settings", kwargs={"username": self.user.username}
        )

    def test_privacy_settings_get(self):
        """프로필 보호 설정 조회 테스트"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("follower_can_see_email", response.data)

    def test_privacy_settings_update(self):
        """프로필 보호 설정 수정 테스트"""
        data = {
            "follower_can_see_email": True,
            "others_can_see_posts": False,
        }
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"], "프로필 보안 설정이 성공적으로 업데이트되었습니다."
        )
        self.assertTrue(response.data["data"]["follower_can_see_email"])
        self.assertFalse(response.data["data"]["others_can_see_posts"])

    def test_privacy_settings_partial_update(self):
        """프로필 보호 설정 부분 수정 테스트"""
        data = {
            "follower_can_see_email": True,
        }
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"], "프로필 보안 설정이 성공적으로 업데이트되었습니다."
        )
        self.assertTrue(response.data["data"]["follower_can_see_email"])

    def test_privacy_settings_invalid_update(self):
        """
        잘못된 데이터로 프로필 보호 설정 수정 테스트
        유효하지 않은 필드 이름, boolean이 아닌 값 검사
        """
        data = {
            "invalid_field": True,
            "follower_can_see_email": "invalid_value",
        }
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_privacy_settings_unauthenticated(self):
        """인증되지 않은 사용자 접근 테스트"""
        self.client.force_authenticate(user=None)
        url = reverse("accounts:privacy_settings", kwargs={"username": "testuser"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_privacy_settings_nonexistent_user(self):
        """존재하지 않는 사용자의 프로필 보호 설정 접근 테스트"""
        url = reverse("accounts:privacy_settings", kwargs={"username": "nonexistent"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_privacy_settings_nonexistent(self):
        """프로필 보호 설정이 없는 경우 테스트"""
        PrivacySettings.objects.filter(user=self.user).delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("follower_can_see_email", response.data)


class FollowViewTestCase(APITransactionTestCase):
    """
    팔로우 기능 테스트
    """

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="testuser1@example.com",
            password="testpassword123",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="testuser2@example.com",
            password="testpassword123",
        )
        self.user3 = User.objects.create_user(
            username="testuser3",
            email="testuser3@example.com",
            password="testpassword123",
        )
        self.client.force_authenticate(user=self.user1)

    def test_follow_user(self):
        """팔로우 테스트"""
        url = reverse("accounts:follow", kwargs={"pk": self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_follow_self(self):
        """자기 자신을 팔로우하려는 경우 에러"""
        url = reverse("accounts:follow", kwargs={"pk": self.user1.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "자기 자신을 팔로우할 수 없습니다.")

    def test_follow_nonexistent_user(self):
        """존재하지 않는 사용자를 팔로우하려는 경우 에러"""
        url = reverse("accounts:follow", kwargs={"pk": 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "팔로우하려는 사용자를 찾을 수 없습니다."
        )

    def test_follow_already_following(self):
        """이미 팔로우한 사용자를 팔로우하려는 경우 에러"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        url = reverse("accounts:follow", kwargs={"pk": self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "이미 팔로우한 사용자입니다.")

    def test_following_list(self):
        """팔로잉 목록 조회 테스트"""
        # user1이 user2와 user3을 팔로우
        Follow.objects.create(follower=self.user1, following=self.user2)
        Follow.objects.create(follower=self.user1, following=self.user3)

        url = reverse(
            "accounts:profile_detail", kwargs={"username": self.user1.username}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data)
        self.assertEqual(
            len(response.data["following"]), 2
        )  # user1은 2명의 유저를 팔로우
        usernames = [user["username"] for user in response.data["following"]]
        self.assertIn(self.user2.username, usernames)
        self.assertIn(self.user3.username, usernames)

    def test_followers_list(self):
        """팔로워 목록 조회 테스트"""
        # user2와 user3이 user1을 팔로우
        Follow.objects.create(follower=self.user2, following=self.user1)
        Follow.objects.create(follower=self.user3, following=self.user1)

        url = reverse(
            "accounts:profile_detail", kwargs={"username": self.user1.username}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data)
        self.assertEqual(
            len(response.data["followers"]), 2
        )  # user1은 2명의 팔로워가 있음
        usernames = [user["username"] for user in response.data["followers"]]
        self.assertIn(self.user2.username, usernames)
        self.assertIn(self.user3.username, usernames)


class UnfollowViewTestCase(APITransactionTestCase):
    """
    언팔로우 기능 테스트
    """

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="testuser1@example.com",
            password="testpassword123",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="testuser2@example.com",
            password="testpassword123",
        )
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.client.force_authenticate(user=self.user1)

    def test_unfollow_user(self):
        """언팔로우 테스트"""
        url = reverse("accounts:unfollow", kwargs={"pk": self.user2.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unfollow_not_following(self):
        """언팔로우할 사용자가 팔로우하지 않은 경우 에러"""
        Follow.objects.filter(follower=self.user1, following=self.user2).delete()
        url = reverse("accounts:unfollow", kwargs={"pk": self.user2.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "현재 유저를 팔로우하고 있지 않습니다."
        )

    def test_unfollow_nonexistent_user(self):
        """존재하지 않는 사용자를 언팔로우하려는 경우 에러"""
        url = reverse("accounts:unfollow", kwargs={"pk": 9999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "언팔로우할 유저가 존재하지 않습니다."
        )


class ProfileSearchViewTestCase(APITransactionTestCase):
    def setUp(self):
        User.objects.all().delete()
        self.user1 = User.objects.create_user(
            username="testuser1",
            password="12345",
            email="test1@example.com",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            password="12345",
            email="test2@example.com",
        )
        self.user3 = User.objects.create_user(
            username="otheruser",
            password="12345",
            email="other@example.com",
        )
        self.client.force_authenticate(user=self.user1)

    def test_profile_search(self):
        """
        프로필 검색 테스트
        한 명의 사용자가 검색되어야 함(본인 제외)
        """
        url = reverse("accounts:profile_search")
        response = self.client.get(url, {"q": "testuser"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"Response data: {response.data}")
        self.assertEqual(response.data["count"], 1)

    def test_profile_search_no_query(self):
        """쿼리가 없는 경우 빈 결과 반환 테스트"""
        url = reverse("accounts:profile_search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"Response data: {response.data}")
        self.assertEqual(response.data["count"], 0)

    def test_profile_search_no_results(self):
        """쿼리에 일치하는 사용자가 없는 경우 빈 결과 반환 테스트"""
        url = reverse("accounts:profile_search")
        response = self.client.get(url, {"q": "nonexistent"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"Response data: {response.data}")
        self.assertEqual(response.data["count"], 0)

    def tearDown(self):
        User.objects.all().delete()
        print(f"User count after tearDown: {User.objects.count()}")

import os
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from accounts.models import User, Follow
from .models import Post


class TestPostAPI(APITestCase):
    def setUp(self):
        """테스트를 위한 APIClient 인스턴스 생성"""
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_create_post(self):
        """게시글 생성 테스트"""
        url = reverse("insta:insta_post_create")
        image_file = self.get_image_file()  # 테스트용 이미지 생성

        data = {
            "content": "This is a test post.",
            "tags": ["testtag1", "testtag2"],
            "images": [image_file],  # 생성한 이미지 데이터 추가
        }
        response = self.client.post(url, data, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED
        assert Post.objects.count() == 1

        # 테스트용 이미지 삭제
        image_file.close()
        os.remove(image_file.name)

    def test_post_list_authenticated_user_with_followings(self):
        """팔로우한 사용자가 있는 인증된 사용자의 게시글 목록 조회 테스트"""
        followed_user = User.objects.create_user(
            username="followed_user", password="password2"
        )
        Follow.objects.create(follower=self.user, following=followed_user)
        post = Post.objects.create(
            content="This is a post by followed user.", user=followed_user
        )

        # 인증된 사용자로 요청
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("insta:post_list"))

        # 응답 코드 및 게시글이 포함되어 있는지 확인
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["id"] == post.id

    def test_post_list_authenticated_user_without_followings(self):
        """팔로우한 사용자가 없는 인증된 사용자의 게시글 목록 조회 테스트"""
        popular_user = User.objects.create_user(username="popularuser", password="pass")
        popular_user.followers_count = 100  # 인기 사용자를 위한 필드 설정
        popular_user.save()
        post = Post.objects.create(user=popular_user, content="Post from popular user")

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("insta:post_list"))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["id"] == post.id

    def test_post_list_unauthenticated_user(self):
        """인증되지 않은 사용자의 게시글 목록 조회 테스트"""
        popular_user = User.objects.create_user(username="popularuser", password="pass")
        popular_user.followers_count = 100  # 인기 사용자를 위한 필드 설정
        popular_user.save()
        post = Post.objects.create(user=popular_user, content="Post from popular user")

        response = self.client.get(reverse("insta:post_list"))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        assert response.data[0]["id"] == post.id

    def test_unauthenticated_user_post_view(self):
        """인증되지 않은 사용자의 게시글 상세 조회 테스트"""
        post = Post.objects.create(user=self.user, content="Test post")
        self.client.force_authenticate(user=None)  # 인증되지 않은 사용자로 설정

        response = self.client.get(reverse("insta:post_detail", args=[post.id]))
        assert response.status_code == status.HTTP_200_OK

    def test_create_post_without_image(self):
        """이미지 없이 게시글 생성 시 에러 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("insta:post_create"),
            {
                "content": "Test post",
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_post_with_excess_images(self):
        """10개를 초과한 이미지를 포함한 게시글 생성 시 에러 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("insta:post_create"),
            {
                "content": "Test post",
                "images": [
                    self.get_image_file() for _ in range(12)
                ],  # 12개 이미지 생성
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCommentAPI(TestPostAPI):
    def setUp(self):
        super().setUP()

    def test_create_comment(self):
        """댓글 생성 테스트"""
        url = reverse("insta:insta_comment_list_create", args=[self.post.id])
        data = {
            "content": "This is a comment.",
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED


class TestLikeAPI(TestPostAPI):
    def test_like_post(self):
        """게시글 좋아요 테스트"""
        url = reverse("insta:insta_like", args=[self.post.id])
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert self.post.likes.count() == 1

    def test_unlike_post(self):
        """게시글 좋아요 취소 테스트"""
        self.post.likes.add(self.user)
        url = reverse("insta:insta_like", args=[self.post.id])
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert self.post.likes.count() == 0


class TestTagAPI(TestPostAPI):
    def test_search_by_tag(self):
        """태그로 게시글 검색 테스트"""
        self.post.tags.add("testtag1")  # 태그 추가
        url = reverse("insta:post_list") + "?tags=testtag1"
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == self.post.id

    def test_search_by_nonexistent_tag(self):
        """존재하지 않는 태그로 게시글 검색 시 결과가 없는지 테스트"""
        url = reverse("insta:post_list") + "?tags=nonexistenttag"
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

import os
import uuid
import tempfile
from PIL import Image
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from accounts.models import Follow
from .models import Post, Like


User = get_user_model()


class TestPostAPI(APITestCase):
    def setUp(self):
        """테스트를 위한 APIClient 인스턴스 생성"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4()}",
            password="testpass",
            email="testuser@example.com",
        )

        # 인기 사용자 생성
        self.popular_user_1 = User.objects.create_user(
            username=f"popular_user_1_{uuid.uuid4()}",
            password="testpass",
            email="popular_user_1@example.com",
        )

        self.popular_user_2 = User.objects.create_user(
            username=f"popular_user_2_{uuid.uuid4()}",
            password="testpass",
            email="popular_user_2@example.com",
        )

        # 팔로우한 사용자 생성
        self.followed_user = User.objects.create_user(  # 여기서 정의
            username=f"followed_user_{uuid.uuid4()}",
            password="testpass",
            email="followed_user@example.com",
        )
        Follow.objects.create(follower=self.user, following=self.followed_user)

        # 인기 사용자의 팔로워 생성
        Follow.objects.create(follower=self.user, following=self.popular_user_1)
        Follow.objects.create(follower=self.user, following=self.popular_user_2)

        # 인기 사용자 게시글 생성
        Post.objects.create(content="Popular post 1", user=self.popular_user_1)
        Post.objects.create(content="Popular post 2", user=self.popular_user_2)

        # 생성된 게시물 ID 확인
        popular_posts = Post.objects.filter(
            user__in=[self.popular_user_1, self.popular_user_2]
        )

        # 팔로우한 사용자의 게시글 생성
        self.followed_post = Post.objects.create(
            content="Followed post", user=self.user
        )

    def get_image_file(self):
        """테스트용 이미지 파일 생성"""
        image = Image.new("RGB", (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        image.save(tmp_file)
        tmp_file.seek(0)
        return tmp_file

    def test_create_post(self):
        """게시글 생성 테스트"""
        self.client.force_authenticate(user=self.user)
        Post.objects.all().delete()

        url = reverse("insta:insta_post_create")
        image_file = self.get_image_file()  # 테스트용 이미지 생성

        data = {
            "content": "This is a test post.",
            "tags": ["testtag1", "testtag2"],
            "images": [image_file],  # 생성한 이미지 데이터 추가
        }
        response = self.client.post(url, data, format="multipart")

        # 응답 상태 코드 확인
        assert response.status_code == status.HTTP_201_CREATED

        # 게시글 수 확인
        assert (
            Post.objects.count() == 1
        ), f"Expected 1 post, but got {Post.objects.count()}"

        # 응답 데이터 확인
        post_data = response.data
        assert post_data["content"] == data["content"]
        assert set(post_data["tags"]) == set(data["tags"])

        # 테스트용 이미지 삭제
        image_file.close()
        os.remove(image_file.name)

    def test_post_list_authenticated_user_with_followings(self):
        """팔로우한 사용자가 있는 인증된 사용자의 게시글 목록 조회 테스트"""
        followed_user = User.objects.create_user(
            username="followed_user",
            email="followed_user_{}.example.com".format(uuid.uuid4()),
            password="testpass",
        )

        Follow.objects.create(follower=self.user, following=followed_user)

        post = Post.objects.create(
            content="This is a post by followed user.", user=followed_user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("insta:insta_post_list"))

        # 응답 코드 및 게시글이 포함되어 있는지 확인
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) > 0  # results 키의 길이를 확인
        assert any(
            item["id"] == post.id for item in response.data["results"]
        )  # results에서 게시물 ID 확인

    def test_post_list_authenticated_user_without_followings(self):
        """팔로우한 사용자가 없는 인증된 사용자의 게시글 목록 조회 테스트"""
        # 인증된 사용자는 있지만 팔로우한 사용자는 없는 상태
        self.client.force_authenticate(user=self.user)

        popular_posts_count = Post.objects.filter(
            user__in=[self.popular_user_1, self.popular_user_2]
        ).count()
        assert (
            popular_posts_count > 0
        ), "인기 게시물이 데이터베이스에 존재하지 않습니다."

        # 게시글 목록 조회 요청
        response = self.client.get(reverse("insta:insta_post_list"))

        # 응답 코드 확인
        assert response.status_code == status.HTTP_200_OK

        # 결과가 비어 있지 않은지 확인
        assert len(response.data["results"]) > 0, "결과가 비어 있습니다."

        # 인기 사용자 게시물이 포함되어 있는지 확인
        popular_post_ids = Post.objects.filter(
            user__in=[self.popular_user_1, self.popular_user_2]
        ).values_list("id", flat=True)
        response_post_ids = [item["id"] for item in response.data["results"]]

        # 비교 로직을 수정하여 더 명확하게 실패 원인 파악
        assert any(
            post_id in response_post_ids for post_id in popular_post_ids
        ), f"인기 사용자의 게시물이 응답에 포함되지 않았습니다. 응답 게시물 ID: {response_post_ids}, 인기 게시물 ID: {popular_post_ids}"

    def test_post_list_unauthenticated_user(self):
        """인증되지 않은 사용자의 게시글 목록 조회 테스트"""
        popular_user = User.objects.create_user(
            username="popularuser", password="pass", email="popularuser@example.com"
        )

        post = Post.objects.create(user=popular_user, content="Post from popular user")

        response = self.client.get(reverse("insta:insta_post_list"))

        # 응답 코드가 200인지 확인 (게시글 목록이 반환되는지 여부 확인)
        assert response.status_code == status.HTTP_200_OK

        # 'results'에 데이터가 있는지 확인
        assert len(response.data["results"]) > 0

        # 게시글의 첫 번째 항목이 예상한 post인지 확인
        assert response.data["results"][0]["id"] == post.id

    def test_create_post_with_excess_images(self):
        """10개를 초과한 이미지를 포함한 게시글 생성 시 에러 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("insta:insta_post_create"),
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
        """테스트를 위한 APIClient 인스턴스 생성"""
        super().setUp()  # 부모 클래스의 setUp 메서드를 호출하여 사용자 및 게시물 생성

        # 댓글을 달 게시물 생성
        self.comment_post = Post.objects.create(content="Test post", user=self.user)

        # 인기 사용자로부터 게시글 생성
        self.popular_post_1 = Post.objects.create(
            content="Popular post 1", user=self.popular_user_1
        )
        self.popular_post_2 = Post.objects.create(
            content="Popular post 2", user=self.popular_user_2
        )

        # 팔로우한 사용자의 게시글 생성
        self.followed_post = Post.objects.create(
            content="Followed post", user=self.followed_user
        )

    def test_create_comment(self):
        """댓글 생성 테스트"""
        url = reverse("insta:insta_comment_list_create", args=[self.comment_post.id])
        data = {
            "content": "This is a comment.",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data)

        # 응답 상태 코드 확인
        assert response.status_code == status.HTTP_201_CREATED

        # 응답 데이터 확인
        comment_data = response.data
        assert (
            comment_data["content"] == data["content"]
        ), f"Expected content '{data['content']}', but got '{comment_data['content']}'"

        # 댓글 수 확인
        assert (
            comment_data["post"] == self.comment_post.id
        ), f"Expected post ID {self.comment_post.id}, but got {comment_data['post']}"


class TestLikeAPI(TestPostAPI):
    def setUp(self):
        """테스트를 위한 APIClient 인스턴스 생성"""
        super().setUp()

        # 게시글 생성
        self.like_post = Post.objects.create(
            content="Test post", user=self.followed_user
        )

        # 인기 사용자로부터 게시글 생성
        self.popular_post_1 = Post.objects.create(
            content="Popular post 1", user=self.popular_user_1
        )
        self.popular_post_2 = Post.objects.create(
            content="Popular post 2", user=self.popular_user_2
        )

        # 팔로우한 사용자의 게시글 생성
        self.followed_post = Post.objects.create(
            content="Followed post", user=self.followed_user
        )

    def test_like_post(self):
        """게시글 좋아요 테스트"""
        self.client.force_authenticate(user=self.user)
        url = reverse("insta:insta_like", args=[self.like_post.id])
        response = self.client.post(url)
        assert (
            response.status_code == status.HTTP_201_CREATED
        ), f"Expected status code 201, but got {response.status_code}"
        self.like_post.refresh_from_db()
        assert (
            self.like_post.likes.count() == 1
        ), f"Expected 1 like, but got {self.like_post.likes.count()}"

    def test_unlike_post(self):
        """게시글 좋아요 취소 테스트"""
        # Like 인스턴스를 생성하여 게시글에 추가
        Like.objects.create(user=self.user, post=self.like_post)

        self.client.force_authenticate(user=self.user)
        url = reverse("insta:insta_like", args=[self.like_post.id])
        response = self.client.post(url)

        assert (
            response.status_code == status.HTTP_204_NO_CONTENT
        ), f"Expected status code 204, but got {response.status_code}"
        self.like_post.refresh_from_db()  # 게시글 데이터를 최신 상태로 갱신
        assert (
            self.like_post.likes.count() == 0
        ), f"Expected 0 likes, but got {self.like_post.likes.count()}"

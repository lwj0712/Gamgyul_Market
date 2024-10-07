from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, Comment, Like
from accounts.models import Follow, User
from .filters import PostFilter
from .serializers import (
    PostSerializer,
    CommentSerializer,
    LikeSerializer,
)


class PostPagination(LimitOffsetPagination):
    """게시물의 pagination 설정"""

    default_limit = 10
    max_limit = 50


class PostListView(generics.ListAPIView):
    """게시물 목록 조회 view"""

    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    pagination_class = PostPagination

    def get_queryset(self):
        """
        사용자가 팔로우한 사용자들의 게시물 또는
        인기 사용자의 게시물 반환
        """
        user = self.request.user

        if user.is_authenticated:
            following_users = Follow.objects.filter(follower=user).values_list(
                "followed_user", flat=True
            )

            if following_users.exists():
                return Post.objects.filter(user__in=following_users).order_by(
                    "-created_at"
                )

        """
        팔로우한 사용자가 없거나, 인증되지 않은 사용자일 경우
        팔로워가 많은 사용자의 게시물 반환
        """
        popular_users = User.objects.annotate(
            followers_count=Count("followers")
        ).order_by("-followers_count")[:10]
        return Post.objects.filter(user__in=popular_users).order_by("-created_at")

    def get(self, request, *args, **kwargs):
        posts = self.get_queryset()
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(posts, many=True)
        return Response({"posts": serializer.data})


class PostCreateView(generics.CreateAPIView):
    """게시물 작성 view"""

    queryset = Post.objects.all()
    serializer_class = PostSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """게시물 작성 처리"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """게시물 상세 조회, 수정, 삭제 view"""

    queryset = Post.objects.all()
    serializer_class = PostSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        """사용자 권한 설정"""
        if self.request.method in ["PUT", "PATCH"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_update(self, serializer):
        """게시물 작성자만 수정 가능"""
        instance = serializer.instance
        if instance.user != self.request.user:
            raise PermissionDenied("글 작성자만 수정할 수 있습니다.")
        serializer.save()


class PostDeleteView(generics.DestroyAPIView):
    """게시물 삭제 view"""

    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        """게시물 작성자만 삭제 가능"""
        if instance.user != self.request.user:
            raise PermissionDenied("글 작성자만 삭제할 수 있습니다.")
        instance.delete()


class CommentListCreateView(generics.ListCreateAPIView):
    """댓글 목록 조회, 작성 view"""

    serializer_class = CommentSerializer

    def get_permissions(self):
        """댓글 작성 시 인증된 사용자만 허용, 조회는 누구나 가능"""
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        """특정 게시물에 대한 댓글 목록 반환"""
        post_id = self.kwargs["post_id"]
        return Comment.objects.filter(post_id=post_id).order_by("-created_at")

    def perform_create(self, serializer):
        """새 댓글 작성 시 현재 사용자 정보 추가"""
        post_id = self.kwargs["post_id"]
        serializer.save(user=self.request.user, post_id=post_id)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """댓글 상세 조회, 수정, 삭제 view"""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_destroy(self, instance):
        """댓글 작성자만 삭제 가능"""
        if instance.user != self.request.user:
            raise PermissionDenied("댓글 작성자만 삭제할 수 있습니다.")
        instance.delete()


class LikeView(generics.GenericAPIView):
    """좋아요 추가, 취소 view"""

    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if created:
            return Response(status=status.HTTP_201_CREATED)
        like.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, post_id):
        """좋아요를 누른 사용자 목록 조회"""
        post = get_object_or_404(Post, id=post_id)
        likes = Like.objects.filter(post=post).select_related("user")
        serializer = self.get_serializer(likes, many=True)
        return Response(serializer.data)


class TagPostListView(generics.ListAPIView):
    """태그로 게시물 검색 view"""

    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = PostFilter

    def get_queryset(self):
        """태그를 기준으로 게시물 검색"""
        tags = self.request.query_params.getlist("tags")
        if tags:
            return (
                Post.objects.filter(tags__name__in=tags)
                .distinct()
                .order_by("-created_at")
            )
        return Post.objects.none()

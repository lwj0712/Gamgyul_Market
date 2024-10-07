from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import LimitOffsetPagination
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from .models import Post, Comment, Like
from accounts.models import Follow, User
from .serializers import (
    PostSerializer,
    CommentSerializer,
    LikeSerializer,
)


class PostPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100


class PostListView(generics.ListAPIView):
    """게시물 목록 조회 view"""

    serializer_class = PostSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "insta/post_list.html"
    permission_classes = [AllowAny]
    pagination_class = PostPagination

    def get_queryset(self):
        """
        사용자가 팔로우한 사용자들의 게시물 또는
        인기 사용자의 게시물 반환
        """
        user = self.request.user

        if user.is_authenticated:
            # 팔로우한 사용자들의 게시물을 가져옴
            followed_users = Follow.objects.filter(follower=user).values_list(
                "followed_user", flat=True
            )

            if followed_users.exists():
                return Post.objects.filter(user__in=followed_users).order_by(
                    "-created_at"
                )

        # 팔로우한 사용자가 없거나, 인증되지 않은 사용자일 경우 팔로워가 많은 사용자의 게시물 반환
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

    def get(self, request, *args, **kwargs):
        """게시물 작성 페이지 렌더링"""
        return render(request, "insta/post_create.html")

    def post(self, request, *args, **kwargs):
        """게시물 작성 처리"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)  # 사용자 정보 추가 후 게시물 생성
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
        return [AllowAny()]  # 게시글 상세 조회 시 인증 여부 상관없이 허용

    def perform_update(self, serializer):
        """수정 시 작성한 사용자만 가능하도록 설정"""
        instance = serializer.instance
        if instance.user != self.request.user:
            raise PermissionDenied("글 작성자만 수정할 수 있습니다.")
        serializer.save()


class PostDeleteView(generics.DestroyAPIView):
    """게시물 삭제 view"""

    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        """삭제 시 작성한 사용자만 가능하도록 설정"""
        if instance.user != self.request.user:
            raise PermissionDenied("글 작성자만 삭제할 수 있습니다.")
        instance.delete()


class CommentListView(generics.ListCreateAPIView):
    """댓글 목록 조회 및 작성 view"""

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
        return [AllowAny()]  # 댓글 조회는 누구나 가능

    def perform_destroy(self, instance):
        """삭제 시 작성한 사용자만 가능하도록 설정"""
        if instance.user != self.request.user:
            raise PermissionDenied("댓글 작성자만 삭제할 수 있습니다.")
        instance.delete()


class LikeView(generics.GenericAPIView):
    """좋아요 추가 및 취소 view"""

    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        """좋아요 추가 또는 취소"""
        post = get_object_or_404(Post, id=post_id)
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if created:
            # 좋아요가 추가되었을 때
            return Response(status=status.HTTP_201_CREATED)
        else:
            # 좋아요가 이미 존재할 때 삭제
            like.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, post_id):
        """좋아요를 누른 사용자 목록 조회"""
        post = get_object_or_404(Post, id=post_id)
        likes = Like.objects.filter(post=post).select_related("user")
        serializer = self.get_serializer(likes, many=True)
        return Response(serializer.data)

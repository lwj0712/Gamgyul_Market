from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, Comment, Like, PostImage
from accounts.models import Follow, User
from config.pagination import LimitOffsetPagination, PageNumberPagination
from .filters import PostFilter
from .serializers import (
    PostSerializer,
    CommentSerializer,
    LikeSerializer,
)


class PostListView(generics.ListAPIView):
    """게시물 목록 조회 view"""

    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    pagination_class = LimitOffsetPagination

    @extend_schema(
        summary="게시물 목록 조회",
        description=(
            "사용자가 팔로우한 사용자들과 본인의 최신 게시물을 가져옵니다. 팔로우한 사용자가 없을 경우, 본인과 인기 사용자의 게시물을 반환합니다."
        ),
        parameters=[
            OpenApiParameter(
                name="limit",
                description="결과의 최대 수",
                required=False,
                type=int,
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="limit 값 예시",
                        description="최대 10개의 게시물을 반환",
                        value=10,
                    )
                ],
            ),
            OpenApiParameter(
                name="offset",
                description="결과의 시작점",
                required=False,
                type=int,
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="offset 값 예시",
                        description="처음부터가 아닌 5번째 게시물부터 시작",
                        value=5,
                    )
                ],
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="게시물 목록 반환에 성공하였습니다.",
                response={
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"},
                        "next": {"type": "string", "nullable": True},
                        "previous": {"type": "string", "nullable": True},
                        "results": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Post"},
                        },
                    },
                },
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="성공적인 응답 예시",
                        description="게시물 목록을 반환합니다.",
                        value={
                            "count": 2,
                            "next": None,
                            "previous": None,
                            "results": [
                                {
                                    "id": 1,
                                    "title": "첫 번째 게시물",
                                    "content": "이것은 첫 번째 게시물입니다.",
                                    "created_at": "2024-10-07T10:00:00Z",
                                },
                                {
                                    "id": 2,
                                    "title": "두 번째 게시물",
                                    "content": "이것은 두 번째 게시물입니다.",
                                    "created_at": "2024-10-07T12:00:00Z",
                                },
                            ],
                        },
                    )
                ],
            ),
        },
        tags=["post"],
    )
    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            """팔로우한 사용자 목록"""
            following_users = Follow.objects.filter(follower=user).values_list(
                "following", flat=True
            )

            """팔로우한 사용자의 게시물 + 본인이 작성한 게시물"""
            if following_users.exists():
                posts = Post.objects.filter(
                    Q(user__in=following_users) | Q(user=user)
                ).order_by("-created_at")
            else:
                """팔로우한 사용자가 없으면 본인 게시물만 조회"""
                posts = Post.objects.filter(user=user).order_by("-created_at")
        else:
            """비로그인 상태에서는 게시물 없음"""
            posts = Post.objects.none()

        """인기 사용자의 게시물 조회"""
        popular_users = User.objects.annotate(
            followers_count=Count("followers")
        ).order_by("-followers_count")[:10]
        popular_posts = Post.objects.filter(user__in=popular_users)

        if user.is_authenticated:
            if not following_users.exists():
                """팔로우한 사용자가 없으면 본인 게시물, 인기 사용자 게시물 조회"""
                posts = posts | popular_posts
        else:
            """비로그인 상태에서는 인기 사용자 게시물만 조회"""
            posts = popular_posts

        return posts.order_by("-created_at")

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

    @extend_schema(
        summary="게시물 작성",
        description="사용자가 텍스트와 이미지를 포함한 게시물을 작성합니다. ",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "images": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                    },
                    "location": {"type": "string"},
                    "tags": {"type": "list"},
                },
                "required": ["content", "images"],
            }
        },
        responses={
            201: OpenApiResponse(
                description="게시물 작성에 성공하였습니다.",
                response=PostSerializer,
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="성공적인 게시물 작성 예시",
                        value={
                            "id": 1,
                            "content": "게시물 내용",
                            "image": "http://example.com/media/posts/image.jpg",
                            "created_at": "2024-10-07T12:00:00Z",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="잘못된 요청 데이터입니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="잘못된 요청 예시",
                        value={"detail": "필수 필드가 누락되었습니다."},
                    )
                ],
            ),
        },
        tags=["post"],
    )
    def post(self, request, *args, **kwargs):
        """게시물 작성 처리"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(
            {"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )


class PostDetailView(generics.RetrieveUpdateAPIView):
    """게시물 상세 조회, 수정 view"""

    queryset = Post.objects.all()
    serializer_class = PostSerializer
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        summary="게시물 상세 조회 및 수정",
        description="게시물의 상세 내용을 조회하거나 수정할 수 있습니다. 수정은 작성자만 가능합니다.",
        responses={
            200: OpenApiResponse(
                description="게시물 조회에 성공하였습니다.",
                response=PostSerializer,
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="성공적인 게시물 조회 예시",
                        value={
                            "id": 1,
                            "content": "이것은 첫 번째 게시물입니다.",
                            "location": "제주",
                            "created_at": "2024-10-07T12:00:00Z",
                            "updated_at": "2024-10-08T12:00:00Z",
                            "tags": ["여행", "제주"],
                            "uploaded_images": [
                                {"image": "http://example.com/media/posts/image.jpg"}
                            ],
                        },
                    )
                ],
            ),
            204: OpenApiResponse(
                description="게시물 수정에 성공하였습니다.",
            ),
            403: OpenApiResponse(
                description="수정 권한이 없습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="수정 권한 없음",
                        value={"detail": "글 작성자만 수정할 수 있습니다."},
                    )
                ],
            ),
        },
        tags=["post"],
    )
    def get_permissions(self):
        """사용자 권한 설정"""
        if self.request.method == "PATCH":
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_update(self, serializer):
        """게시물 작성자만 수정 가능"""
        instance = serializer.instance
        if instance.user != self.request.user:
            raise PermissionDenied("글 작성자만 수정할 수 있습니다.")

        serializer.save()

        existing_images = self.request.data.get("existing_images", None)

        existing_images = self.request.data.get("existing_images", [])
        new_images = self.request.data.getlist("images")

        """새로운 이미지만 추가"""
        for image_data in new_images:
            if image_data:
                PostImage.objects.create(post=instance, image=image_data)

        return instance


class PostDeleteView(generics.DestroyAPIView):
    """게시물 삭제 view"""

    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="게시물 삭제",
        description="게시물을 삭제합니다. 작성자만 삭제할 수 있습니다.",
        responses={
            204: OpenApiResponse(description="게시물 삭제에 성공하였습니다."),
            403: OpenApiResponse(
                description="삭제 권한이 없습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="삭제 권한 없음",
                        value={"detail": "글 작성자만 삭제할 수 있습니다."},
                    )
                ],
            ),
            404: OpenApiResponse(
                description="게시물을 찾을 수 없습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="게시물 없음",
                        value={"detail": "해당 ID의 게시물을 찾을 수 없습니다."},
                    )
                ],
            ),
        },
        tags=["post"],
    )
    def perform_destroy(self, instance):
        """게시물 작성자만 삭제 가능"""
        if instance.user != self.request.user:
            raise PermissionDenied("글 작성자만 삭제할 수 있습니다.")
        instance.delete()


class CommentListCreateView(generics.ListCreateAPIView):
    """댓글 목록 조회, 작성 view"""

    serializer_class = CommentSerializer

    @extend_schema(
        summary="댓글 목록 조회 및 작성",
        description="특정 게시물에 대한 댓글을 조회하거나 작성할 수 있습니다.",
        parameters=[
            OpenApiParameter(
                name="post_id", description="게시물의 ID", required=True, type=int
            )
        ],
        request=CommentSerializer,
        responses={
            200: OpenApiResponse(
                description="댓글 목록 조회에 성공하였습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="댓글 목록 조회 예시",
                        value=[
                            {
                                "id": 1,
                                "content": "첫 번째 댓글입니다.",
                                "created_at": "2024-10-08T09:00:00Z",
                            },
                            {
                                "id": 2,
                                "content": "두 번째 댓글입니다.",
                                "created_at": "2024-10-08T09:05:00Z",
                            },
                        ],
                    )
                ],
            ),
            201: OpenApiResponse(
                description="댓글 작성에 성공하였습니다.",
                response=CommentSerializer,
            ),
            403: OpenApiResponse(
                description="작성 권한이 없습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="작성 권한 없음",
                        value={"detail": "인증된 사용자만 댓글을 작성할 수 있습니다."},
                    )
                ],
            ),
        },
        tags=["comment"],
    )
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

    @extend_schema(
        summary="댓글 상세 조회, 수정 및 삭제",
        description="특정 댓글을 조회하거나 수정, 삭제할 수 있습니다. 수정 및 삭제는 작성자만 가능합니다.",
        responses={
            200: OpenApiResponse(description="댓글 조회에 성공하였습니다."),
            403: OpenApiResponse(
                description="수정/삭제 권한이 없습니다.",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="권한 없음",
                        value={"detail": "댓글 작성자만 수정할 수 있습니다."},
                    )
                ],
            ),
        },
        tags=["comment"],
    )
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

    queryset = Like.objects.all()

    @extend_schema(
        summary="게시물 좋아요 추가/취소",
        description="게시물에 좋아요를 추가하거나 취소할 수 있습니다.",
        parameters=[
            OpenApiParameter(
                name="post_id", description="게시물의 ID", required=True, type=int
            )
        ],
        responses={
            201: OpenApiResponse(description="좋아요 추가 성공"),
            204: OpenApiResponse(description="좋아요 취소 성공"),
            404: OpenApiResponse(description="게시물 찾을 수 없음"),
        },
        tags=["like"],
    )
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if created:
            return Response(status=status.HTTP_201_CREATED)
        like.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="좋아요를 누른 사용자 목록 조회",
        description="특정 게시물에 좋아요를 누른 사용자들의 목록을 조회합니다.",
        responses={
            200: OpenApiResponse(
                description="사용자 목록 조회 성공",
                examples=[
                    OpenApiExample(
                        "Example 1",
                        summary="좋아요 사용자 목록 예시",
                        value=[{"username": "user1"}, {"username": "user2"}],
                    )
                ],
            )
        },
        tags=["like"],
    )
    def get_queryset(self):
        """특정 게시물에 대한 좋아요 목록 반환"""
        post_id = self.kwargs["post_id"]
        return Like.objects.filter(post__id=post_id).select_related("user")

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

    @extend_schema(
        summary="태그로 게시물 검색",
        description="하나 이상의 태그로 게시물을 검색합니다.",
        parameters=[
            OpenApiParameter(
                name="tags",
                description="검색할 태그 목록 (빈 문자열은 허용되지 않음)",
                required=False,
                type=OpenApiTypes.STR,
                examples=[
                    OpenApiExample(
                        "Example tags",
                        value=["tag1", "tag2"],
                    ),
                ],
            ),
        ],
        responses={
            200: OpenApiResponse(description="게시물 검색에 성공하였습니다."),
            404: OpenApiResponse(description="태그에 해당하는 게시물이 없습니다."),
        },
        tags=["tag"],
    )
    def get_queryset(self):
        """태그를 기준으로 게시물 검색"""
        queryset = Post.objects.all()
        return queryset

    def get(self, request, *args, **kwargs):
        """게시물 검색 처리"""
        tags = self.request.query_params.getlist("tags")

        if not tags or (len(tags) == 1 and tags[0] == ""):
            return Response(
                {"detail": "태그에 해당하는 게시물이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        queryset = self.get_queryset()
        filterset = PostFilter(self.request.GET, queryset=queryset)

        if filterset.is_valid():
            print(f"필터링된 게시물 수: {filterset.qs.count()}")
            if filterset.qs.exists():
                serializer = self.get_serializer(filterset.qs, many=True)
                return Response(serializer.data)
            else:
                return Response(
                    {"detail": "태그에 해당하는 게시물이 없습니다."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(
            {"detail": "유효하지 않은 필터입니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

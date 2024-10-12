from django.db import IntegrityError
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from django.core.exceptions import PermissionDenied
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes
from accounts.serializers import (
    FollowSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    PrivacySettingsSerializer,
    ProfileSearchSerializer,
)
from accounts.filters import ProfileFilter
from accounts.models import Follow, PrivacySettings

User = get_user_model()


class ProfileDetailView(generics.RetrieveAPIView):

    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "username"

    @extend_schema(
        summary="사용자 프로필 조회",
        description="지정된 사용자명의 프로필 정보를 조회합니다. 조회자의 권한에 따라 정보 표시가 다를 수 있습니다.",
        parameters=[
            OpenApiParameter(
                name="username",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="조회할 사용자의 username",
            ),
        ],
        responses={
            200: ProfileSerializer,
            401: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "프로필 조회 성공 예시",
                summary="성공적인 프로필 조회",
                description="사용자 프로필 정보가 성공적으로 조회된 경우",
                value={
                    "id": 1,
                    "username": "example_user",
                    "bio": "This is a bio",
                    "profile_image": "http://example.com/profile.jpg",
                    "followers_count": 10,
                    "following_count": 20,
                },
                response_only=True,
            ),
        ],
        tags=["profile"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProfileUpdateView(generics.UpdateAPIView):

    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @extend_schema(
        summary="사용자 프로필 조회",
        description="현재 로그인한 사용자의 프로필 정보를 조회합니다.",
        responses={200: ProfileUpdateSerializer},
        tags=["profile"],
    )
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="사용자 프로필 전체 업데이트",
        description="현재 로그인한 사용자의 프로필 정보를 전체 업데이트합니다.",
        request=ProfileUpdateSerializer,
        responses={200: ProfileUpdateSerializer},
        examples=[
            OpenApiExample(
                "프로필 업데이트 예시",
                value={
                    "bio": "새로운 자기소개",
                    "username": "newuser",
                },
                request_only=True,
            )
        ],
        tags=["profile"],
    )
    def put(self, request, *args, **kwargs):
        """전체 업데이트"""
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="사용자 프로필 부분 업데이트",
        description="현재 로그인한 사용자의 프로필 정보를 부분적으로 업데이트합니다.",
        request=ProfileUpdateSerializer,
        responses={200: ProfileUpdateSerializer},
        examples=[
            OpenApiExample(
                "프로필 부분 업데이트 예제",
                value={
                    "bio": "새로운 자기소개",
                },
                request_only=True,
            )
        ],
        tags=["profile"],
    )
    def patch(self, request, *args, **kwargs):
        """부분 업데이트"""
        return super().partial_update(request, *args, **kwargs)


class PrivacySettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = PrivacySettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        username = self.kwargs.get("username")
        user = get_object_or_404(User, username=username)

        # 현재 로그인한 사용자가 요청한 사용자와 같은지 확인
        if self.request.user != user:
            raise PermissionDenied("You don't have permission to access this settings.")

        return PrivacySettings.objects.get_or_create(user=user)[0]

    @extend_schema(
        summary="프로필 보안 설정 조회",
        description="현재 사용자의 프로필 보안 설정을 조회합니다.",
        responses={
            status.HTTP_200_OK: PrivacySettingsSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenApiTypes.OBJECT,
            status.HTTP_403_FORBIDDEN: OpenApiTypes.OBJECT,
            status.HTTP_404_NOT_FOUND: OpenApiTypes.OBJECT,
        },
        tags=["profile"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="프로필 보안 설정 업데이트",
        description="현재 사용자의 프로필 보안 설정을 업데이트합니다.",
        request=PrivacySettingsSerializer,
        responses={
            status.HTTP_200_OK: PrivacySettingsSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiTypes.OBJECT,
            status.HTTP_401_UNAUTHORIZED: OpenApiTypes.OBJECT,
            status.HTTP_403_FORBIDDEN: OpenApiTypes.OBJECT,
            status.HTTP_404_NOT_FOUND: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "유효한 입력",
                value={
                    "follower_can_see_email": False,
                    "follower_can_see_bio": True,
                    "follower_can_see_posts": True,
                    "follower_can_see_following_list": True,
                    "follower_can_see_follower_list": True,
                    "following_can_see_email": False,
                    "following_can_see_bio": True,
                    "following_can_see_posts": True,
                    "following_can_see_following_list": True,
                    "following_can_see_follower_list": True,
                    "others_can_see_email": False,
                    "others_can_see_bio": True,
                    "others_can_see_posts": True,
                    "others_can_see_following_list": False,
                    "others_can_see_follower_list": False,
                },
                request_only=True,
            ),
        ],
        tags=["profile"],
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="프로필 보안 설정 부분 업데이트",
        description="현재 사용자의 프로필 보안 설정을 부분적으로 업데이트합니다.",
        request=PrivacySettingsSerializer,
        responses={
            status.HTTP_200_OK: PrivacySettingsSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiTypes.OBJECT,
            status.HTTP_401_UNAUTHORIZED: OpenApiTypes.OBJECT,
            status.HTTP_403_FORBIDDEN: OpenApiTypes.OBJECT,
            status.HTTP_404_NOT_FOUND: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "유효한 부분 입력",
                value={
                    "follower_can_see_email": True,
                    "others_can_see_posts": False,
                },
                request_only=True,
            ),
        ],
        tags=["profile"],
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        프로필 보안 설정 업데이트
        부분 업데이트와 전체 업데이트를 모두 지원
        serializer 유효성 검사 후 업데이트
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "detail": "프로필 보안 설정이 성공적으로 업데이트되었습니다.",
                "data": serializer.data,
            }
        )


class FollowView(generics.CreateAPIView):

    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="사용자 팔로우",
        description="특정 사용자를 팔로우합니다. 자기 자신을 팔로우하거나 이미 팔로우한 사용자를 다시 팔로우할 수 없습니다.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="팔로우할 사용자의 ID",
            ),
        ],
        responses={
            status.HTTP_201_CREATED: ProfileSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiTypes.OBJECT,
            status.HTTP_401_UNAUTHORIZED: OpenApiTypes.OBJECT,
            status.HTTP_404_NOT_FOUND: OpenApiTypes.OBJECT,
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "성공 응답",
                value={
                    "id": 2,
                    "username": "user2",
                    "bio": "Hello, I'm User Two",
                    "profile_image": "http://example.com/media/profile_images/user2.jpg",
                    "followers": [
                        {
                            "id": "1",
                            "username": "user1",
                            "profile_image": "http://example.com/media/profile_images/user1.jpg",
                        }
                    ],
                    "following": [],
                    "followers_count": 1,
                    "following_count": 0,
                    "commented_posts": [],
                    "products": [],
                },
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "오류: 자기 팔로우",
                value={"detail": "자기 자신을 팔로우할 수 없습니다."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "오류: 이미 팔로우 중",
                value={"detail": "이미 팔로우한 사용자입니다."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "오류: 사용자를 찾을 수 없음",
                value={"detail": "팔로우하려는 사용자를 찾을 수 없습니다."},
                response_only=True,
                status_codes=["404"],
            ),
            OpenApiExample(
                "오류: 서버 오류",
                value={"detail": "팔로우 처리 중 오류가 발생했습니다."},
                response_only=True,
                status_codes=["500"],
            ),
        ],
        tags=["profile"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        팔로우할 아이디 pk(id)값 불러오기
        팔로우할 사용자가 존재하는지 확인
        자기 자신을 팔로우하려는 경우 예외 처리 후 팔로우 관계 생성 시도
        나머지(사용자를 못찾을 때, 이미 팔로우한 사람, 서버 오류) 예외 처리
        """
        try:
            following_id = self.kwargs["pk"]
            following_user = User.objects.get(id=following_id)
            if request.user.id == following_user.id:
                return Response(
                    {"detail": "자기 자신을 팔로우할 수 없습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            follow, created = Follow.objects.get_or_create(
                follower=request.user, following=following_user
            )

            if created:
                serializer = self.get_serializer(follow)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {"detail": "이미 팔로우한 사용자입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except User.DoesNotExist:
            return Response(
                {"detail": "팔로우하려는 사용자를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": f"팔로우 처리 중 오류가 발생했습니다: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    summary="언팔로우",
    description="특정 사용자를 언팔로우합니다.",
    parameters=[
        OpenApiParameter(
            name="pk", description="언팔로우할 사용자의 ID", required=True, type=int
        ),
    ],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=ProfileSerializer,
            description="언팔로우 성공 및 해당 사용자의 프로필 정보 반환",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="팔로우한 사용자를 찾을 수 없음"
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="이미 팔로우하지 않은 사용자"
        ),
    },
    tags=["profile"],
)
class UnfollowView(generics.DestroyAPIView):
    queryset = Follow.objects.all()

    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def destroy(self, request, *args, **kwargs):
        """
        팔로우 관계가 있는 유저의 id 값 저장 후
        id 값으로 팔로워를 찾고 삭제
        유저, 팔로우 관계 예외처리
        """
        following_id = self.kwargs["pk"]

        try:
            following_user = User.objects.get(id=following_id)
            follow = Follow.objects.get(
                follower=self.request.user, following=following_user
            )
            follow.delete()
            profile_serializer = self.get_serializer(
                following_user, context={"request": request}
            )
            return Response(profile_serializer.data)

        except User.DoesNotExist:
            return Response(
                {"detail": "언팔로우할 유저가 존재하지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Follow.DoesNotExist:
            return Response(
                {"detail": "현재 유저를 팔로우하고 있지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProfileSearchView(generics.ListAPIView):
    serializer_class = ProfileSearchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ProfileFilter

    @extend_schema(
        summary="프로필 검색",
        description="사용자 이름, 이메일을 기반으로 프로필을 검색합니다.",
        parameters=[
            OpenApiParameter(
                name="q",
                description="검색 쿼리 (사용자 이름, 이메일)",
                required=False,
                type=str,
            ),
        ],
        responses={200: ProfileSearchSerializer(many=True)},
        examples=[
            OpenApiExample(
                "응답 예시",
                value=[
                    {
                        "id": 1,
                        "username": "john_doe",
                        "profile_image": "http://example.com/media/profile_images/john.jpg",
                    },
                    {
                        "id": 2,
                        "username": "jane_doe",
                        "profile_image": "http://example.com/media/profile_images/jane.jpg",
                    },
                ],
                response_only=True,
            ),
        ],
        tags=["profile"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return User.objects.all()

    def filter_queryset(self, queryset):
        """쿼리 파라미터 'q'가 없을 때 빈 queryset을 반환"""
        filtered_queryset = super().filter_queryset(queryset)
        if not self.request.query_params.get("q"):
            return queryset.none()
        return filtered_queryset

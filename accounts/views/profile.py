from django.db import IntegrityError
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
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
                    "nickname": "Example User",
                    "bio": "This is a bio",
                    "profile_image": "http://example.com/profile.jpg",
                    "temperature": 36.5,
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
        summary="사용자 프로필 전체 업데이트",
        description="현재 로그인한 사용자의 프로필 정보를 전체 업데이트합니다.",
        request=ProfileUpdateSerializer,
        responses={200: ProfileUpdateSerializer},
        examples=[
            OpenApiExample(
                "프로필 업데이트 예시",
                value={
                    "nickname": "새로운닉네임",
                    "bio": "새로운 자기소개",
                    "email": "new.email@example.com",
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
                    "nickname": "새로운닉네임",
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

    @extend_schema(
        summary="프로필 보안 설정 조회",
        description="현재 사용자의 프로필 보안 설정을 조회합니다.",
        responses={
            status.HTTP_200_OK: PrivacySettingsSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenApiTypes.OBJECT,
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
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="프로필 보안 설정 부분 업데이트",
        description="현재 사용자의 프로필 보안 설정을 부분적으로 업데이트합니다.",
        request=PrivacySettingsSerializer,
        responses={
            status.HTTP_200_OK: PrivacySettingsSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiTypes.OBJECT,
            status.HTTP_401_UNAUTHORIZED: OpenApiTypes.OBJECT,
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

    def get_object(self):
        """
        get_or_create_object 메서드 삭제
        객체가 존재하면 get, 없으면 create
        """
        try:
            return PrivacySettings.objects.get(user=self.request.user)
        except ObjectDoesNotExist:
            return PrivacySettings.objects.create(user=self.request.user)

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
                    "nickname": "User Two",
                    "bio": "Hello, I'm User Two",
                    "profile_image": "http://example.com/media/profile_images/user2.jpg",
                    "temperature": 36.5,
                    "followers": [
                        {
                            "id": "1",
                            "nickname": "User One",
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
                status_codes=["400"],
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

            Follow.objects.create(follower=request.user, following=following_user)

            profile_serializer = ProfileSerializer(
                following_user, context={"request": request}
            )
            return Response(profile_serializer.data, status=status.HTTP_201_CREATED)

        except User.DoesNotExist:
            return Response(
                {"detail": "팔로우하려는 사용자를 찾을 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError:
            return Response(
                {"detail": "이미 팔로우한 사용자입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
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

    @extend_schema(
        summary="프로필 검색",
        description="사용자 이름, 닉네임 또는 이메일을 기반으로 프로필을 검색합니다.",
        parameters=[
            OpenApiParameter(
                name="q",
                description="검색 쿼리 (사용자 이름, 닉네임 또는 이메일)",
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
                        "nickname": "John",
                        "profile_image": "http://example.com/media/profile_images/john.jpg",
                    },
                    {
                        "id": 2,
                        "username": "jane_doe",
                        "nickname": "Jane",
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
        """
        유저 이름, 닉네임, 이메일로 프로필 검색
        """
        query = self.request.query_params.get("q", "")
        if query:
            return User.objects.filter(
                Q(username__icontains=query)
                | Q(nickname__icontains=query)
                | Q(email__icontains=query)
            ).distinct()
        return User.objects.none()

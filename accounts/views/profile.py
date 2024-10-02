from django.db import IntegrityError
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q
from django.shortcuts import get_object_or_404

from django.contrib.auth import get_user_model
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
    """
    프로필 API view
    profileserializer 사용
    """

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
                    # 기타 필드는 조회자의 권한에 따라 다를 수 있음
                },
                response_only=True,
            ),
        ],
        tags=["profile"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class ProfileUpdateView(generics.UpdateAPIView):
    """
    프로필 수정 API view
    """

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
                "Profile Update Example",
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
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="사용자 프로필 부분 업데이트",
        description="현재 로그인한 사용자의 프로필 정보를 부분적으로 업데이트합니다.",
        request=ProfileUpdateSerializer,
        responses={200: ProfileUpdateSerializer},
        examples=[
            OpenApiExample(
                "Profile Partial Update Example",
                value={
                    "nickname": "새로운닉네임",
                },
                request_only=True,
            )
        ],
        tags=["profile"],
    )
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class PrivacySettingsView(generics.RetrieveUpdateAPIView):
    """
    프로필 보안 설정 API view
    privacysettingsserializer 사용
    """

    serializer_class = PrivacySettingsSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="프로필 보안 설정 조회",
        description="현재 사용자의 프로필 보안 설정을 조회합니다.",
        responses={
            status.HTTP_200_OK: PrivacySettingsSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenApiTypes.OBJECT,
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
        },
        examples=[
            OpenApiExample(
                "Valid Input",
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
        },
        examples=[
            OpenApiExample(
                "Valid Partial Input",
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
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        return PrivacySettings.objects.get_or_create(user=self.request.user)[0]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class FollowView(generics.CreateAPIView):
    """
    팔로우 API View
    follow serializer 사용
    create 메서드로 팔로우 기능 구현
    get_or_create로 중복 팔로우 경우의 수 제거
    존재하지 않는 사용자를 팔로우 불가
    자기 자신을 팔로우 불가
    """

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
                "Error: Self Follow",
                value={"detail": "자기 자신을 팔로우할 수 없습니다."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Error: Already Following",
                value={"detail": "이미 팔로우한 사용자입니다."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Error: User Not Found",
                value={"detail": "팔로우하려는 사용자를 찾을 수 없습니다."},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Error: Server Error",
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
        try:
            following_id = self.kwargs["pk"]

            # 팔로우할 사용자가 존재하는지 확인
            following_user = User.objects.get(id=following_id)

            # 자기 자신을 팔로우하려는 경우 예외 처리
            if request.user.id == following_user.id:
                return Response(
                    {"detail": "자기 자신을 팔로우할 수 없습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 팔로우 관계 생성 시도
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
            # 이미 팔로우한 경우
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
    """
    언팔로우 API View
    destoryAPIView로 DELETE 요청 처리
    """

    queryset = Follow.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def destroy(self, request, *args, **kwargs):
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
    """
    프로필 검색 API View
    사용자 이름, 닉네임 또는 이메일을 기반으로 프로필을 검색
    검색 결과는 인증된 사용자에게만 제공
    """

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
                "Example Response",
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
        query = self.request.query_params.get("q", "")
        if query:
            return User.objects.filter(
                Q(username__icontains=query)
                | Q(nickname__icontains=query)
                | Q(email__icontains=query)
            ).distinct()
        return User.objects.none()

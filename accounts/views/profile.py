from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q
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
    get_or_create로 중복 제거
    """

    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        following_id = self.kwargs["pk"]
        following_user = User.objects.get(id=following_id)
        Follow.objects.get_or_create(
            follower=self.request.user, following=following_user
        )
        profile_serializer = ProfileSerializer(
            following_user, context={"request": request}
        )
        return Response(profile_serializer.data)


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
            Follow.objects.filter(
                follower=self.request.user, following=following_user
            ).delete()
            profile_serializer = self.get_serializer(
                following_user, context={"request": request}
            )
            return Response(profile_serializer.data)
        except User.DoesNotExist:
            return Response(
                {"detail": "유저가 존재하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Follow.DoesNotExist:
            return Response(
                {"detail": "현재 유저를 팔로우하고 있지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProfileSearchView(generics.ListAPIView):
    """
    프로필 검색 API View
    """

    serializer_class = ProfileSearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        if query:
            return User.objects.filter(
                Q(username__icontains=query)
                | Q(nickname__icontains=query)
                | Q(email__icontains=query)
            ).distinct()
        return User.objects.none()

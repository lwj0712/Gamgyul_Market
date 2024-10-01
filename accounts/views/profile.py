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

    @extend_schema(
        summary="사용자 프로필 업데이트",
        description="현재 로그인한 사용자의 프로필 정보를 업데이트합니다.",
        request=ProfileUpdateSerializer,
        responses={200: ProfileUpdateSerializer},
        methods=["PUT", "PATCH"],
        examples=[
            OpenApiExample(
                "프로필 업데이트 예시",
                summary="프로필 정보 업데이트",
                description="사용자 프로필 정보 업데이트 요청 예시",
                value={
                    "nickname": "새로운 닉네임",
                    "bio": "새로운 자기소개",
                    "email": "new.email@example.com",
                },
                request_only=True,
            ),
            OpenApiExample(
                "프로필 업데이트 응답 예시",
                summary="프로필 정보 업데이트 응답",
                description="성공적으로 업데이트된 프로필 정보 응답 예시",
                value={
                    "nickname": "새로운 닉네임",
                    "bio": "새로운 자기소개",
                    "email": "new.email@example.com",
                    "profile_image": "http://example.com/new_profile.jpg",
                    "profile_image_thumbnail": "http://example.com/new_profile_thumb.jpg",
                },
                response_only=True,
            ),
        ],
        tags=["profile"],
    )
    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        # patch, put 요청 모두 처리
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # serializer의 save() 메서드를 호출하여 데이터베이스에 변경사항을 저장
        self.perform_update(serializer)

        # 관련 객체들을 미리 가져왔을 때 쓰는 캐시, update되면 cache 비움(최적화)
        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @extend_schema(
        summary="사용자 프로필 부분 업데이트",
        description="현재 로그인한 사용자의 프로필 정보를 부분적으로 업데이트합니다.",
        request=ProfileUpdateSerializer,
        responses={200: ProfileUpdateSerializer},
        examples=[
            OpenApiExample(
                "프로필 부분 업데이트 예시",
                summary="프로필 정보 부분 업데이트",
                description="사용자 프로필 정보 부분 업데이트 요청 예시",
                value={
                    "nickname": "새로운 닉네임",
                },
                request_only=True,
            ),
        ],
        tags=["profile"],
    )
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
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Follow.DoesNotExist:
            return Response(
                {"detail": "You are not following this user."},
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

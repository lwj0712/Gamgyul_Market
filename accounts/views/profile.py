from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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
    팔로우 api view
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
    언팔로우 api view
    destoryAPIView로 DELETE 요청 처리
    """

    queryset = Follow.objects.all()
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        following_id = self.kwargs["pk"]
        following_user = User.objects.get(id=following_id)
        Follow.objects.filter(
            follower=self.request.user, following=following_user
        ).delete()
        profile_serializer = ProfileSerializer(
            following_user, context={"request": request}
        )
        return Response(profile_serializer.data)


class ProfileSearchView(generics.ListAPIView):
    """
    프로필 검색 api view
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

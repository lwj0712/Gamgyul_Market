from django.db.models import Count
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, OpenApiResponse
from insta.models import Post
from accounts.serializers import ProfileSearchSerializer

User = get_user_model()


class FriendRecommendationFilter(filters.FilterSet):
    """
    필터 기능
    팔로워, 관심사, 인기도 타입으로 추천
    """

    recommendation_type = filters.ChoiceFilter(
        choices=[
            ("followers", "Common Followers"),
            ("interests", "Common Interests"),
            ("popular", "Popular Users"),
        ],
        method="filter_recommendations",
    )

    class Meta:
        model = User
        fields = ["recommendation_type"]

    def filter_recommendations(self, queryset, name, value):
        """
        value == "followers" :

        - 사용자가 팔로우하는 사람들이 팔로우하는 사용자들을 필터
        - 현재 팔로우하고 있거나 자기 자신은 제외
        - 공통 팔로워의 수를 계산하여 많은 순서대로 정렬

        value == "interests" :

        - 현재 사용자의 포스트에 사용된 모든 태그 필터
        - 현재 사용자의 태그를 사용한 포스트를 작성한 사용자들 필터
        - 현재 팔로우하고 있거나 자기 자신은 제외
        - 공통 태그가 가장 많은 순서대로 정렬

        value == "popular" :

        - 모든 사용자의 팔로워 수를 계산
        - 현재 팔로우하고 있거나 자기 자신은 제외
        - 팔로워 수가 많은 순서대로 정렬
        """
        user = self.request.user
        following_users = user.following.values_list("following", flat=True)

        if value == "followers":
            return (
                queryset.filter(followers__follower__in=following_users)
                .exclude(id__in=following_users)
                .exclude(id=user.id)
                .annotate(common_count=Count("followers__follower", distinct=True))
                .order_by("-common_count")
            )

        elif value == "interests":
            user_tags = (
                Post.objects.filter(user=user)
                .values_list("tags__name", flat=True)
                .distinct()
            )
            return (
                queryset.filter(post__tags__name__in=user_tags)
                .exclude(id__in=following_users)
                .exclude(id=user.id)
                .annotate(common_tags=Count("post__tags", distinct=True))
                .order_by("-common_tags")
            )

        elif value == "popular":
            return (
                queryset.annotate(followers_count=Count("followers"))
                .exclude(id__in=following_users)
                .exclude(id=user.id)
                .order_by("-followers_count")
            )

        return queryset.none()


class FriendRecommendationView(generics.ListAPIView):
    """
    친구 추천 view
    """

    serializer_class = ProfileSearchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FriendRecommendationFilter

    @extend_schema(
        summary="친구 추천",
        description="현재 로그인한 사용자에게 최대 15명의 친구를 추천합니다. 추천 기준은 공통 팔로워, 공통 관심사(해시태그), 인기도 등입니다.",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=ProfileSearchSerializer(many=True),
                description="추천된 사용자 목록",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="인증되지 않은 사용자",
            ),
        },
        tags=["profile"],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        recommended_users = set()

        for recommendation_type in ["followers", "interests", "popular"]:
            filtered_queryset = self.filterset_class(
                data={"recommendation_type": recommendation_type},
                queryset=queryset,
                request=request,
            ).qs

            for user in filtered_queryset:
                recommended_users.add(user.id)
                if len(recommended_users) >= 15:
                    break

            if len(recommended_users) >= 15:
                break

        final_recommendations = User.objects.filter(id__in=recommended_users)[:15]
        serializer = self.get_serializer(final_recommendations, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        return User.objects.all()

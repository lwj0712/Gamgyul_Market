from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from market.models import Receipt
from insta.models import Post
from accounts.serializers import ProfileSearchSerializer

User = get_user_model()


class FriendRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        recommended_users = set()

        """
        내가 팔로우하고 있는 유저 ID 리스트 생성: following_users
        'following' 필드의 값만을 평면화된 리스트로 반환
        현재 사용자가 팔로우하는 사람들이 팔로우하는 모든 사용자를 찾음: followers__follower__in 역참조 사용
        결과에서 자기 자신은 제외
        이미 팔로우 하고 있는 사용자도 제외
        공통 팔로워 수 계산, 중복 제거, 많은 순으로 정렬(내림차순)
        """
        following_users = user.following.values_list("following", flat=True)
        common_followers = (
            User.objects.filter(followers__follower__in=following_users)
            .exclude(id=user.id)
            .exclude(id__in=following_users)
            .annotate(common_count=Count("followers__follower", distinct=True))
            .order_by("-common_count")
        )

        for common_follower in common_followers:
            recommended_users.add(common_follower.id)
            if len(recommended_users) >= 15:
                break

        """
        공통 관심사(해시태그) 기반 추천
        user의 태그 이름을 평면화된 리스트로 반환하고 중복 값 제거
        user의 테그와 포스트에 달린 태그의 이름을 역참조하여 유저의 정보를 가져옴
        본인, 이미 팔로우 하고 있는 사용자 제외
        같은 태그의 수가 많은 순으로 추천
        """
        user_tags = (
            Post.objects.filter(user=user)
            .values_list("tags__name", flat=True)
            .distinct()
        )
        users_with_common_interests = (
            User.objects.filter(post__tags__name__in=user_tags)
            .exclude(id__in=following_users)
            .exclude(id=user.id)
            .annotate(common_tags=Count("post__tags", distinct=True))
            .order_by("-common_tags")
        )

        for common_interest_user in users_with_common_interests:
            recommended_users.add(common_interest_user.id)
            if len(recommended_users) >= 15:
                break

        """
        최근 거래한 유저 추천
        현재 사용자가 거래한 기록(구매자, 판매자일 경우 모두)에서 팔로워, 중복 제외
        자기 자신 아이디도 제거 후 추천 목록에 추가
        """
        recent_transaction_users = (
            Receipt.objects.filter(Q(buyer=user) | Q(seller=user))
            .exclude(Q(buyer__in=following_users) | Q(seller__in=following_users))
            .values_list("buyer", "seller")
            .distinct()
        )

        for buyer, seller in recent_transaction_users:
            if buyer != user.id:
                recommended_users.add(buyer)
            if seller != user.id:
                recommended_users.add(seller)
            if len(recommended_users) >= 15:
                break

        """
        팔로워가 없는 경우(초기 유저 포함), 유저 중에서 팔로워 수가 많은 순으로 추천
        """
        if not following_users:
            popular_users = User.objects.annotate(
                followers_count=Count("followers")
            ).order_by("-followers_count")[:10]

            for popular_user in popular_users:
                if popular_user.id != user.id:
                    recommended_users.add(popular_user.id)
                if len(recommended_users) >= 15:
                    break

        """최종 추천 유저 목록 생성"""
        final_recommendations = User.objects.filter(id__in=recommended_users)[:15]
        serializer = ProfileSearchSerializer(final_recommendations, many=True)

        return Response(serializer.data)

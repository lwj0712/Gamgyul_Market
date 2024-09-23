from django.contrib.auth.models import AbstractUser
from django.db import models

# settings 변경 필요
from django.conf import settings
from geoposition.fields import GeopositionField

# market, insta 모델 참조 예정.
from market.models import Product, Transaction
from insta.models import Post, Comment


# 사용자 모델 (CustomUser)
class CustomUser(AbstractUser):
    nickname = models.CharField(max_length=100, unique=True)
    profile_image = models.ImageField(
        upload_to="profile_images/", blank=True, null=True
    )
    temperature = models.FloatField(default=36.5)  # 초기 온도 36.5
    location = GeopositionField()  # 위치 정보 (위도와 경도)

    def __str__(self):
        return self.username


# 팔로우 기능
class Follow(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="following", on_delete=models.CASCADE
    )
    followed_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="followers", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "followed_user")

    def __str__(self):
        return f"{self.user} follows {self.followed_user}"


# 프로필 모델
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)  # 추가적인 사용자 정보 (자기 소개)

    # market 앱과 insta 앱에서 역참조 해야 함.
    @property
    def products_for_sale(self):
        # 판매 중인 상품 (is_sold가 False인 상품만 조회)
        return self.user.products.filter(is_sold=False)

    @property
    def commented_posts(self):
        # 내가 댓글 단 게시글 조회
        commented_posts_ids = self.user.comments.values_list(
            "post_id", flat=True
        ).distinct()
        return Post.objects.filter(id__in=commented_posts_ids)

    @property
    def transactions(self):
        # 자신이 관련된 거래 내역 (판매자 또는 구매자로)
        return Transaction.objects.filter(
            models.Q(seller=self.user) | models.Q(buyer=self.user)
        )

    def __str__(self):
        return f"{self.user.username}'s profile"

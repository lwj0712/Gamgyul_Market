from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from imagekit.models import ProcessedImageField, ImageSpecField
from imagekit.processors import ResizeToFill, Thumbnail


class User(AbstractUser):
    """
    커스텀 유저 모델
    """

    profile_image = ProcessedImageField(
        upload_to="profile_images",
        processors=[ResizeToFill(400, 400)],
        format="JPEG",
        options={"quality": 60},
        null=True,
        blank=True,
    )
    profile_image_thumbnail = ImageSpecField(
        source="profile_image",
        processors=[Thumbnail(100, 100)],
        format="JPEG",
        options={"quality": 60},
    )
    temperature = models.FloatField(
        default=36.5, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    nickname = models.CharField(max_length=50, unique=True, null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.username


class SocialAccount(models.Model):
    """
    소셜 계정 유저 모델
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="social_accounts"
    )
    provider = models.CharField(max_length=30)
    uid = models.CharField(max_length=255, unique=True)
    extra_data = models.JSONField(default=dict)

    class Meta:
        unique_together = ("provider", "uid")

    def __str__(self):
        return f"{self.user.username} - {self.provider}"


class Follow(models.Model):
    """
    팔로우 관계 모델
    """

    follower = models.ForeignKey(
        User, related_name="following", on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        User, related_name="followers", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class PrivacySettings(models.Model):
    """
    프로필 공개 설정 모델
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="privacy_settings",
    )

    # 팔로워에게 공개될 정보
    follower_can_see_email = models.BooleanField(default=False)
    follower_can_see_bio = models.BooleanField(default=True)
    follower_can_see_posts = models.BooleanField(default=True)
    follower_can_see_following_list = models.BooleanField(default=True)
    follower_can_see_follower_list = models.BooleanField(default=True)

    # 팔로잉에게 공개될 정보
    following_can_see_email = models.BooleanField(default=False)
    following_can_see_bio = models.BooleanField(default=True)
    following_can_see_posts = models.BooleanField(default=True)
    following_can_see_following_list = models.BooleanField(default=True)
    following_can_see_follower_list = models.BooleanField(default=True)

    # 둘 다 아닌 사람들에게 공개될 정보
    others_can_see_email = models.BooleanField(default=False)
    others_can_see_bio = models.BooleanField(default=True)
    others_can_see_posts = models.BooleanField(default=True)
    others_can_see_following_list = models.BooleanField(default=False)
    others_can_see_follower_list = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Privacy Settings"

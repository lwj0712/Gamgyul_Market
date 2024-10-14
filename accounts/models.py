from django.contrib.auth.models import AbstractUser
from django.db import models
from imagekit.models import ProcessedImageField, ImageSpecField
from imagekit.processors import ResizeToFill, Thumbnail


class User(AbstractUser):
    """
    커스텀 유저 모델
    """

    email = models.EmailField("이메일 주소", unique=True)
    username = models.CharField(
        "사용자명",
        max_length=150,
        unique=True,
        help_text="필수 항목입니다. 150자 이하로 작성해주세요. 문자, 숫자 그리고 @/./+/-/_만 사용 가능합니다.",
        validators=[AbstractUser.username_validator],
        error_messages={
            "unique": "이미 사용 중인 사용자명입니다.",
        },
    )
    profile_image = models.URLField(max_length=1000)
    profile_image_thumbnail = models.URLField(max_length=1000)
    bio = models.TextField(max_length=500, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username

    def get_followers_count(self):
        return self.followers.count()


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
        User, on_delete=models.CASCADE, related_name="following"
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers"
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
        User, on_delete=models.CASCADE, related_name="privacy_settings"
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

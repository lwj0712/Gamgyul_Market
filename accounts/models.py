from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    profile_image = models.ImageField(
        upload_to="profile_images/", null=True, blank=True
    )
    temperature = models.FloatField(
        default=36.5, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    nickname = models.CharField(max_length=50, unique=True)
    bio = models.TextField(max_length=500, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.username


class SocialAccount(models.Model):
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

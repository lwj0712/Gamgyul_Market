from rest_framework import serializers
from .models import User, SocialAccount, Follow


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "profile_image",
            "temperature",
            "nickname",
            "bio",
            "latitude",
            "longitude",
        )
        read_only_fields = ("id", "temperature")


class SocialAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialAccount
        fields = ("id", "user", "provider", "uid")
        read_only_fields = ("id",)


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("id", "follower", "following", "created_at")
        read_only_fields = ("id", "created_at")


class UserProfileSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "profile_image",
            "temperature",
            "nickname",
            "bio",
            "latitude",
            "longitude",
            "followers_count",
            "following_count",
        )
        read_only_fields = ("id", "temperature", "followers_count", "following_count")

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from allauth.socialaccount.models import SocialAccount

# from insta.models import Comment, Post
from market.models import Product

User = get_user_model()


class SocialAccountSerializer(serializers.ModelSerializer):
    """
    소셜 계정 정보를 위한 serializer
    """

    class Meta:
        model = SocialAccount
        fields = ("provider", "uid", "extra_data")


class UserSerializer(serializers.ModelSerializer):
    """
    회원가입 serializer
    password2: 비밀번호 확인 메서드 후 회원 정보에서 제거
    소셜 계정 정보 추가
    """

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    social_accounts = SocialAccountSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "nickname": {"required": True},
            "bio": {"required": False},
            "profile_image": {"required": False},
            "latitude": {"required": False},
            "longitude": {"required": False},
            "temperature": {"read_only": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "비밀번호가 일치하지 않습니다."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


class SocialLoginSerializer(serializers.Serializer):
    """
    소셜 로그인을 위한 serializer
    """

    provider = serializers.CharField(max_length=30)
    access_token = serializers.CharField(max_length=4096, trim_whitespace=True)


class LoginSerializer(serializers.Serializer):
    """
    로그인 serializer
    """

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "nickname", "profile_image")


# class CommentedPostSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Post
#         fields = ("id", "content", "created_at")


class ProductSerializer(serializers.ModelSerializer):
    """
    Product 정보 불러오기
    """

    class Meta:
        model = Product
        fields = "__all__"


class ProfileSerializer(serializers.ModelSerializer):
    """
    프로필 정보 표시
    기본 정보, 마켓 정보, 팔로우 관계와 수, 댓글 단 post 내용
    """

    followers = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    # commented_posts = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "nickname",
            "bio",
            "profile_image",
            "temperature",
            "followers",
            "following",
            "followers_count",
            "following_count",
            "commented_posts",
            "products",
        )

    def get_followers(self, obj):
        return FollowSerializer(obj.followers.all(), many=True).data

    def get_following(self, obj):
        return FollowSerializer(obj.following.all(), many=True).data

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    # def get_commented_posts(self, obj):
    #     comments = (
    #         Comment.objects.filter(user=obj).values_list("post", flat=True).distinct()
    #     )
    #     posts = Post.objects.filter(id__in=comments)
    #     return CommentedPostSerializer(posts, many=True).data

    def get_products(self, obj):
        products = Product.objects.filter(user=obj)
        return ProductSerializer(products, many=True).data

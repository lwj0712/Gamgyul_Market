import os
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.conf import settings
from allauth.socialaccount.models import SocialAccount
from insta.models import Comment, Post
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
    password2 필드 제거: 비밀번호 확인은 프론트엔드에서 처리
    유효성 검사 로직 제거
    소셜 계정 정보 추가
    """

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
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

    def validate_profile_image(self, value):
        if value:
            # 파일 크기 제한
            if value.size > settings.MAX_PROFILE_IMAGE_SIZE:
                raise ValidationError(
                    f"이미지 파일 크기는 {settings.MAX_PROFILE_IMAGE_SIZE / (1024 * 1024)}MB를 초과할 수 없습니다."
                )

            # 이미지 크기 제한
            width, height = get_image_dimensions(value)
            if (
                width > settings.MAX_PROFILE_IMAGE_WIDTH
                or height > settings.MAX_PROFILE_IMAGE_HEIGHT
            ):
                raise ValidationError(
                    f"이미지 크기는 {settings.MAX_PROFILE_IMAGE_WIDTH}x{settings.MAX_PROFILE_IMAGE_HEIGHT} 픽셀을 초과할 수 없습니다."
                )

            # 파일 확장자 제한
            allowed_extensions = settings.ALLOWED_PROFILE_IMAGE_EXTENSIONS
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(
                    f"허용되는 이미지 형식은 {', '.join(allowed_extensions)}입니다."
                )

        return value

    def create(self, validated_data):
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


class PasswordChangeSerializer(serializers.Serializer):
    """
    비밀번호 변경 serializer
    이전 비밀번호가 올바른 지 유효성 검사
    통과 시 new_password로 변경해서 저장
    """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("이전 비밀번호가 올바르지 않습니다.")
        return value

    def save(self, **kwargs):
        password = self.validated_data["new_password"]
        user = self.context["request"].user
        user.set_password(password)
        user.save()
        return user


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "nickname", "profile_image")


class CommentedPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "content", "created_at")


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
    commented_posts = serializers.SerializerMethodField()
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

    def get_commented_posts(self, obj):
        comments = (
            Comment.objects.filter(user=obj).values_list("post", flat=True).distinct()
        )
        posts = Post.objects.filter(id__in=comments)
        return CommentedPostSerializer(posts, many=True).data

    def get_products(self, obj):
        products = Product.objects.filter(user=obj)
        return ProductSerializer(products, many=True).data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    프로필 업데이트 serializer
    nickname, bio, email, profile_image 변경
    """

    class Meta:
        model = User
        fields = ["nickname", "bio", "email", "profile_image"]
        extra_kwargs = {
            "email": {"required": False},
            "profile_image": {"required": False},
        }

    def validate_email(self, value):
        # 현재 사용자를 제외한 유저들의 email 체크
        if User.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("이 이메일은 이미 사용 중에 있습니다.")
        return value

    def validate_profile_image(self, value):
        if value:
            # 파일 크기 제한
            if value.size > settings.MAX_PROFILE_IMAGE_SIZE:
                raise ValidationError(
                    f"이미지 파일 크기는 {settings.MAX_PROFILE_IMAGE_SIZE / (1024 * 1024)}MB를 초과할 수 없습니다."
                )

            # 이미지 크기 제한
            width, height = get_image_dimensions(value)
            if (
                width > settings.MAX_PROFILE_IMAGE_WIDTH
                or height > settings.MAX_PROFILE_IMAGE_HEIGHT
            ):
                raise ValidationError(
                    f"이미지 크기는 {settings.MAX_PROFILE_IMAGE_WIDTH}x{settings.MAX_PROFILE_IMAGE_HEIGHT} 픽셀을 초과할 수 없습니다."
                )

            # 파일 확장자 제한
            allowed_extensions = settings.ALLOWED_PROFILE_IMAGE_EXTENSIONS
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(
                    f"허용되는 이미지 형식은 {', '.join(allowed_extensions)}입니다."
                )

        return value

    def update(self, instance, validated_data):
        # 업데이트된 이미지 파일 받아옴
        profile_image = validated_data.get("profile_image")
        if profile_image and isinstance(profile_image, InMemoryUploadedFile):
            if instance.profile_image:
                instance.profile_image.delete(
                    save=False
                )  # 기존 프로필이 있다면 제거 후 생성
            instance.profile_image = profile_image

        # Update other fields
        instance.nickname = validated_data.get("nickname", instance.nickname)
        instance.bio = validated_data.get("bio", instance.bio)
        instance.email = validated_data.get("email", instance.email)

        instance.save()
        return instance

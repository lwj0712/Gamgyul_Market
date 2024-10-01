from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.uploadedfile import InMemoryUploadedFile
from allauth.socialaccount.models import SocialAccount
from insta.models import Comment, Post
from market.models import Product
from .models import PrivacySettings

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
    """

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    social_accounts = SocialAccountSerializer(many=True, read_only=True)
    profile_image_thumbnail = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "nickname",
            "bio",
            "profile_image",
            "profile_image_thumbnail",
            "social_accounts",
            "temperature",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "nickname": {"required": False},
            "bio": {"required": False},
            "profile_image": {"required": False},
            "profile_image_thumbnail": {"required": False},
            "latitude": {"required": False},
            "longitude": {"required": False},
            "temperature": {"read_only": True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class SocialLoginSerializer(serializers.Serializer):
    """
    소셜 로그인을 위한 serializer
    """

    provider = serializers.CharField(max_length=30)
    access_token = serializers.CharField(max_length=4096, trim_whitespace=True)


class CustomLoginSerializer(serializers.Serializer):
    """
    로그인 serializer
    """

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class CustomPasswordChangeSerializer(serializers.Serializer):
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
    """
    팔로우 serializer
    """

    id = serializers.CharField(read_only=True)
    nickname = serializers.CharField(read_only=True)
    profile_image = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "nickname", "profile_image")


class CommentedPostSerializer(serializers.ModelSerializer):
    """
    내가 단 댓글의 포스트 정보
    """

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

    # get_<field명> 메서드로 데이터 직렬화
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

    @extend_schema_field(FollowSerializer(many=True))
    def get_followers(self, obj):
        return FollowSerializer(obj.followers.all(), many=True).data

    @extend_schema_field(FollowSerializer(many=True))
    def get_following(self, obj):
        return FollowSerializer(obj.following.all(), many=True).data

    @extend_schema_field(OpenApiTypes.INT)
    def get_followers_count(self, obj):
        return obj.followers.count()

    @extend_schema_field(OpenApiTypes.INT)
    def get_following_count(self, obj):
        return obj.following.count()

    @extend_schema_field(CommentedPostSerializer(many=True))
    def get_commented_posts(self, obj):
        comments = (
            Comment.objects.filter(user=obj).values_list("post", flat=True).distinct()
        )
        posts = Post.objects.filter(id__in=comments)
        return CommentedPostSerializer(posts, many=True).data

    @extend_schema_field(ProductSerializer(many=True))
    def get_products(self, obj):
        products = Product.objects.filter(user=obj)
        return ProductSerializer(products, many=True).data

    def get_viewer_type(self, viewer, profile_owner):
        # 프로필 열람 타입 구분 메서드
        is_follower = viewer.following.filter(following=profile_owner).exists()
        is_following = viewer.followers.filter(follower=profile_owner).exists()

        if is_follower and is_following:
            return "follower"  # 팔로워 기준 값 리턴
        elif is_follower:
            return "follower"
        elif is_following:
            return "following"
        else:
            return "others"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and request.user != instance:
            viewer_type = self.get_viewer_type(request.user, instance)
            privacy_settings = PrivacySettings.objects.get_or_create(user=instance)[0]

            fields_to_check = {
                "email": f"{viewer_type}_can_see_email",
                "bio": f"{viewer_type}_can_see_bio",
                "followers": f"{viewer_type}_can_see_follower_list",
                "following": f"{viewer_type}_can_see_following_list",
                "commented_posts": f"{viewer_type}_can_see_posts",
                "products": f"{viewer_type}_can_see_posts",
            }

            for field, setting in fields_to_check.items():
                if not getattr(privacy_settings, setting, True):
                    data.pop(field, None)

            # 항상 표시되어야 하는 필드들
            always_visible = [
                "id",
                "username",
                "nickname",
                "profile_image",
                "temperature",
            ]
            data = {k: v for k, v in data.items() if k in always_visible or k in data}

        return data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    프로필 업데이트 serializer
    """

    profile_image_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "nickname",
            "bio",
            "email",
            "profile_image",
            "profile_image_thumbnail",
        ]
        extra_kwargs = {
            "email": {"required": False},
            "profile_image": {"required": False},
        }

    @extend_schema_field(OpenApiTypes.URI)
    def get_profile_image_thumbnail(self, obj):
        # 필드명 url로 인식
        if obj.profile_image:
            return obj.profile_image_thumbnail.url
        return None

    def validate_email(self, value):
        # 현재 사용자를 제외한 유저들의 email 체크
        if User.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("이 이메일은 이미 사용 중에 있습니다.")
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

        # 다른 필드도 업데이트
        instance.nickname = validated_data.get("nickname", instance.nickname)
        instance.bio = validated_data.get("bio", instance.bio)
        instance.email = validated_data.get("email", instance.email)

        instance.save()
        return instance


class PrivacySettingsSerializer(serializers.ModelSerializer):
    """
    프로필 설정 serializer
    """

    class Meta:
        model = PrivacySettings
        exclude = ("user",)

    def get_visible_fields(self, viewer_type):
        if viewer_type not in ["follower", "following", "others"]:
            raise serializers.ValidationError("Invalid viewer type")

        visible_fields = []
        for field in self.Meta.model._meta.fields:
            if field.name.startswith(f"{viewer_type}_can_see_") and getattr(
                self.instance, field.name
            ):
                visible_fields.append(field.name.replace(f"{viewer_type}_can_see_", ""))

        return visible_fields


class ProfileSearchSerializer(serializers.ModelSerializer):
    """
    프로필 검색 serializer
    """

    class Meta:
        model = User
        fields = ["id", "username", "nickname", "profile_image"]

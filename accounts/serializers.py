from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.uploadedfile import InMemoryUploadedFile
from allauth.socialaccount.models import SocialAccount
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
            "bio",
            "profile_image",
            "profile_image_thumbnail",
            "social_accounts",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "username": {"required": True},
            "bio": {"required": False},
            "profile_image": {"required": False},
            "profile_image_thumbnail": {"required": False},
        }

    def validate_email(self, value):
        """
        이미 사용 중인 이메일 사용 불가 유효성 검사
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value

    def validate_email(self, value):
        """
        이미 사용 중인 유저이름 사용 불가 유효성 검사
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 사용 중인 유저 이름입니다.")
        return value

    def create(self, validated_data):
        """통과하면 생성"""
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

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class CustomPasswordChangeSerializer(serializers.Serializer):
    """
    비밀번호 변경 serializer
    이전 비밀번호가 올바른 지 유효성 검사
    통과 시 new_password로 변경해서 저장
    """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate(self, data):
        if data["old_password"] == data["new_password"]:
            raise serializers.ValidationError(
                "새 비밀번호는 이전 비밀번호와 달라야 합니다."
            )
        return data

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
    username = serializers.CharField(read_only=True)
    profile_image = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "profile_image")


class ProductSerializer(serializers.ModelSerializer):
    """
    Product 정보 불러오기
    """

    class Meta:
        model = Product
        fields = (
            "user",
            "name",
            "price",
            "description",
            "stock",
            "variety",
            "growing_region",
            "harvest_date",
        )


class ProfileSerializer(serializers.ModelSerializer):
    """
    프로필 정보 표시
    기본 정보, 마켓 정보, 팔로우 관계와 수, 댓글 단 post 내용
    get_<field명> 메서드로 데이터 직렬화
    """

    followers = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "bio",
            "profile_image",
            "followers",
            "following",
            "followers_count",
            "following_count",
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

    @extend_schema_field(ProductSerializer(many=True))
    def get_products(self, obj):
        products = Product.objects.filter(user=obj)
        return ProductSerializer(products, many=True).data

    def get_viewer_type(self, viewer, profile_owner):
        """
        프로필 열람 타입 구분 메서드
        팔로워 기준 값 리턴
        """
        is_follower = viewer.following.filter(following=profile_owner).exists()
        is_following = viewer.followers.filter(follower=profile_owner).exists()

        if is_follower and is_following:
            return "follower"
        elif is_follower:
            return "follower"
        elif is_following:
            return "following"
        else:
            return "others"

    def to_representation(self, instance):
        """
        요청한 사용자가 프로필 소유자가 아닌 경우 프라이버시 설정을 적용
        요청한 사용자의 유형(팔로워, 팔로잉, 기타)을 확인
        프라이버시 설정에 따라 특정 필드 필터링
        항상 표시되어야 하는 필드들 설정
        """
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
                "products": f"{viewer_type}_can_see_posts",
            }

            for field, setting in fields_to_check.items():
                if not getattr(privacy_settings, setting, True):
                    data.pop(field, None)

            always_visible = [
                "id",
                "username",
                "profile_image",
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
            "username",
            "bio",
            "profile_image",
            "profile_image_thumbnail",
        ]
        extra_kwargs = {
            "username": {"required": False},
            "profile_image": {"required": False},
        }

    @extend_schema_field(OpenApiTypes.URI)
    def get_profile_image_thumbnail(self, obj):
        """필드명 url로 인식"""
        if obj.profile_image:
            return obj.profile_image_thumbnail.url
        return None

    def validate_username(self, value):
        """현재 사용자를 제외한 유저들의 username 체크"""
        if User.objects.exclude(pk=self.instance.pk).filter(username=value).exists():
            raise serializers.ValidationError("이 사용자명은 이미 사용 중입니다.")
        return value

    def update(self, instance, validated_data):
        """
        업데이트된 이미지 파일 받아옴
        기존 프로필이 있다면 제거 후 생성
        다른 필드도 업데이트
        """
        profile_image = validated_data.get("profile_image")
        if profile_image and isinstance(profile_image, InMemoryUploadedFile):
            if instance.profile_image:
                instance.profile_image.delete(save=False)
            instance.profile_image = profile_image

        instance.bio = validated_data.get("bio", instance.bio)
        instance.username = validated_data.get("username", instance.username)

        instance.save()
        return instance


class PrivacySettingsSerializer(serializers.ModelSerializer):
    """
    프로필 설정 serializer
    """

    class Meta:
        model = PrivacySettings
        exclude = ("user",)

    def validate(self, data):
        """
        필드 이름이 유효한 접두사로 시작하는지 확인
        값이 불리언인지 확인하고 에러 처리
        """
        valid_prefixes = ["follower_can_see_", "following_can_see_", "others_can_see_"]

        for field_name, value in data.items():
            if not any(field_name.startswith(prefix) for prefix in valid_prefixes):
                raise serializers.ValidationError(f"잘못된 필드 이름: {field_name}")

            if not isinstance(value, bool):
                raise serializers.ValidationError(
                    f"{field_name} 참, 거짓 값이어야 합니다"
                )

        return data

    def get_visible_fields(self, viewer_type):
        """
        타입이 정해지지 않은 사용자 필드 못봄
        타입에 따라 볼 수 있는 필드 값 적용
        """
        if viewer_type not in ["follower", "following", "others"]:
            raise serializers.ValidationError("잘못된 뷰어 유형입니다.")

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
        fields = ["id", "username", "profile_image"]

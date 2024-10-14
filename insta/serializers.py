from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from .models import Post, PostImage, Comment, Like
from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "profile_image"]


class PostImageSerializer(serializers.ModelSerializer):
    """게시물 이미지 모델의 serializer"""

    class Meta:
        model = PostImage
        fields = ["id", "image"]


class CommentSerializer(serializers.ModelSerializer):
    """댓글 모델의 serializer"""

    user = SimpleUserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "post",
            "parent_comment",
            "content",
            "created_at",
            "replies",
        ]
        read_only_fields = ["user", "post"]

    def get_replies(self, obj):
        """대댓글 리스트 반환"""
        if obj.parent_comment is None:  # 최상위 댓글인 경우에만 대댓글을 가져옴
            replies = Comment.objects.filter(parent_comment=obj).order_by("-created_at")
            return CommentSerializer(replies, many=True).data
        return []

    def validate(self, attrs):
        """대댓글 작성 시 부모 댓글 유효성 검사"""
        if "parent_comment" in attrs:
            parent_comment = attrs["parent_comment"]
            if not Comment.objects.filter(id=parent_comment.id).exists():
                raise serializers.ValidationError("존재하지 않는 부모 댓글입니다.")
        return attrs


class LikeSerializer(serializers.ModelSerializer):
    """좋아요 모델의 serializer"""

    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ["id", "user", "post", "created_at"]
        read_only_fields = ["user", "post"]


class PostSerializer(TaggitSerializer, serializers.ModelSerializer):
    """게시물 모델의 serlializer"""

    user = SimpleUserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    tags = TagListSerializerField(required=False)
    uploaded_images = PostImageSerializer(many=True, read_only=True)
    images = serializers.ListField(
        child=serializers.URLField(
            max_length=255, allow_empty_file=False, use_url=False
        ),
        write_only=True,
        required=True,
    )
    content = serializers.CharField(required=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "content",
            "location",
            "created_at",
            "updated_at",
            "tags",
            "uploaded_images",
            "images",
            "likes_count",
            "comments",
        ]
        read_only_fields = [
            "user",
            "created_at",
            "updated_at",
            "likes_count",
            "comments",
        ]

    def get_likes_count(self, obj):
        """좋아요 수를 반환"""
        return obj.likes.count()

    def create(self, validated_data):
        """게시물 생성 로직"""
        tags_data = validated_data.pop("tags", None)
        images_data = validated_data.pop("images")

        request = self.context.get("request")
        validated_data["user"] = request.user

        if not images_data:
            raise serializers.ValidationError("이미지는 필수입니다.")
        if len(images_data) > 10:
            raise serializers.ValidationError("이미지는 10개까지 첨부할 수 있습니다.")

        post = Post.objects.create(**validated_data)

        """이미지 저장"""
        for image_data in images_data:
            PostImage.objects.create(post=post, image=image_data)

        """태그 추가"""
        if tags_data:
            post.tags.add(*tags_data)

        return post

    def update(self, instance, validated_data):
        """게시물 수정 로직"""
        tags_data = validated_data.pop("tags", None)

        instance.content = validated_data.get("content", instance.content)
        instance.location = validated_data.get("location", instance.location)
        instance.save()

        """태그 수정"""
        if tags_data is not None:
            instance.tags.set(tags_data)

        """이미지 추가 로직"""
        if validated_data.get("images"):
            current_image_count = instance.images.count()
            new_images_count = len(validated_data["images"])

            if new_images_count + current_image_count > 10:
                raise serializers.ValidationError(
                    "이미지는 10개까지 첨부할 수 있습니다."
                )

            for image_data in validated_data["images"]:
                PostImage.objects.create(post=instance, image=image_data)

        return instance

    def to_representation(self, instance):
        """객체를 JSON으로 변환할 때의 표현 정의"""
        representation = super().to_representation(instance)
        representation["tags"] = [str(tag) for tag in instance.tags.all()]
        representation["images"] = [image.image.url for image in instance.images.all()]
        return representation

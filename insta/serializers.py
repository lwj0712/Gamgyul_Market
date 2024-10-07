from rest_framework import serializers
from .models import Post, PostImage, Comment, Like
from taggit.serializers import TagListSerializerField, TaggitSerializer
from accounts.serializers import UserSerializer


class PostImageSerializer(serializers.ModelSerializer):
    """게시물 이미지 모델의 serializer"""

    class Meta:
        model = PostImage
        fields = ["id", "image"]


class CommentSerializer(serializers.ModelSerializer):
    """댓글 모델의 serializer"""

    user = UserSerializer(read_only=True)
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
        ]
        read_only_fields = ["user", "post"]

    def get_replies(self, obj):
        if obj.parent_comment is None:  # 최상위 댓글인 경우에만 대댓글을 가져옴
            replies = Comment.objects.filter(parent_comment=obj)
            return CommentSerializer(replies, many=True).data
        return []


class LikeSerializer(serializers.ModelSerializer):
    """좋아요 모델의 serializer"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ["id", "user", "post", "created_at"]
        read_only_fields = ["user", "post"]


class PostSerializer(serializers.ModelSerializer):
    """게시물 모델의 serlializer"""

    user = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    tags = TagListSerializerField()
    images = PostImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(
            max_length=1000000, allow_empty_file=False, use_url=False
        ),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "content",
            "location",
            "created_at",
            "updated_at",
            "tags",
            "images",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]

    def create(self, validated_data):
        """Post 객체 생성 시 커스텀 동작 정의"""
        tags_data = validated_data.pop("tags", None)
        images_data = validated_data.pop("images", None)

        request = self.context.get("request")
        validated_data["user"] = request.user

        if not images_data or len(images_data) == 0:
            raise serializers.ValidationError("이미지는 필수입니다.")

        if len(images_data) > 10:
            raise serializers.ValidationError("이미지는 10개까지 첨부할 수 있습니다.")

        post = Post.objects.create(**validated_data)

        for image_data in images_data:
            PostImage.objects.create(post=post, **image_data)

        if tags_data:
            post.tags.add(*tags_data)

        return post

    def update(self, instance, validated_data):
        """Post 객체 수정 시 커스텀 동작 정의"""
        tags_data = validated_data.pop("tags", None)
        images_data = validated_data.pop("images", [])

        instance.content = validated_data.get("content", instance.content)
        instance.location = validated_data.get("location", instance.location)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if images_data:
            if len(images_data) + instance.images.count() > 10:
                raise serializers.ValidationError(
                    "이미지는 10개까지 첨부할 수 있습니다."
                )

            for image_data in images_data:
                PostImage.objects.create(post=instance, **image_data)

        return instance

    def to_representation(self, instance):
        """객체를 JSON으로 변환할 때의 표현 정의"""
        representation = super().to_representation(instance)
        representation["tags"] = [str(tag) for tag in instance.tags.all()]
        representation["images"] = [image.image.url for image in instance.images.all()]
        return representation

from rest_framework import serializers
from .models import Post, PostImage, Comment, Like


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ["id", "image"]


class PostSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False
    )
    images = PostImageSerializer(many=True, required=False)

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
            "images",
        ]

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        images_data = validated_data.pop("images", [])
        post = Post.objects.create(**validated_data)
        post.tags.add(*tags_data)

        for image_data in images_data:
            PostImage.objects.create(post=post, **image_data)

        return post


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = "__all__"

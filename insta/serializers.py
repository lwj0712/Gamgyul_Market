from rest_framework import serializers
from .models import Post, PostImage, Comment, Like


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ["id", "image"]


class PostSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, required=False)

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
        tags_data = validated_data.pop("tags", [])
        images_data = validated_data.pop("images", [])

        request = self.context.get("request")
        validated_data["user"] = request.user

        post = Post.objects.create(**validated_data)

        if len(images_data) + post.images.count() > 10:
            raise serializers.ValidationError("이미지는 10개까지 첨부할 수 있습니다.")

        for image_data in images_data:
            PostImage.objects.create(post=post, **image_data)

        post.tags.add(*tags_data)

        return post

    def update(self, instance, validated_data):
        tags_data = validated_data.pop("tags", [])
        images_data = validated_data.pop("images", [])

        instance.content = validated_data.get("content", instance.content)
        instance.location = validated_data.get("location", instance.location)
        instance.save()

        if tags_data:
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
        representation = super().to_representation(instance)
        representation["tags"] = [str(tag) for tag in instance.tags.all()]
        return representation


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = "__all__"

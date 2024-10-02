from rest_framework import serializers
from .models import Product, ProductImage, Review


class ReviewSerializer(serializers.ModelSerializer):
    """
    리뷰 시리얼라이저
    """

    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Review
        fields = ["id", "user", "content", "rating", "created_at"]


class ProductListSerializer(serializers.ModelSerializer):
    """
    상품 리스트 시리얼라이저
    """

    user = serializers.CharField(source="user.username")
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "price", "user", "stock", "average_rating"]


class ProductSerializer(serializers.ModelSerializer):
    """
    상품 시리얼라이저
    """

    average_rating = serializers.FloatField(read_only=True)
    username = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "username",
            "price",
            "description",
            "stock",
            "variety",
            "growing_region",
            "harvest_date",
            "created_at",
            "updated_at",
            "average_rating",
            "images",
        ]

    def get_username(self, obj):
        return obj.user.username

    def get_images(self, obj):
        request = self.context.get("request")
        return (
            [request.build_absolute_uri(image.image.url) for image in obj.images.all()]
            if request
            else []
        )

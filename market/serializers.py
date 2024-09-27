from rest_framework import serializers
from .models import Product, ProductImage, Review


# Review Serializer
class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Review
        fields = ["id", "user", "content", "rating", "created_at"]


class ProductListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")

    class Meta:
        model = Product
        fields = ["id", "name", "price", "user"]


# Product Serializer
class ProductSerializer(serializers.ModelSerializer):

    # reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "price",
            "description",
            "stock",
            "variety",
            "growing_region",
            "harvest_date",
            "created_at",
            "updated_at",
            # "images",
            # "reviews",  # 상품 이미지와 리뷰도 포함
        ]


# ProductImage Serializer
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "product", "image_urls"]

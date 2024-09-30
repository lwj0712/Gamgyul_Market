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
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "price", "user", "stock", "average_rating"]


# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(read_only=True)
    username = serializers.SerializerMethodField()

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
            # "images",
        ]

    def get_username(self, obj):
        return obj.user.username


# ProductImage Serializer
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "product", "image_urls"]

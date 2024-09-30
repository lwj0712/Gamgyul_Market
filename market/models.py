from django.db import models
from django.conf import settings
from django.db.models import Avg


# Product Model
class Product(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1
    )  # user_id
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    stock = models.IntegerField()
    variety = models.CharField(max_length=255, blank=True, null=True)  # 감귤 품종
    growing_region = models.CharField(
        max_length=255, blank=True, null=True
    )  # 재배 지역
    harvest_date = models.DateField(blank=True, null=True)  # 수확 날짜
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def average_rating(self):
        return self.reviews.aggregate(Avg("rating"))["rating_avg"]


# ProductImage Model
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )  # product_id
    image_urls = models.ImageField(upload_to="media/products/")  # 이미지 URL
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"


# Review Model
class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1
    )  # user_id
    product = models.ForeignKey(
        Product, related_name="reviews", on_delete=models.CASCADE
    )  # product_id
    content = models.TextField()  # 리뷰 내용
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 별점 1~5점
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product.name}"


# 영수증? 장부?
class Receipt(models.Model):
    product = models.TextField()
    quantity = models.IntegerField()
    seller = models.TextField()
    buyer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

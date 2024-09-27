from rest_framework import generics, permissions
from .models import Product, ProductImage, Review
from .serializers import ProductListSerializer, ProductSerializer, ReviewSerializer
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.annotate(average_rating=Avg("reviews__rating"))
    serializer_class = ProductListSerializer


class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        product = serializer.save(user=self.request.user)
        images = self.request.FILES.getlist("image_urls")
        for image in images:
            ProductImage.objects.create(product=product, image_urls=image)


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.annotate(average_rating=Avg("reviews__rating"))
    serializer_class = ProductSerializer
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        product = self.get_object()
        reviews = Review.objects.filter(product=product)
        review_serializer = ReviewSerializer(reviews, many=True)
        product_serializer = self.get_serializer(product)
        return Response(
            {
                "product": product_serializer.data,
                "reviews": review_serializer.data,
            }
        )

    def post(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "id"

    def perform_update(self, serializer):
        product = serializer.save()
        images = self.request.FILES.getlist("image_urls")
        for image in images:
            ProductImage.objects.create(product=product, image_urls=image)


class ProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "id"


class IsReviewOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class ReviewDeleteView(generics.DestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewOwner]
    lookup_field = "id"

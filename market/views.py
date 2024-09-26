from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Product, ProductImage, Review
from .serializers import (
    ProductListSerializer,
    ProductSerializer,
    ProductImageSerializer,
    ReviewSerializer,
)


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer


class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def perform_create(self, serializer):
        product = serializer.save()
        images = self.request.FILES.getlist("image_urls")
        for image in images:
            ProductImage.objects.create(product=product, image_urls=image)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = "id"


class ProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = "id"

    def perform_update(self, serializer):
        product = serializer.save()
        images = self.request.FILES.getlist("image_urls")
        for image in images:
            ProductImage.objects.create(product=product, image_urls=image)


class ProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = "id"


class ReviewListView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def perform_create(self, serializer):
        serializer.save()


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer


class ProductImageUploadView(APIView):
    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )

        images = request.FILES.getlist("image_urls")
        for image in images:
            ProductImage.objects.create(product=product, image_urls=image)

        return Response(
            {"message": "Images uploaded successfully"}, status=status.HTTP_201_CREATED
        )

from rest_framework import generics, permissions
from .models import Product, ProductImage, Review
from .serializers import ProductListSerializer, ProductSerializer, ReviewSerializer
from django.shortcuts import get_object_or_404, redirect
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg
from rest_framework.renderers import TemplateHTMLRenderer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.annotate(average_rating=Avg("reviews__rating")).order_by(
        "-created_at"
    )
    serializer_class = ProductListSerializer
    renderer_classes = [TemplateHTMLRenderer]  # HTML 렌더링 설정
    template_name = "market/product_list.html"  # 사용할 템플릿 경로

    def get(self, request, *args, **kwargs):
        products = self.get_queryset()
        return Response({"products": products})


class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        product = serializer.save(user=self.request.user)
        images = self.request.FILES.getlist("image_urls")
        for image in images:
            ProductImage.objects.create(product=product, image_urls=image)


@method_decorator(csrf_exempt, name="dispatch")
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.annotate(average_rating=Avg("reviews__rating"))
    serializer_class = ProductSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "market/product_detail.html"
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        product = self.get_object()
        print("Product ID:", product.id)
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
        try:
            product = self.get_object()
            content = request.POST.get("content")
            rating = request.POST.get("rating")

            # 리뷰 생성
            review = Review.objects.create(
                product=product, user=request.user, content=content, rating=rating
            )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Review created successfully",
                    "data": {
                        "id": review.id,
                        "user": review.user.username,
                        "content": review.content,
                        "rating": review.rating,
                        "created_at": review.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                }
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


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


class ReviewCreateView(generics.CreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        product_id = self.kwargs["product_id"]  # URL에서 product_id를 가져옵니다.
        product = get_object_or_404(Product, id=product_id)
        serializer.save(user=self.request.user, product=product)


class ReviewDeleteView(generics.DestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewOwner]
    lookup_field = "id"

from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
from .models import Product, ProductImage, Review
from .serializers import ProductListSerializer, ProductSerializer, ReviewSerializer
from django.db.models import Avg


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    해당 모델의 작성자가 같은지 확인하는 함수
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class ProductListView(generics.ListAPIView):
    """
    상품 목록을 보여주는 view
    """

    queryset = Product.objects.annotate(average_rating=Avg("reviews__rating")).order_by(
        "-created_at"
    )
    serializer_class = ProductListSerializer
    renderer_classes = [TemplateHTMLRenderer]  # HTML 렌더링 설정
    template_name = "market/product_list.html"  # 사용할 템플릿 경로

    def get(self, request, *args, **kwargs):
        products = self.get_queryset()
        return Response({"products": products})


class ProductCreateView(generics.GenericAPIView):
    """
    상품 등록 view
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "market/product_create.html"

    def get(self, request, *args, **kwargs):
        return Response({"serializer": self.get_serializer()})

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save(user=self.request.user)
            images = request.FILES.getlist("image")

            if len(images) > 5:
                return Response(
                    {"error": "최대 5장까지만 이미지를 업로드할 수 있습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for image in images:
                ProductImage.objects.create(product=product, image=image)

            success_url = reverse("product-detail", kwargs={"id": product.id})
            return HttpResponseRedirect(success_url)

        return Response({"serializer": serializer}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class ProductDetailView(generics.RetrieveAPIView):
    """
    상품 상세 view
    댓글 작성 함수도 포함되어있음
    """

    serializer_class = ProductSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "market/product_detail.html"
    lookup_field = "id"

    def get_queryset(self):
        return Product.objects.annotate(
            average_rating=Avg("reviews__rating")
        ).prefetch_related("images")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        # 디버깅: 이미지 URL 출력
        for image in instance.images.all():
            print(f"Image URL: {image.image.url}")

        return Response(data)

    def get(self, request, *args, **kwargs):
        product = self.get_object()
        reviews = Review.objects.filter(product=product)
        review_serializer = ReviewSerializer(reviews, many=True)
        product_serializer = self.get_serializer(product, context={"request": request})
        return Response(
            {
                "product": product_serializer.data,
                "reviews": review_serializer.data,
            }
        )

    def post(self, request, *args, **kwargs):
        """
        댓글 작성 기능
        """
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
    """
    상품 내용 수정 view
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "id"
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "market/product_update.html"  # 템플릿 경로 지정
    http_method_names = ["get", "post", "patch"]

    def get(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = self.get_serializer(product)
        return Response({"serializer": serializer, "product": product})

    def post(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = self.get_serializer(product, data=request.data, partial=True)

        if serializer.is_valid():
            self.perform_update(serializer)
            # 상품 수정 후 상세 페이지로 리디렉션
            success_url = reverse("product-detail", kwargs={"id": product.id})
            return HttpResponseRedirect(success_url)

        # 유효성 검사 실패 시, 다시 폼을 렌더링
        return Response({"serializer": serializer, "product": product}, status=400)

    def perform_update(self, serializer):
        product = serializer.save()
        images = self.request.FILES.getlist("image")
        for image in images:
            ProductImage.objects.create(product=product, image=image)


class ProductDeleteView(generics.DestroyAPIView):
    """
    상품 삭제 view
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "id"
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "market/product_delete.html"  # 템플릿 경로 지정

    def get(self, request, *args, **kwargs):
        product = self.get_object()
        return Response({"product": product})

    def post(self, request, *args, **kwargs):
        product = self.get_object()
        self.perform_destroy(product)
        # 삭제 후 목록 페이지로 리디렉션
        success_url = reverse("product-list")
        return HttpResponseRedirect(success_url)

    def perform_destroy(self, instance):
        instance.delete()


class IsReviewOwner(permissions.BasePermission):
    """
    댓글 주인확인
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class ReviewDeleteView(generics.DestroyAPIView):
    """
    리뷰 삭제 view
    """

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewOwner]
    lookup_field = "id"

    def delete(self, request, *args, **kwargs):
        try:
            review = self.get_object()
            self.perform_destroy(review)
            return JsonResponse(
                {"status": "success", "message": "Review deleted successfully"}
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

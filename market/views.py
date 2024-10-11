from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from .models import Product, ProductImage, Review
from .serializers import ProductListSerializer, ProductSerializer, ReviewSerializer
from config.pagination import LimitOffsetPagination, PageNumberPagination
from django.db.models import Avg, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from urllib.parse import urlparse


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    해당 모델의 작성자가 같은지 확인하는 함수
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


@extend_schema(
    summary="상품 목록 조회",
    description="모든 상품의 목록을 반환합니다. 검색 기능을 사용하여 특정 상품을 찾을 수 있습니다.",
    parameters=[
        OpenApiParameter(
            name="search",
            type=OpenApiTypes.STR,
            description="상품 이름, 작성자, 품종, 재배 지역으로 검색 (선택사항)",
            required=False,
        ),
    ],
    responses={
        200: OpenApiResponse(
            ProductListSerializer(many=True), description="목록 조회 성공"
        ),
    },
    examples=[
        OpenApiExample(
            "상품 목록 결과 예시",
            summary="상품 목록 조회 결과 예시",
            description="상품 목록 조회 결과의 예시입니다.",
            value=[
                {
                    "id": 1,
                    "name": "유기농 사과",
                    "price": "10000.00",
                    "user": "user1",
                    "stock": 100,
                    "average_rating": 4.5,
                },
                {
                    "id": 2,
                    "name": "제주 감귤",
                    "price": "5000.00",
                    "user": "user2",
                    "stock": 500,
                    "average_rating": 4.8,
                },
            ],
            response_only=True,
            status_codes=["200"],
        ),
        OpenApiExample(
            "검색 결과 예시",
            summary="검색 결과 예시",
            description="'사과'로 검색한 결과의 예시입니다.",
            value=[
                {
                    "id": 1,
                    "name": "유기농 사과",
                    "price": "10000.00",
                    "user": "user1",
                    "stock": 100,
                    "average_rating": 4.5,
                },
                {
                    "id": 3,
                    "name": "청송 사과",
                    "price": "8000.00",
                    "user": "user3",
                    "stock": 200,
                    "average_rating": 4.2,
                },
            ],
            response_only=True,
            status_codes=["200"],
        ),
    ],
)
class ProductListView(generics.ListAPIView):
    """
    상품 목록을 보여주는 view
    검색 기능 포함
    """

    queryset = Product.objects.annotate(average_rating=Avg("reviews__rating")).order_by(
        "-created_at"
    )
    serializer_class = ProductListSerializer
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "market/product_list.html"
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name", "user__username", "variety", "growing_region"]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get("search", None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(user__username__icontains=search_query)
                | Q(variety__icontains=search_query)
                | Q(growing_region__icontains=search_query)
            )
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if request.accepted_renderer.format == "html":
            context = {"products": self.paginate_queryset(queryset)}
            return Response(context, template_name=self.template_name)
        return super().list(request, *args, **kwargs)


@extend_schema(
    summary="상품 등록",
    description="새로운 상품을 등록합니다.",
    request=ProductSerializer,
    responses={201: ProductSerializer},
    examples=[
        OpenApiExample(
            "상품 등록 요청 예시",
            summary="상품 등록 요청 예시",
            description="새로운 상품을 등록하는 요청 예시입니다.",
            value={
                "name": "Product 5",
                "price": "15000",
                "description": "Product description",
                "stock": 100,
                "variety": "product variety",
                "growing_region": "Product region",
                "harvest_date": "2024-03-15",
            },
            request_only=True,
        ),
        OpenApiExample(
            "상품 등록 결과 예시",
            summary="상품 등록 응답 예시",
            description="성공적으로 상품이 등록되었을 때의 응답 예시입니다.",
            value={
                "id": 1,
                "user": 1,
                "name": "Product 5",
                "price": "15000",
                "description": "Product description",
                "stock": 100,
                "variety": "product variety",
                "growing_region": "Product region",
                "harvest_date": "2024-03-15",
                "created_at": "2024-10-03T15:00:00Z",
                "updated_at": "2024-10-03T15:00:00Z",
            },
            response_only=True,
        ),
    ],
)
class ProductCreateView(generics.CreateAPIView):
    """
    상품 등록 view
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "market/product_create.html"

    def get(self, request, *args, **kwargs):
        if request.accepted_renderer.format == "html":
            return Response({"serializer": self.get_serializer()})
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save(user=self.request.user)
            images = request.FILES.getlist("images")

            if len(images) > 5:
                return Response(
                    {"error": "최대 5장까지만 이미지를 업로드할 수 있습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for image in images:
                ProductImage.objects.create(product=product, image=image)

            if request.accepted_renderer.format == "html":
                success_url = reverse("product-detail", kwargs={"id": product.id})
                return HttpResponseRedirect(success_url)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.accepted_renderer.format == "html":
            return Response(
                {"serializer": serializer}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
@extend_schema(
    summary="상품 상세 정보 조회",
    description="특정 상품의 상세 정보를 반환합니다.",
    responses={200: ProductSerializer},
    examples=[
        OpenApiExample(
            "상품 상세 결과 예시",
            value=[
                {
                    "id": 1,
                    "name": "product 1",
                    "username": "user1",
                    "price": "10000.00",
                    "description": "product description",
                    "stock": 100,
                    "variety": "product variety",
                    "growing_region": "Seoul",
                    "harvest_date": "2024-10-01",
                    "created_at": "2024-10-01T16:13:47.931470+09:00",
                    "updated_at": "2024-10-01T16:28:46.019304+09:00",
                    "average_rating": 5,
                    "images": [
                        "your/project/dir/media/products/image1.jpg",
                        "your/project/dir/media/products/image2.jpg",
                    ],
                }
            ],
            response_only=True,
            status_codes=["200"],
        )
    ],
)
class ProductDetailView(generics.RetrieveAPIView):
    """
    상품 상세 view
    댓글 작성 함수도 포함되어있음
    """

    serializer_class = ProductSerializer
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "market/product_detail.html"
    lookup_field = "id"

    def get_queryset(self):
        return Product.objects.annotate(
            average_rating=Avg("reviews__rating")
        ).prefetch_related("images")

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        if request.accepted_renderer.format == "html":
            reviews = Review.objects.filter(product=instance)
            review_serializer = ReviewSerializer(reviews, many=True)
            return Response(
                {
                    "product": serializer.data,
                    "reviews": review_serializer.data,
                }
            )
        return Response(serializer.data)

    @extend_schema(
        summary="상품 리뷰 작성",
        description="특정 상품에 대한 리뷰를 작성합니다.",
        request=ReviewSerializer,
        responses={
            201: OpenApiExample(
                "Review created",
                value={
                    "status": "success",
                    "message": "Review created successfully",
                    "data": {
                        "id": 1,
                        "user": "user1",
                        "content": "This is a great product!",
                        "rating": 5,
                        "created_at": "2024-10-02T12:34:56Z",
                    },
                },
                response_only=True,
                status_codes=["201"],
            ),
        },
        examples=[
            OpenApiExample(
                "리뷰 작성 예시입니다",
                value={
                    "content": "This is a great product!",
                    "rating": 5,
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        """
        댓글 작성 기능
        """
        try:
            product = self.get_object()
            content = request.data.get("content")
            rating = request.data.get("rating")

            review = Review.objects.create(
                product=product, user=request.user, content=content, rating=rating
            )

            serializer = ReviewSerializer(review)
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Review created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


@extend_schema(
    summary="상품 정보 수정",
    description="특정 상품의 정보를 수정합니다.",
    request=ProductSerializer,
    responses={200: ProductSerializer},
    examples=[
        OpenApiExample(
            "Valid input example",
            summary="상품 수정 요청 예시",
            description="상품 이름과 가격을 수정하는 요청 예시입니다.",
            value={
                "name": "업데이트된 상품 이름",
                "price": 15000,
                "description": "이 상품에 대한 새로운 설명입니다.",
            },
            request_only=True,
        ),
        OpenApiExample(
            "Valid output example",
            summary="상품 수정 응답 예시",
            description="성공적으로 상품이 수정되었을 때의 응답 예시입니다.",
            value={
                "id": 1,
                "name": "업데이트된 상품 이름",
                "price": 15000,
                "description": "이 상품에 대한 새로운 설명입니다.",
                "created_at": "2024-10-03T12:00:00Z",
                "updated_at": "2024-10-03T14:30:00Z",
            },
            response_only=True,
        ),
    ],
)
class ProductUpdateView(generics.UpdateAPIView):
    """
    상품 내용 수정 view
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "id"
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "market/product_update.html"
    http_method_names = ["get", "post", "patch"]

    def get(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = self.get_serializer(product)
        if request.accepted_renderer.format == "html":
            return Response({"serializer": serializer, "product": product})
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):
        product = serializer.save()

        images_to_delete = self.request.data.getlist("images_to_delete", [])

        for full_image_url in images_to_delete:
            try:
                parsed_url = urlparse(full_image_url)
                relative_path = parsed_url.path
                if relative_path.startswith(settings.MEDIA_URL):
                    relative_path = relative_path[len(settings.MEDIA_URL) :]

                image = ProductImage.objects.get(image=relative_path, product=product)

                if default_storage.exists(relative_path):
                    default_storage.delete(relative_path)
                    print(f"Deleted file: {relative_path}")
                else:
                    print(f"File not found in storage: {relative_path}")

                image.delete()
                print(f"Deleted image record for URL: {full_image_url}")
            except ProductImage.DoesNotExist:
                print(f"Image record not found for path: {relative_path}")
            except Exception as e:
                print(f"Error deleting image with URL {full_image_url}: {str(e)}")

        new_images = self.request.FILES.getlist("image")
        for image in new_images:
            ProductImage.objects.create(product=product, image=image)

        return product

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


@extend_schema(
    summary="상품 삭제",
    description="특정 상품을 삭제합니다.",
    responses={204: "삭제가 완료되었습니다"},
)
class ProductDeleteView(generics.DestroyAPIView):
    """
    상품 삭제 view
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "id"
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "market/product_delete.html"

    def get(self, request, *args, **kwargs):
        product = self.get_object()
        if request.accepted_renderer.format == "html":
            return Response({"product": product})
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def post(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class IsReviewOwner(permissions.BasePermission):
    """
    댓글 주인확인
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


@extend_schema(
    summary="리뷰 삭제",
    description="특정 리뷰를 삭제합니다.",
    responses={204: "삭제가 완료되었습니다"},
)
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
                {"status": "success", "message": "Review deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

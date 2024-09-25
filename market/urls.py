from django.urls import path
from . import views

urlpatterns = [
    # Product URLs
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/create/", views.ProductCreateView.as_view(), name="product-create"),
    path(
        "products/<int:id>/", views.ProductDetailView.as_view(), name="product-detail"
    ),
    path(
        "products/<int:id>/update/",
        views.ProductUpdateView.as_view(),
        name="product-update",
    ),
    path(
        "products/<int:id>/delete/",
        views.ProductDeleteView.as_view(),
        name="product-delete",
    ),
    path(
        "products/<int:product_id>/upload-image/",
        views.ProductImageUploadView.as_view(),
        name="product-image-upload",
    ),
    # Review URLs
    path("reviews/", views.ReviewListView.as_view(), name="review-list"),
    path("reviews/<int:pk>/", views.ReviewDetailView.as_view(), name="review-detail"),
]

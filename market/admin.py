from django.contrib import admin
from .models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "user", "stock", "created_at", "updated_at")
    list_filter = ("user", "created_at", "updated_at")
    search_fields = ("name", "description", "user__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ProductImageInline]

    fieldsets = (
        (None, {"fields": ("user", "name", "price", "description", "stock")}),
        (
            "추가 정보",
            {
                "fields": ("variety", "growing_region", "harvest_date"),
                "classes": ("collapse",),
            },
        ),
        (
            "시간 정보",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "image", "created_at")
    list_filter = ("created_at",)
    search_fields = ("product__name",)

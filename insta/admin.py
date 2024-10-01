from django.contrib import admin
from .models import Post, PostImage, Comment, Like


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("user", "content", "location", "created_at", "updated_at")
    search_fields = ("user__username", "content", "location")
    list_filter = ("created_at",)


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ("post", "image")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "content", "created_at")
    search_fields = ("user__username", "post__content", "content")
    list_filter = ("created_at",)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")

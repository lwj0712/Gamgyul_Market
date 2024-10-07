from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import (
    PostListView,
    PostDetailView,
    PostCreateView,
    PostDeleteView,
    CommentListView,
    CommentDetailView,
    LikeView,
)

app_name = "insta"

urlpatterns = [
    path("posts/", PostListView.as_view(), name="insta_post_list"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="insta_post_detail"),
    path("posts/create/", PostCreateView.as_view(), name="insta_post_create"),
    path("posts/<int:pk>/delete/", PostDeleteView.as_view(), name="insta_post_delete"),
    path(
        "posts/<int:post_id>/comments/",
        CommentListView.as_view(),
        name="insta_comment_list",
    ),
    path(
        "comments/<int:pk>/", CommentDetailView.as_view(), name="insta_comment_detail"
    ),
    path("posts/<int:post_id>/like/", LikeView.as_view(), name="insta_like"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

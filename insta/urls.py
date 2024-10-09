from django.urls import path
from . import views

app_name = "insta"

urlpatterns = [
    path("posts/", views.PostListView.as_view(), name="insta_post_list"),
    path("posts/<int:pk>/", views.PostDetailView.as_view(), name="insta_post_detail"),
    path("posts/create/", views.PostCreateView.as_view(), name="insta_post_create"),
    path(
        "posts/<int:pk>/delete/",
        views.PostDeleteView.as_view(),
        name="insta_post_delete",
    ),
    path(
        "posts/<int:post_id>/comments/",
        views.CommentListCreateView.as_view(),
        name="insta_comment_list_create",
    ),
    path(
        "comments/<int:pk>/",
        views.CommentDetailView.as_view(),
        name="insta_comment_detail",
    ),
    path("posts/<int:post_id>/like/", views.LikeView.as_view(), name="insta_like"),
    path("posts/search/", views.TagPostListView.as_view(), name="insta_tag_post_list"),
]

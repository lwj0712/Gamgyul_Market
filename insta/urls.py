from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import (
    PostList,
    PostDetail,
    PostCreate,
    PostDelete,
    CommentList,
    CommentDetail,
    CommentDelete,
)

app_name = "insta"

urlpatterns = [
    path("posts/", PostList.as_view(), name="post-list"),
    path("posts/<int:pk>/", PostDetail.as_view(), name="post-detail"),
    path("posts/create/", PostCreate.as_view(), name="post-create"),
    path("posts/<int:pk>/delete/", PostDelete.as_view(), name="post-delete"),
    path("posts/<int:post_id>/comments/", CommentList.as_view(), name="comment-list"),
    path("comments/<int:pk>/", CommentDetail.as_view(), name="comment-detail"),
    path("comments/<int:pk>/delete", CommentDelete.as_view(), name="comment-delete"),
]

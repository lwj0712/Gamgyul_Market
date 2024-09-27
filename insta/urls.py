from django.urls import path
from .views import PostList, PostDetail, CommentList, CommentDetail

app_name = "insta"

urlpatterns = [
    path("posts/", PostList.as_view(), name="post-list"),
    path("posts/<int:pk>/", PostDetail.as_view(), name="post-detail"),
    path("posts/<int:post_id>/comments/", CommentList.as_view(), name="comment-list"),
    path("comments/<int:pk>/", CommentDetail.as_view(), name="comment-detail"),
]

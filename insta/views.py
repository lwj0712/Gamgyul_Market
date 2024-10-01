from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Post, Comment, Like, PostImage
from .serializers import (
    PostSerializer,
    CommentSerializer,
    LikeSerializer,
    PostImageSerializer,
)


class PostList(generics.ListCreateAPIView):
    queryset = Post.objects.all().order_by("-created_at")
    serializer_class = PostSerializer
    permission_classes = []


class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = []


class CommentList(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = []

    def get_queryset(self):
        post_id = self.kwargs["post_id"]
        return Comment.objects.filter(post_id=post_id).order_by("-created_at")


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]


class LikeList(generics.ListCreateAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]


class LikeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]


class PostImageList(generics.ListCreateAPIView):
    serializer_class = PostImageSerializer
    permission_classes = []

    def get_queryset(self):
        post_id = self.kwargs["post_id"]
        return PostImage.objects.filter(post_id=post_id)


class PostImageDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PostImage.objects.all()
    serializer_class = PostImageSerializer
    permission_classes = []

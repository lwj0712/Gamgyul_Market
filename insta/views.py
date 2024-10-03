from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
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
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "insta/post_list.html"

    def get(self, request, *args, **kwargs):
        posts = self.get_queryset()
        return Response({"posts": posts})

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_serializer(self, *args, **kwargs):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return self.serializer_class(*args, context=context, **kwargs)


class PostCreate(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return render(request, "insta/post_create.html")

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            post = serializer.save(user=self.request.user)

            tags = request.data.get("tags")
            if tags:
                tag_list = [tag.strip() for tag in tags.split(",")]
                post.tags.add(*tag_list)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()


class PostDelete(generics.DestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("글 작성자만 삭제할 수 있습니다.")
        instance.delete()


class CommentList(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs["post_id"]
        return Comment.objects.filter(post_id=post_id).order_by("-created_at")


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]


class CommentDelete(generics.DestroyAPIView):
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("댓글 작성자만 삭제할 수 있습니다.")
        instance.delete()


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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs["post_id"]
        return PostImage.objects.filter(post_id=post_id)

    def perform_create(self, serializer):
        post_id = self.kwargs["post_id"]
        post_images_count = PostImage.objects.filter(post_id=post_id).count()

        if post_images_count > 10:
            raise ValidationError("이미지는 10장까지 첨부할 수 있습니다.")

        serializer.save(post_id=post_id)


class PostImageDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PostImage.objects.all()
    serializer_class = PostImageSerializer
    permission_classes = [IsAuthenticated]

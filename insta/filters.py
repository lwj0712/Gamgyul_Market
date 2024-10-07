from django_filters import rest_framework as filters
from .models import Post


class PostFilter(filters.FilterSet):
    tags = filters.CharFilter(field_name="tags__name", lookup_expr="icontains")

    class Meta:
        model = Post
        fields = ["tags"]

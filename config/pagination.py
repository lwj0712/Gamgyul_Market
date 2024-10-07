from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination


class LimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 50


class PageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

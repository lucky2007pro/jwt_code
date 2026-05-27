from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Standart pagination — 20 ta elementdan"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class SmallPagination(PageNumberPagination):
    """Kichik pagination — 10 ta elementdan"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class LargePagination(PageNumberPagination):
    """Katta pagination — 50 ta elementdan"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

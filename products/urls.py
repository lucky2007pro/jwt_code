from django.urls import path
from .views import (
    CategoryListView, CategoryDetailView, CategoryCreateView,
    BrandListView, BrandDetailView,
    ProductListView, ProductDetailView,
    ProductCreateView, ProductUpdateView, ProductDeleteView,
    ProductImageAddView, ProductImageDeleteView,
)

urlpatterns = [
    # Kategoriyalar
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/create/', CategoryCreateView.as_view(), name='category-create'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),

    # Brendlar
    path('brands/', BrandListView.as_view(), name='brand-list'),
    path('brands/<slug:slug>/', BrandDetailView.as_view(), name='brand-detail'),

    # Mahsulotlar
    path('', ProductListView.as_view(), name='product-list'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('<uuid:pk>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('<uuid:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),

    # Mahsulot rasmlari
    path('<uuid:pk>/images/add/', ProductImageAddView.as_view(), name='product-image-add'),
    path('<uuid:pk>/images/<uuid:image_id>/delete/', ProductImageDeleteView.as_view(), name='product-image-delete'),
]

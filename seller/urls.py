from django.urls import path
from .views import (
    SellerRegisterView, SellerProfileView,
    SellerDashboardView, SellerProductsView,
    SellerPublicView,
)

urlpatterns = [
    path('register/', SellerRegisterView.as_view(), name='seller-register'),
    path('profile/', SellerProfileView.as_view(), name='seller-profile'),
    path('dashboard/', SellerDashboardView.as_view(), name='seller-dashboard'),
    path('products/', SellerProductsView.as_view(), name='seller-products'),
    path('<slug:slug>/', SellerPublicView.as_view(), name='seller-public'),
]

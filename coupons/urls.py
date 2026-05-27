from django.urls import path
from .views import (
    CouponValidateView,
    SellerCouponListCreateView, SellerCouponDetailView,
)

urlpatterns = [
    path('validate/', CouponValidateView.as_view(), name='coupon-validate'),
    path('seller/', SellerCouponListCreateView.as_view(), name='seller-coupon-list'),
    path('seller/<uuid:pk>/', SellerCouponDetailView.as_view(), name='seller-coupon-detail'),
]

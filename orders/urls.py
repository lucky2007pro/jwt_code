from django.urls import path
from .views import (
    ShippingAddressListCreateView, ShippingAddressDetailView,
    CheckoutView, OrderListView, OrderDetailView,
    OrderCancelView, OrderStatusUpdateView, SellerOrdersView,
)

urlpatterns = [
    # Manzillar
    path('addresses/', ShippingAddressListCreateView.as_view(), name='address-list-create'),
    path('addresses/<uuid:pk>/', ShippingAddressDetailView.as_view(), name='address-detail'),

    # Buyurtmalar
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('', OrderListView.as_view(), name='order-list'),
    path('<str:order_number>/', OrderDetailView.as_view(), name='order-detail'),
    path('<str:order_number>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('<str:order_number>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),

    # Seller buyurtmalari
    path('seller/list/', SellerOrdersView.as_view(), name='seller-orders'),
]

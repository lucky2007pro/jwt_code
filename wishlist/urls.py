from django.urls import path
from .views import WishlistView, WishlistToggleView, WishlistRemoveView

urlpatterns = [
    path('', WishlistView.as_view(), name='wishlist'),
    path('toggle/', WishlistToggleView.as_view(), name='wishlist-toggle'),
    path('remove/<uuid:product_id>/', WishlistRemoveView.as_view(), name='wishlist-remove'),
]

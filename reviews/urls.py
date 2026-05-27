from django.urls import path
from .views import (
    ProductReviewsView, ReviewCreateView,
    ReviewUpdateView, ReviewDeleteView,
    ReviewReplyView, MyReviewsView,
)

urlpatterns = [
    path('product/<uuid:product_id>/', ProductReviewsView.as_view(), name='product-reviews'),
    path('create/', ReviewCreateView.as_view(), name='review-create'),
    path('<uuid:pk>/update/', ReviewUpdateView.as_view(), name='review-update'),
    path('<uuid:pk>/delete/', ReviewDeleteView.as_view(), name='review-delete'),
    path('<uuid:pk>/reply/', ReviewReplyView.as_view(), name='review-reply'),
    path('my/', MyReviewsView.as_view(), name='my-reviews'),
]

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count
from .models import Review, ReviewReply
from .serializers import (
    ReviewSerializer, ReviewCreateSerializer,
    ReviewUpdateSerializer, ReviewReplyCreateSerializer,
)
from products.models import Product
from products.permissions import IsSeller


class ProductReviewsView(APIView):
    """Mahsulot sharhlari ro'yxati"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, is_active=True)
        reviews = Review.objects.filter(
            product=product, is_approved=True
        ).select_related('user').prefetch_related('images', 'replies__user')

        # Statistika
        stats = reviews.aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id'),
        )

        # Rating taqsimoti
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[str(i)] = reviews.filter(rating=i).count()

        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response({
            'success': True,
            'message': f"'{product.name}' mahsuloti sharhlari.",
            'data': {
                'reviews': serializer.data,
                'stats': {
                    'average_rating': round(stats['avg_rating'], 1) if stats['avg_rating'] else 0,
                    'total_reviews': stats['total_reviews'],
                    'rating_distribution': rating_distribution,
                }
            }
        }, status=status.HTTP_200_OK)


class ReviewCreateView(APIView):
    """Sharh qoldirish"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ReviewCreateSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response({
            'success': True,
            'message': "Sharh muvaffaqiyatli qoldirildi.",
            'data': ReviewSerializer(review, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class ReviewUpdateView(APIView):
    """O'z sharhini tahrirlash"""
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        review = get_object_or_404(Review, pk=pk, user=request.user)
        serializer = ReviewUpdateSerializer(instance=review, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Sharh muvaffaqiyatli yangilandi.",
            'data': ReviewSerializer(review, context={'request': request}).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        review = get_object_or_404(Review, pk=pk, user=request.user)
        serializer = ReviewUpdateSerializer(
            instance=review, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Sharh muvaffaqiyatli yangilandi.",
            'data': ReviewSerializer(review, context={'request': request}).data,
        }, status=status.HTTP_200_OK)


class ReviewDeleteView(APIView):
    """O'z sharhini o'chirish"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        review = get_object_or_404(Review, pk=pk, user=request.user)
        review.delete()
        return Response({
            'success': True,
            'message': "Sharh muvaffaqiyatli o'chirildi.",
        }, status=status.HTTP_200_OK)


class ReviewReplyView(APIView):
    """Seller yoki admin sharh ga javob berish"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)

        # Tekshirish: seller faqat o'z mahsulotiga javob bera oladi
        if review.product.seller != request.user:
            return Response({
                'success': False,
                'message': "Siz faqat o'z mahsulotingiz sharhlariga javob bera olasiz.",
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ReviewReplyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reply = ReviewReply.objects.create(
            review=review,
            user=request.user,
            text=serializer.validated_data['text'],
        )

        return Response({
            'success': True,
            'message': "Javob muvaffaqiyatli qoldirildi.",
            'data': ReviewSerializer(review, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class MyReviewsView(APIView):
    """Mening sharhlarim"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        reviews = Review.objects.filter(
            user=request.user
        ).select_related('product', 'user').prefetch_related('images', 'replies__user')

        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response({
            'success': True,
            'message': "Mening sharhlarim.",
            'data': serializer.data,
            'count': len(serializer.data),
        }, status=status.HTTP_200_OK)

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import WishlistItem
from .serializers import WishlistItemSerializer, WishlistToggleSerializer
from products.models import Product


class WishlistView(APIView):
    """Sevimlilar ro'yxati"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wishlist = WishlistItem.objects.filter(
            user=request.user
        ).select_related('product__category', 'product__brand', 'product__seller')

        serializer = WishlistItemSerializer(
            wishlist, many=True, context={'request': request}
        )
        return Response({
            'success': True,
            'message': "Sevimlilar ro'yxati.",
            'data': serializer.data,
            'count': len(serializer.data),
        }, status=status.HTTP_200_OK)


class WishlistToggleView(APIView):
    """Sevimlilar ga qo'shish/olib tashlash (toggle)"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = WishlistToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = Product.objects.get(id=serializer.validated_data['product_id'])

        wishlist_item, created = WishlistItem.objects.get_or_create(
            user=request.user, product=product
        )

        if not created:
            # Allaqachon mavjud — olib tashlash
            wishlist_item.delete()
            return Response({
                'success': True,
                'message': f"'{product.name}' sevimlilardan olib tashlandi.",
                'data': {'is_wishlisted': False},
            }, status=status.HTTP_200_OK)

        return Response({
            'success': True,
            'message': f"'{product.name}' sevimlilarga qo'shildi.",
            'data': {'is_wishlisted': True},
        }, status=status.HTTP_201_CREATED)


class WishlistRemoveView(APIView):
    """Sevimlilardan aniq mahsulotni olib tashlash"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, product_id):
        wishlist_item = get_object_or_404(
            WishlistItem, user=request.user, product_id=product_id
        )
        product_name = wishlist_item.product.name
        wishlist_item.delete()
        return Response({
            'success': True,
            'message': f"'{product_name}' sevimlilardan olib tashlandi.",
        }, status=status.HTTP_200_OK)

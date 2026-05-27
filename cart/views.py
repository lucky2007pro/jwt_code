from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import (
    CartSerializer, CartItemAddSerializer, CartItemUpdateSerializer,
)
from products.models import Product


class CartView(APIView):
    """Foydalanuvchi savatchasini ko'rish"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(
            user=request.user, is_active=True
        )
        serializer = CartSerializer(cart, context={'request': request})
        return Response({
            'success': True,
            'message': "Savatcha.",
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class CartItemAddView(APIView):
    """Savatchaga mahsulot qo'shish"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CartItemAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart, created = Cart.objects.get_or_create(
            user=request.user, is_active=True
        )
        product = Product.objects.get(id=serializer.validated_data['product_id'])
        quantity = serializer.validated_data.get('quantity', 1)

        # Agar mahsulot allaqachon savatchada bo'lsa, sonini oshirish
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={'quantity': quantity}
        )
        if not item_created:
            cart_item.quantity += quantity
            if cart_item.quantity > product.stock:
                return Response({
                    'success': False,
                    'message': f"Omborda faqat {product.stock} ta mahsulot mavjud.",
                }, status=status.HTTP_400_BAD_REQUEST)
            cart_item.save(update_fields=['quantity'])

        cart_data = CartSerializer(cart, context={'request': request}).data
        return Response({
            'success': True,
            'message': f"'{product.name}' savatchaga qo'shildi.",
            'data': cart_data,
        }, status=status.HTTP_201_CREATED if item_created else status.HTTP_200_OK)


class CartItemUpdateView(APIView):
    """Savatcha mahsuloti sonini o'zgartirish"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, item_id):
        cart = get_object_or_404(Cart, user=request.user, is_active=True)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data['quantity']
        if quantity > cart_item.product.stock:
            return Response({
                'success': False,
                'message': f"Omborda faqat {cart_item.product.stock} ta mahsulot mavjud.",
            }, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save(update_fields=['quantity'])

        cart_data = CartSerializer(cart, context={'request': request}).data
        return Response({
            'success': True,
            'message': "Mahsulot soni yangilandi.",
            'data': cart_data,
        }, status=status.HTTP_200_OK)


class CartItemRemoveView(APIView):
    """Savatchadan mahsulotni olib tashlash"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, item_id):
        cart = get_object_or_404(Cart, user=request.user, is_active=True)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        product_name = cart_item.product.name
        cart_item.delete()

        cart_data = CartSerializer(cart, context={'request': request}).data
        return Response({
            'success': True,
            'message': f"'{product_name}' savatchadan olib tashlandi.",
            'data': cart_data,
        }, status=status.HTTP_200_OK)


class CartClearView(APIView):
    """Savatchani to'liq tozalash"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        cart = get_object_or_404(Cart, user=request.user, is_active=True)
        cart.items.all().delete()
        return Response({
            'success': True,
            'message': "Savatcha tozalandi.",
        }, status=status.HTTP_200_OK)

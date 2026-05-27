from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import (
    ShippingAddress, Order, OrderItem, OrderStatusHistory,
    PENDING, CANCELLED, DELIVERED,
)
from .serializers import (
    ShippingAddressSerializer, ShippingAddressCreateSerializer,
    OrderSerializer, OrderListSerializer,
    CheckoutSerializer, OrderStatusUpdateSerializer,
)
from cart.models import Cart
from products.permissions import IsSeller, IsAdminUser


# ==================== SHIPPING ADDRESS VIEWS ====================

class ShippingAddressListCreateView(APIView):
    """Yetkazish manzillari ro'yxati va yangi qo'shish"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        addresses = ShippingAddress.objects.filter(user=request.user)
        serializer = ShippingAddressSerializer(addresses, many=True)
        return Response({
            'success': True,
            'message': "Yetkazish manzillari.",
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ShippingAddressCreateSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        address = serializer.save()
        return Response({
            'success': True,
            'message': "Yetkazish manzili muvaffaqiyatli qo'shildi.",
            'data': ShippingAddressSerializer(address).data,
        }, status=status.HTTP_201_CREATED)


class ShippingAddressDetailView(APIView):
    """Yetkazish manzilini ko'rish/tahrirlash/o'chirish"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        address = get_object_or_404(ShippingAddress, pk=pk, user=request.user)
        return Response({
            'success': True,
            'data': ShippingAddressSerializer(address).data,
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        address = get_object_or_404(ShippingAddress, pk=pk, user=request.user)
        serializer = ShippingAddressCreateSerializer(
            instance=address, data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Manzil muvaffaqiyatli yangilandi.",
            'data': ShippingAddressSerializer(address).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        address = get_object_or_404(ShippingAddress, pk=pk, user=request.user)
        serializer = ShippingAddressCreateSerializer(
            instance=address, data=request.data,
            partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Manzil muvaffaqiyatli yangilandi.",
            'data': ShippingAddressSerializer(address).data,
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        address = get_object_or_404(ShippingAddress, pk=pk, user=request.user)
        address.delete()
        return Response({
            'success': True,
            'message': "Manzil muvaffaqiyatli o'chirildi.",
        }, status=status.HTTP_200_OK)


# ==================== ORDER VIEWS ====================

class CheckoutView(APIView):
    """Savatchadan buyurtma yaratish"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CheckoutSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        cart = Cart.objects.filter(user=user, is_active=True).first()

        if not cart or not cart.items.exists():
            return Response({
                'success': False,
                'message': "Savatcha bo'sh. Avval mahsulot qo'shing.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Manzilni olish
        shipping_address = ShippingAddress.objects.get(
            id=serializer.validated_data['shipping_address_id']
        )

        # Subtotal hisoblash
        subtotal = sum(
            item.product.final_price * item.quantity
            for item in cart.items.select_related('product').all()
        )

        # Buyurtma yaratish
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            payment_method=serializer.validated_data['payment_method'],
            note=serializer.validated_data.get('note', ''),
            subtotal=subtotal,
            total=subtotal,  # Hozircha chegirmasiz
        )

        # Buyurtma mahsulotlarini yaratish
        for cart_item in cart.items.select_related('product').all():
            product = cart_item.product

            # Stock tekshirish
            if product.stock < cart_item.quantity:
                # Tranzaktsiyani bekor qilish
                raise Exception(
                    f"'{product.name}' omborda yetarli emas. Mavjud: {product.stock}"
                )

            OrderItem.objects.create(
                order=order,
                product=product,
                seller=product.seller,
                product_name=product.name,
                product_price=product.final_price,
                quantity=cart_item.quantity,
                total=product.final_price * cart_item.quantity,
            )

            # Stockdan kamaytirish
            product.stock -= cart_item.quantity
            product.save(update_fields=['stock'])

        # Status tarixi
        OrderStatusHistory.objects.create(
            order=order,
            old_status='',
            new_status=PENDING,
            changed_by=user,
            note="Buyurtma yaratildi.",
        )

        # Savatchani tozalash
        cart.items.all().delete()
        cart.is_active = False
        cart.save(update_fields=['is_active'])

        return Response({
            'success': True,
            'message': f"Buyurtma muvaffaqiyatli yaratildi. Buyurtma raqami: {order.order_number}",
            'data': OrderSerializer(order, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    """Mening buyurtmalarim"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related('items')

        # Filter by status
        order_status = request.query_params.get('status')
        if order_status:
            orders = orders.filter(status=order_status)

        serializer = OrderListSerializer(orders, many=True)
        return Response({
            'success': True,
            'message': "Mening buyurtmalarim.",
            'data': serializer.data,
            'count': len(serializer.data),
        }, status=status.HTTP_200_OK)


class OrderDetailView(APIView):
    """Buyurtma batafsil ko'rish"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_number):
        order = get_object_or_404(
            Order.objects.prefetch_related(
                'items__product', 'status_history__changed_by'
            ),
            order_number=order_number, user=request.user
        )
        serializer = OrderSerializer(order, context={'request': request})
        return Response({
            'success': True,
            'message': "Buyurtma tafsilotlari.",
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class OrderCancelView(APIView):
    """Buyurtmani bekor qilish (faqat PENDING holatda)"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_number):
        order = get_object_or_404(
            Order, order_number=order_number, user=request.user
        )

        if order.status != PENDING:
            return Response({
                'success': False,
                'message': "Faqat 'Kutilmoqda' holatidagi buyurtmalarni bekor qilish mumkin.",
            }, status=status.HTTP_400_BAD_REQUEST)

        old_status = order.status
        order.status = CANCELLED
        order.save(update_fields=['status'])

        # Stockni qaytarish
        for item in order.items.select_related('product').all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save(update_fields=['stock'])

        # Status tarixi
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=CANCELLED,
            changed_by=request.user,
            note="Buyurtmachi tomonidan bekor qilindi.",
        )

        return Response({
            'success': True,
            'message': "Buyurtma muvaffaqiyatli bekor qilindi.",
        }, status=status.HTTP_200_OK)


class OrderStatusUpdateView(APIView):
    """Seller/Admin: Buyurtma holatini o'zgartirish"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    @transaction.atomic
    def patch(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)

        # Seller faqat o'z mahsulotlari bor buyurtmalarni o'zgartira oladi
        seller_items = order.items.filter(seller=request.user)
        if not seller_items.exists() and request.user.user_role != 'admin':
            return Response({
                'success': False,
                'message': "Bu buyurtmani o'zgartirish huquqi yo'q.",
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_status = order.status
        new_status = serializer.validated_data['status']

        order.status = new_status
        if new_status == DELIVERED:
            order.is_paid = True
        order.save(update_fields=['status', 'is_paid'])

        # Status tarixi
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            note=serializer.validated_data.get('note', ''),
        )

        return Response({
            'success': True,
            'message': f"Buyurtma holati '{new_status}' ga o'zgartirildi.",
            'data': OrderSerializer(order, context={'request': request}).data,
        }, status=status.HTTP_200_OK)


class SellerOrdersView(APIView):
    """Seller: O'z buyurtmalari ro'yxati"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def get(self, request):
        # Seller mahsulotlari bor buyurtmalar
        order_ids = OrderItem.objects.filter(
            seller=request.user
        ).values_list('order_id', flat=True).distinct()

        orders = Order.objects.filter(
            id__in=order_ids
        ).prefetch_related('items')

        order_status = request.query_params.get('status')
        if order_status:
            orders = orders.filter(status=order_status)

        serializer = OrderListSerializer(orders, many=True)
        return Response({
            'success': True,
            'message': "Seller buyurtmalari.",
            'data': serializer.data,
            'count': len(serializer.data),
        }, status=status.HTTP_200_OK)

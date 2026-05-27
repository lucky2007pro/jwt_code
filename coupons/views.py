from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import Coupon, CouponUsage
from .serializers import (
    CouponSerializer, CouponCreateSerializer,
    CouponValidateSerializer, CouponApplySerializer,
)
from products.permissions import IsSeller


class CouponValidateView(APIView):
    """Kupon haqiqiyligini tekshirish"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code'].upper().strip()
        order_total = serializer.validated_data.get('order_total', 0)

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({
                'success': False,
                'message': "Kupon topilmadi.",
            }, status=status.HTTP_404_NOT_FOUND)

        if not coupon.is_valid:
            return Response({
                'success': False,
                'message': "Kupon muddati o'tgan yoki faol emas.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Per user limit tekshirish
        user_usage_count = CouponUsage.objects.filter(
            coupon=coupon, user=request.user
        ).count()
        if user_usage_count >= coupon.per_user_limit:
            return Response({
                'success': False,
                'message': "Siz bu kupondan maksimal foydalangansiz.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Minimal summa tekshirish
        if order_total > 0 and order_total < coupon.min_order_amount:
            return Response({
                'success': False,
                'message': f"Minimal buyurtma summasi: {coupon.min_order_amount} so'm.",
            }, status=status.HTTP_400_BAD_REQUEST)

        discount = coupon.calculate_discount(order_total) if order_total > 0 else 0

        return Response({
            'success': True,
            'message': "Kupon haqiqiy.",
            'data': {
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_value': str(coupon.discount_value),
                'discount_amount': str(discount),
                'min_order_amount': str(coupon.min_order_amount),
            }
        }, status=status.HTTP_200_OK)


# ==================== SELLER COUPON VIEWS ====================

class SellerCouponListCreateView(APIView):
    """Seller: O'z kuponlarini ko'rish va yaratish"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def get(self, request):
        coupons = Coupon.objects.filter(seller=request.user)
        serializer = CouponSerializer(coupons, many=True)
        return Response({
            'success': True,
            'message': "Kuponlar ro'yxati.",
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CouponCreateSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        coupon = serializer.save()
        return Response({
            'success': True,
            'message': "Kupon muvaffaqiyatli yaratildi.",
            'data': CouponSerializer(coupon).data,
        }, status=status.HTTP_201_CREATED)


class SellerCouponDetailView(APIView):
    """Seller: Kuponni tahrirlash/o'chirish"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def put(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk, seller=request.user)
        serializer = CouponCreateSerializer(
            instance=coupon, data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Kupon muvaffaqiyatli yangilandi.",
            'data': CouponSerializer(coupon).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk, seller=request.user)
        serializer = CouponCreateSerializer(
            instance=coupon, data=request.data,
            partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Kupon muvaffaqiyatli yangilandi.",
            'data': CouponSerializer(coupon).data,
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk, seller=request.user)
        coupon.delete()
        return Response({
            'success': True,
            'message': "Kupon muvaffaqiyatli o'chirildi.",
        }, status=status.HTTP_200_OK)

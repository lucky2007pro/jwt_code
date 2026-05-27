from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q
from .models import SellerProfile
from .serializers import (
    SellerRegisterSerializer, SellerProfileSerializer,
    SellerProfileUpdateSerializer, SellerDashboardSerializer,
    SellerPublicSerializer,
)
from products.models import Product
from products.serializers import ProductListSerializer
from products.permissions import IsSeller


class SellerRegisterView(APIView):
    """Foydalanuvchini seller sifatida ro'yxatdan o'tkazish"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SellerRegisterSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        seller_profile = serializer.save()
        return Response({
            'success': True,
            'message': "Sotuvchi profili muvaffaqiyatli yaratildi.",
            'data': SellerProfileSerializer(seller_profile, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class SellerProfileView(APIView):
    """Seller o'z profilini ko'rish va yangilash"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def get(self, request):
        seller_profile = get_object_or_404(SellerProfile, user=request.user)
        serializer = SellerProfileSerializer(seller_profile, context={'request': request})
        return Response({
            'success': True,
            'message': "Sotuvchi profili.",
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def put(self, request):
        seller_profile = get_object_or_404(SellerProfile, user=request.user)
        serializer = SellerProfileUpdateSerializer(
            instance=seller_profile, data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Sotuvchi profili muvaffaqiyatli yangilandi.",
            'data': SellerProfileSerializer(seller_profile, context={'request': request}).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        seller_profile = get_object_or_404(SellerProfile, user=request.user)
        serializer = SellerProfileUpdateSerializer(
            instance=seller_profile, data=request.data,
            partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Sotuvchi profili muvaffaqiyatli yangilandi.",
            'data': SellerProfileSerializer(seller_profile, context={'request': request}).data,
        }, status=status.HTTP_200_OK)


class SellerDashboardView(APIView):
    """Seller dashboard — statistikalar"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def get(self, request):
        user = request.user
        products = Product.objects.filter(seller=user)

        total_products = products.count()
        active_products = products.filter(is_active=True).count()
        out_of_stock_products = products.filter(is_active=True, stock=0).count()
        total_views = products.aggregate(total=Sum('views_count'))['total'] or 0

        # Orders statistikasi — hozircha 0 (orders app qo'shilganda yangilanadi)
        total_orders = 0
        pending_orders = 0
        total_revenue = 0

        # Seller rating
        seller_profile = getattr(user, 'seller_profile', None)
        shop_rating = seller_profile.rating if seller_profile else 0

        dashboard_data = {
            'total_products': total_products,
            'active_products': active_products,
            'out_of_stock_products': out_of_stock_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_revenue': total_revenue,
            'total_views': total_views,
            'shop_rating': shop_rating,
        }

        serializer = SellerDashboardSerializer(dashboard_data)
        return Response({
            'success': True,
            'message': "Sotuvchi dashboard statistikasi.",
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class SellerProductsView(APIView):
    """Seller o'z mahsulotlarini ko'rish"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def get(self, request):
        products = Product.objects.filter(
            seller=request.user
        ).select_related('category', 'brand', 'seller').prefetch_related('images')

        # Filter by status
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            products = products.filter(is_active=is_active.lower() == 'true')

        in_stock = request.query_params.get('in_stock')
        if in_stock is not None:
            if in_stock.lower() == 'true':
                products = products.filter(stock__gt=0)
            else:
                products = products.filter(stock=0)

        serializer = ProductListSerializer(
            products, many=True, context={'request': request}
        )
        return Response({
            'success': True,
            'message': "Seller mahsulotlari ro'yxati.",
            'data': serializer.data,
            'count': len(serializer.data),
        }, status=status.HTTP_200_OK)


class SellerPublicView(APIView):
    """Do'kon ommaviy sahifasi — har kim ko'ra oladi"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        seller_profile = get_object_or_404(
            SellerProfile, shop_slug=slug, is_verified=True
        )
        profile_data = SellerPublicSerializer(
            seller_profile, context={'request': request}
        ).data

        # Seller mahsulotlari
        products = Product.objects.filter(
            seller=seller_profile.user, is_active=True
        ).select_related('category', 'brand', 'seller').prefetch_related('images')

        products_data = ProductListSerializer(
            products, many=True, context={'request': request}
        ).data

        return Response({
            'success': True,
            'message': f"'{seller_profile.shop_name}' do'koni.",
            'data': {
                'shop': profile_data,
                'products': products_data,
                'products_count': len(products_data),
            }
        }, status=status.HTTP_200_OK)

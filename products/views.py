from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import Category, Brand, Product, ProductImage
from .serializers import (
    CategorySerializer, CategoryCreateSerializer,
    BrandSerializer, BrandCreateSerializer,
    ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, ProductImageSerializer,
)
from .permissions import IsSeller, IsProductOwner, IsAdminUser


# ==================== CATEGORY VIEWS ====================

class CategoryListView(APIView):
    """Barcha kategoriyalar ro'yxati (faqat parent=null bo'lganlar, children bilan)"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories = Category.objects.filter(
            is_active=True, parent__isnull=True
        ).prefetch_related('children')

        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response({
            'success': True,
            'message': "Kategoriyalar ro'yxati.",
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class CategoryDetailView(APIView):
    """Bitta kategoriya va uning mahsulotlari"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug, is_active=True)
        # Kategoriya ma'lumotlari
        category_data = CategorySerializer(category, context={'request': request}).data

        # Shu kategoriya va uning bolalaridagi mahsulotlar
        category_ids = [category.id]
        children = category.children.filter(is_active=True)
        category_ids.extend(children.values_list('id', flat=True))

        products = Product.objects.filter(
            category_id__in=category_ids, is_active=True
        ).select_related('category', 'brand', 'seller')

        products_data = ProductListSerializer(
            products, many=True, context={'request': request}
        ).data

        return Response({
            'success': True,
            'message': f"'{category.name}' kategoriyasi mahsulotlari.",
            'data': {
                'category': category_data,
                'products': products_data,
                'products_count': len(products_data),
            }
        }, status=status.HTTP_200_OK)


class CategoryCreateView(APIView):
    """Admin: Kategoriya yaratish"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = CategoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response({
            'success': True,
            'message': "Kategoriya muvaffaqiyatli yaratildi.",
            'data': CategorySerializer(category, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


# ==================== BRAND VIEWS ====================

class BrandListView(APIView):
    """Barcha brendlar ro'yxati"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        brands = Brand.objects.filter(is_active=True)
        serializer = BrandSerializer(brands, many=True, context={'request': request})
        return Response({
            'success': True,
            'message': "Brendlar ro'yxati.",
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class BrandDetailView(APIView):
    """Bitta brend va uning mahsulotlari"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        brand = get_object_or_404(Brand, slug=slug, is_active=True)
        brand_data = BrandSerializer(brand, context={'request': request}).data

        products = Product.objects.filter(
            brand=brand, is_active=True
        ).select_related('category', 'brand', 'seller')

        products_data = ProductListSerializer(
            products, many=True, context={'request': request}
        ).data

        return Response({
            'success': True,
            'message': f"'{brand.name}' brendi mahsulotlari.",
            'data': {
                'brand': brand_data,
                'products': products_data,
                'products_count': len(products_data),
            }
        }, status=status.HTTP_200_OK)


# ==================== PRODUCT VIEWS ====================

class ProductListView(APIView):
    """Barcha mahsulotlar ro'yxati (filter bilan)"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        products = Product.objects.filter(
            is_active=True
        ).select_related('category', 'brand', 'seller').prefetch_related('images')

        # Filtrlash
        category_slug = request.query_params.get('category')
        brand_slug = request.query_params.get('brand')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering', '-created_at')
        in_stock = request.query_params.get('in_stock')

        if category_slug:
            category = Category.objects.filter(slug=category_slug).first()
            if category:
                # Shu kategoriya va uning bolalari
                category_ids = [category.id]
                category_ids.extend(
                    category.children.filter(is_active=True).values_list('id', flat=True)
                )
                products = products.filter(category_id__in=category_ids)

        if brand_slug:
            products = products.filter(brand__slug=brand_slug)

        if min_price:
            products = products.filter(price__gte=min_price)

        if max_price:
            products = products.filter(price__lte=max_price)

        if search:
            from django.db.models import Q
            products = products.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        if in_stock and in_stock.lower() == 'true':
            products = products.filter(stock__gt=0)

        # Saralash
        allowed_orderings = [
            'price', '-price', 'created_at', '-created_at',
            'views_count', '-views_count', 'name', '-name',
        ]
        if ordering in allowed_orderings:
            products = products.order_by(ordering)

        serializer = ProductListSerializer(
            products, many=True, context={'request': request}
        )
        return Response({
            'success': True,
            'message': "Mahsulotlar ro'yxati.",
            'data': serializer.data,
            'count': len(serializer.data),
        }, status=status.HTTP_200_OK)


class ProductDetailView(APIView):
    """Mahsulot batafsil ko'rish"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        product = get_object_or_404(
            Product.objects.select_related('category', 'brand', 'seller')
            .prefetch_related('images'),
            slug=slug, is_active=True
        )
        # Ko'rishlar sonini oshirish
        product.views_count += 1
        product.save(update_fields=['views_count'])

        serializer = ProductDetailSerializer(product, context={'request': request})
        return Response({
            'success': True,
            'message': "Mahsulot tafsilotlari.",
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class ProductCreateView(APIView):
    """Seller: Yangi mahsulot qo'shish"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def post(self, request):
        serializer = ProductCreateUpdateSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response({
            'success': True,
            'message': "Mahsulot muvaffaqiyatli yaratildi.",
            'data': ProductDetailSerializer(product, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)


class ProductUpdateView(APIView):
    """Seller: O'z mahsulotini tahrirlash"""
    permission_classes = [permissions.IsAuthenticated, IsSeller, IsProductOwner]

    def get_object(self, pk):
        product = get_object_or_404(Product, pk=pk)
        self.check_object_permissions(self.request, product)
        return product

    def put(self, request, pk):
        product = self.get_object(pk)
        serializer = ProductCreateUpdateSerializer(
            instance=product, data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response({
            'success': True,
            'message': "Mahsulot muvaffaqiyatli yangilandi.",
            'data': ProductDetailSerializer(product, context={'request': request}).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        product = self.get_object(pk)
        serializer = ProductCreateUpdateSerializer(
            instance=product, data=request.data,
            partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response({
            'success': True,
            'message': "Mahsulot muvaffaqiyatli yangilandi.",
            'data': ProductDetailSerializer(product, context={'request': request}).data,
        }, status=status.HTTP_200_OK)


class ProductDeleteView(APIView):
    """Seller: O'z mahsulotini o'chirish (soft delete — is_active=False)"""
    permission_classes = [permissions.IsAuthenticated, IsSeller, IsProductOwner]

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        self.check_object_permissions(request, product)
        product.is_active = False
        product.save(update_fields=['is_active'])
        return Response({
            'success': True,
            'message': "Mahsulot muvaffaqiyatli o'chirildi.",
        }, status=status.HTTP_200_OK)


# ==================== PRODUCT IMAGE VIEWS ====================

class ProductImageAddView(APIView):
    """Seller: Mahsulotga rasm qo'shish"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if product.seller != request.user:
            return Response({
                'success': False,
                'message': "Siz bu mahsulotning egasi emassiz.",
            }, status=status.HTTP_403_FORBIDDEN)

        image = request.FILES.get('image')
        if not image:
            return Response({
                'success': False,
                'message': "Rasm fayli yuborilmadi.",
            }, status=status.HTTP_400_BAD_REQUEST)

        is_primary = request.data.get('is_primary', False)
        alt_text = request.data.get('alt_text', '')

        product_image = ProductImage.objects.create(
            product=product,
            image=image,
            is_primary=is_primary,
            alt_text=alt_text,
        )
        return Response({
            'success': True,
            'message': "Rasm muvaffaqiyatli qo'shildi.",
            'data': ProductImageSerializer(product_image).data,
        }, status=status.HTTP_201_CREATED)


class ProductImageDeleteView(APIView):
    """Seller: Mahsulot rasmini o'chirish"""
    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def delete(self, request, pk, image_id):
        product = get_object_or_404(Product, pk=pk)
        if product.seller != request.user:
            return Response({
                'success': False,
                'message': "Siz bu mahsulotning egasi emassiz.",
            }, status=status.HTTP_403_FORBIDDEN)

        image = get_object_or_404(ProductImage, pk=image_id, product=product)
        image.delete()
        return Response({
            'success': True,
            'message': "Rasm muvaffaqiyatli o'chirildi.",
        }, status=status.HTTP_200_OK)

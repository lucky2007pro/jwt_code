from rest_framework import serializers
from .models import SellerProfile
from products.models import Product
from products.serializers import ProductListSerializer
from accounts.models import CustomUser, SELLER


class SellerRegisterSerializer(serializers.ModelSerializer):
    """Seller profilini yaratish uchun"""

    class Meta:
        model = SellerProfile
        fields = ['shop_name', 'description', 'logo', 'banner', 'address', 'phone']

    def validate(self, attrs):
        user = self.context['request'].user
        if hasattr(user, 'seller_profile'):
            raise serializers.ValidationError({
                "xatolik": "Siz allaqachon sotuvchi sifatida ro'yxatdan o'tgansiz."
            })
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        # User role'ni seller ga o'zgartirish
        user.user_role = SELLER
        user.save(update_fields=['user_role'])

        seller_profile = SellerProfile.objects.create(
            user=user, **validated_data
        )
        return seller_profile


class SellerProfileSerializer(serializers.ModelSerializer):
    """Seller profili to'liq ko'rish"""
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = SellerProfile
        fields = [
            'id', 'username', 'full_name', 'email',
            'shop_name', 'shop_slug', 'description',
            'logo', 'banner', 'address', 'phone',
            'is_verified', 'rating', 'total_sales',
            'products_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'shop_slug', 'is_verified',
            'rating', 'total_sales',
            'created_at', 'updated_at',
        ]

    def get_products_count(self, obj):
        return Product.objects.filter(seller=obj.user, is_active=True).count()


class SellerProfileUpdateSerializer(serializers.ModelSerializer):
    """Seller profilini yangilash"""

    class Meta:
        model = SellerProfile
        fields = ['shop_name', 'description', 'logo', 'banner', 'address', 'phone']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        # slug ni yangilash agar shop_name o'zgarsa
        if 'shop_name' in validated_data:
            instance.shop_slug = ''  # save() da qayta generatsiya qiladi
        instance.save()
        return instance


class SellerDashboardSerializer(serializers.Serializer):
    """Seller dashboard statistikasi"""
    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_views = serializers.IntegerField()
    shop_rating = serializers.DecimalField(max_digits=3, decimal_places=2)


class SellerPublicSerializer(serializers.ModelSerializer):
    """Ommaviy ko'rinadigan seller profili"""
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = SellerProfile
        fields = [
            'id', 'shop_name', 'shop_slug', 'description',
            'logo', 'banner', 'full_name',
            'is_verified', 'rating', 'total_sales',
            'products_count', 'created_at',
        ]

    def get_products_count(self, obj):
        return Product.objects.filter(seller=obj.user, is_active=True).count()

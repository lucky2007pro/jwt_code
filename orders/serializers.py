from rest_framework import serializers
from .models import (
    ShippingAddress, Order, OrderItem, OrderStatusHistory,
    PENDING, CANCELLED,
)
from products.serializers import ProductListSerializer


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'full_name', 'phone', 'region', 'district',
            'address', 'zip_code', 'is_default', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ShippingAddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = ['full_name', 'phone', 'region', 'district', 'address', 'zip_code', 'is_default']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    product_slug = serializers.CharField(source='product.slug', read_only=True, default=None)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_slug', 'product_name',
            'product_price', 'quantity', 'total', 'seller',
        ]
        read_only_fields = ['id']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True, default=None)

    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'old_status', 'new_status', 'changed_by_name', 'note', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    """Buyurtma to'liq ko'rish"""
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = ShippingAddressSerializer(read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'payment_method', 'payment_method_display', 'is_paid',
            'subtotal', 'discount_amount', 'shipping_cost', 'total',
            'coupon_code', 'coupon_discount',
            'note', 'shipping_address', 'items', 'status_history',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'order_number', 'created_at', 'updated_at']


class OrderListSerializer(serializers.ModelSerializer):
    """Buyurtmalar ro'yxati uchun yengil serializer"""
    items_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'total', 'is_paid', 'items_count', 'created_at',
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class CheckoutSerializer(serializers.Serializer):
    """Savatchadan buyurtma yaratish"""
    shipping_address_id = serializers.UUIDField(required=True)
    payment_method = serializers.ChoiceField(
        choices=['cash', 'card', 'click', 'payme'], default='cash'
    )
    note = serializers.CharField(required=False, default='', allow_blank=True)
    coupon_code = serializers.CharField(required=False, default='', allow_blank=True)

    def validate_shipping_address_id(self, value):
        user = self.context['request'].user
        if not ShippingAddress.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Yetkazish manzili topilmadi.")
        return value


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Buyurtma holatini o'zgartirish"""
    status = serializers.ChoiceField(
        choices=['confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
    )
    note = serializers.CharField(required=False, default='', allow_blank=True)

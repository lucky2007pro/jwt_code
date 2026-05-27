from rest_framework import serializers
from .models import WishlistItem
from products.serializers import ProductListSerializer


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'created_at']
        read_only_fields = ['id', 'created_at']


class WishlistToggleSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(required=True)

    def validate_product_id(self, value):
        from products.models import Product
        if not Product.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Mahsulot topilmadi yoki faol emas.")
        return value

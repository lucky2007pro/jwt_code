from rest_framework import serializers
from .models import Coupon, CouponUsage


class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description', 'discount_type', 'discount_type_display',
            'discount_value', 'min_order_amount', 'max_discount',
            'usage_limit', 'used_count', 'per_user_limit',
            'valid_from', 'valid_to', 'is_active', 'is_valid',
            'created_at',
        ]
        read_only_fields = ['id', 'used_count', 'created_at']


class CouponCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            'code', 'description', 'discount_type', 'discount_value',
            'min_order_amount', 'max_discount',
            'usage_limit', 'per_user_limit',
            'valid_from', 'valid_to', 'is_active',
        ]

    def validate_code(self, value):
        return value.upper().strip()

    def validate(self, attrs):
        if attrs.get('valid_from') and attrs.get('valid_to'):
            if attrs['valid_from'] >= attrs['valid_to']:
                raise serializers.ValidationError({
                    "valid_to": "Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak."
                })
        if attrs.get('discount_value', 0) <= 0:
            raise serializers.ValidationError({
                "discount_value": "Chegirma qiymati 0 dan katta bo'lishi kerak."
            })
        if attrs.get('discount_type') == 'percentage' and attrs.get('discount_value', 0) > 100:
            raise serializers.ValidationError({
                "discount_value": "Foiz 100 dan oshmasligi kerak."
            })
        return attrs

    def create(self, validated_data):
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    order_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0
    )


class CouponApplySerializer(serializers.Serializer):
    code = serializers.CharField(required=True)

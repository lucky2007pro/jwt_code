from rest_framework import serializers
from .models import Review, ReviewImage, ReviewReply


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image']
        read_only_fields = ['id']


class ReviewReplySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = ReviewReply
        fields = ['id', 'username', 'full_name', 'text', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewSerializer(serializers.ModelSerializer):
    """Sharh ko'rish uchun to'liq serializer"""
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_photo = serializers.SerializerMethodField()
    images = ReviewImageSerializer(many=True, read_only=True)
    replies = ReviewReplySerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'username', 'full_name', 'user_photo',
            'rating', 'comment', 'pros', 'cons',
            'images', 'replies', 'is_approved',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_photo(self, obj):
        if obj.user.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.photo.url)
            return obj.user.photo.url
        return None


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Sharh qoldirish uchun"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True, required=False
    )

    class Meta:
        model = Review
        fields = ['product', 'rating', 'comment', 'pros', 'cons', 'images']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Baho 1 dan 5 gacha bo'lishi kerak.")
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        product = attrs.get('product')
        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError({
                "xatolik": "Siz bu mahsulotga allaqachon sharh qoldirgansiz."
            })
        return attrs

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        validated_data['user'] = self.context['request'].user
        review = Review.objects.create(**validated_data)

        for image in images_data:
            ReviewImage.objects.create(review=review, image=image)

        return review


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """O'z sharhini tahrirlash"""

    class Meta:
        model = Review
        fields = ['rating', 'comment', 'pros', 'cons']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Baho 1 dan 5 gacha bo'lishi kerak.")
        return value


class ReviewReplyCreateSerializer(serializers.Serializer):
    """Seller yoki admin javobi"""
    text = serializers.CharField(required=True)

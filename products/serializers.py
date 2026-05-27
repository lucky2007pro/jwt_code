from rest_framework import serializers
from .models import Category, Brand, Product, ProductImage


class CategoryChildSerializer(serializers.ModelSerializer):
    """Kategoriyaning child (bola) kategoriyalari uchun serializer"""

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'is_active']


class CategorySerializer(serializers.ModelSerializer):
    """Kategoriya serializer — children bilan"""
    children = CategoryChildSerializer(many=True, read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'image', 'parent',
            'is_active', 'children', 'products_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class CategoryCreateSerializer(serializers.ModelSerializer):
    """Kategoriya yaratish/tahrirlash uchun"""

    class Meta:
        model = Category
        fields = ['name', 'image', 'parent', 'is_active']


class BrandSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'slug', 'logo', 'description',
            'is_active', 'products_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class BrandCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['name', 'logo', 'description', 'is_active']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'alt_text']
        read_only_fields = ['id']


class ProductListSerializer(serializers.ModelSerializer):
    """Mahsulotlar ro'yxati uchun yengil serializer"""
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    brand_name = serializers.CharField(source='brand.name', read_only=True, default=None)
    seller_name = serializers.CharField(source='seller.full_name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    final_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_percentage = serializers.FloatField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'discount_price',
            'final_price', 'discount_percentage',
            'stock', 'is_in_stock', 'is_active',
            'category_name', 'brand_name', 'seller_name',
            'primary_image', 'views_count',
            'created_at',
        ]

    def get_primary_image(self, obj):
        img = obj.primary_image
        if img:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(img.image.url)
            return img.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Mahsulot batafsil ko'rish uchun to'liq serializer"""
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    seller_name = serializers.CharField(source='seller.full_name', read_only=True)
    seller_id = serializers.UUIDField(source='seller.id', read_only=True)
    final_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    discount_percentage = serializers.FloatField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    reviews_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'price', 'discount_price', 'final_price', 'discount_percentage',
            'stock', 'is_in_stock', 'is_active',
            'category', 'brand',
            'seller_id', 'seller_name',
            'images', 'specifications', 'views_count',
            'reviews_count', 'average_rating',
            'created_at', 'updated_at',
        ]

    def get_reviews_count(self, obj):
        if hasattr(obj, 'reviews'):
            return obj.reviews.count()
        return 0

    def get_average_rating(self, obj):
        if hasattr(obj, 'reviews'):
            from django.db.models import Avg
            avg = obj.reviews.aggregate(avg=Avg('rating'))['avg']
            return round(avg, 1) if avg else 0
        return 0


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Seller uchun mahsulot yaratish/tahrirlash"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True, required=False
    )

    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'discount_price',
            'stock', 'is_active', 'category', 'brand',
            'specifications', 'images',
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Narx 0 dan katta bo'lishi kerak.")
        return value

    def validate_discount_price(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Chegirmali narx 0 dan katta bo'lishi kerak.")
        return value

    def validate(self, attrs):
        price = attrs.get('price', getattr(self.instance, 'price', None))
        discount_price = attrs.get('discount_price')
        if discount_price and price and discount_price >= price:
            raise serializers.ValidationError({
                "discount_price": "Chegirmali narx asosiy narxdan kam bo'lishi kerak."
            })
        return attrs

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        request = self.context.get('request')
        validated_data['seller'] = request.user
        product = Product.objects.create(**validated_data)

        # Rasmlarni saqlash
        for i, image in enumerate(images_data):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(i == 0),  # Birinchi rasm primary
            )
        return product

    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Yangi rasmlar qo'shish
        if images_data:
            for image in images_data:
                ProductImage.objects.create(
                    product=instance,
                    image=image,
                )
        return instance

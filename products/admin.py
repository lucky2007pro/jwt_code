from django.contrib import admin
from .models import Category, Brand, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'is_primary', 'alt_text']
    readonly_fields = []


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    ordering = ['name']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    ordering = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'seller', 'category', 'brand',
        'price', 'discount_price', 'stock',
        'is_active', 'views_count', 'created_at',
    ]
    list_filter = ['is_active', 'category', 'brand', 'seller']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'stock', 'price']
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    inlines = [ProductImageInline]
    ordering = ['-created_at']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'slug', 'description', 'seller')
        }),
        ('Kategoriya va Brend', {
            'fields': ('category', 'brand')
        }),
        ('Narx va Zaxira', {
            'fields': ('price', 'discount_price', 'stock')
        }),
        ('Xususiyatlar', {
            'fields': ('specifications',),
            'classes': ('collapse',),
        }),
        ('Holat', {
            'fields': ('is_active', 'views_count', 'created_at', 'updated_at')
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'alt_text', 'created_at']
    list_filter = ['is_primary']
    search_fields = ['product__name', 'alt_text']

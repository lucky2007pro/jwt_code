from django.contrib import admin
from .models import SellerProfile


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = [
        'shop_name', 'user', 'shop_slug',
        'is_verified', 'rating', 'total_sales', 'created_at',
    ]
    list_filter = ['is_verified']
    search_fields = ['shop_name', 'user__username', 'user__email']
    list_editable = ['is_verified']
    readonly_fields = ['shop_slug', 'rating', 'total_sales', 'created_at', 'updated_at']
    ordering = ['-created_at']

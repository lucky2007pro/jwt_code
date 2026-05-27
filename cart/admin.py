from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'total_items', 'total_price', 'created_at']
    list_filter = ['is_active']
    search_fields = ['user__username', 'user__email']
    inlines = [CartItemInline]
    ordering = ['-created_at']

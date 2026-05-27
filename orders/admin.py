from django.contrib import admin
from .models import ShippingAddress, Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'seller', 'product_name', 'product_price', 'quantity', 'total']


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'note', 'created_at']


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'region', 'district', 'is_default', 'created_at']
    list_filter = ['region', 'is_default']
    search_fields = ['full_name', 'user__username', 'address']
    ordering = ['-created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'payment_method',
        'is_paid', 'total', 'created_at',
    ]
    list_filter = ['status', 'payment_method', 'is_paid', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email']
    list_editable = ['status', 'is_paid']
    readonly_fields = ['order_number', 'subtotal', 'total', 'created_at', 'updated_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    ordering = ['-created_at']

    fieldsets = (
        ('Buyurtma ma\'lumotlari', {
            'fields': ('order_number', 'user', 'shipping_address', 'note')
        }),
        ('Holat va To\'lov', {
            'fields': ('status', 'payment_method', 'is_paid')
        }),
        ('Narxlar', {
            'fields': ('subtotal', 'discount_amount', 'shipping_cost', 'coupon_code', 'coupon_discount', 'total')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

import random
import string
from django.db import models
from shared.models import BaseModel
from accounts.models import CustomUser
from products.models import Product

# Order status
PENDING = 'pending'
CONFIRMED = 'confirmed'
PROCESSING = 'processing'
SHIPPED = 'shipped'
DELIVERED = 'delivered'
CANCELLED = 'cancelled'
REFUNDED = 'refunded'

ORDER_STATUS = (
    (PENDING, 'Kutilmoqda'),
    (CONFIRMED, 'Tasdiqlangan'),
    (PROCESSING, 'Tayyorlanmoqda'),
    (SHIPPED, 'Yetkazilmoqda'),
    (DELIVERED, 'Yetkazildi'),
    (CANCELLED, 'Bekor qilindi'),
    (REFUNDED, 'Qaytarildi'),
)

# Payment methods
CASH = 'cash'
CARD = 'card'
CLICK = 'click'
PAYME = 'payme'

PAYMENT_METHOD = (
    (CASH, 'Naqd pul'),
    (CARD, 'Plastik karta'),
    (CLICK, 'Click'),
    (PAYME, 'Payme'),
)


class ShippingAddress(BaseModel):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='addresses'
    )
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    region = models.CharField(max_length=100, help_text="Viloyat")
    district = models.CharField(max_length=100, help_text="Tuman/Shahar")
    address = models.TextField(help_text="To'liq manzil")
    zip_code = models.CharField(max_length=10, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Yetkazish manzili'
        verbose_name_plural = 'Yetkazish manzillari'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.full_name} — {self.region}, {self.district}"

    def save(self, *args, **kwargs):
        # Agar bu default bo'lsa, boshqa default manzillarni o'chirish
        if self.is_default:
            ShippingAddress.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


def generate_order_number():
    """Unikal buyurtma raqami yaratish: ORD-XXXXXX"""
    from django.utils import timezone
    date_str = timezone.now().strftime('%y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"ORD-{date_str}-{random_str}"


class Order(BaseModel):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='orders'
    )
    order_number = models.CharField(
        max_length=20, unique=True, default=generate_order_number
    )
    shipping_address = models.ForeignKey(
        ShippingAddress, on_delete=models.SET_NULL, null=True
    )
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS, default=PENDING
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD, default=CASH
    )
    is_paid = models.BooleanField(default=False)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    shipping_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    total = models.DecimalField(max_digits=12, decimal_places=2)

    note = models.TextField(blank=True, help_text="Buyurtmachi izohi")

    coupon_code = models.CharField(max_length=50, blank=True)
    coupon_discount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} — {self.user.username} ({self.get_status_display()})"


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, related_name='order_items'
    )
    seller = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name='sold_items'
    )
    # Snapshot — mahsulot o'chsa ham saqlanadi
    product_name = models.CharField(max_length=300)
    product_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Buyurtma mahsuloti'
        verbose_name_plural = 'Buyurtma mahsulotlari'

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class OrderStatusHistory(BaseModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='status_history'
    )
    old_status = models.CharField(max_length=20, choices=ORDER_STATUS)
    new_status = models.CharField(max_length=20, choices=ORDER_STATUS)
    changed_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True
    )
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Buyurtma holat tarixi'
        verbose_name_plural = 'Buyurtma holat tarixlari'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} → {self.new_status}"

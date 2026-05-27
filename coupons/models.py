from django.db import models
from django.utils import timezone
from shared.models import BaseModel
from accounts.models import CustomUser
from products.models import Product, Category

PERCENTAGE = 'percentage'
FIXED = 'fixed'

DISCOUNT_TYPE = (
    (PERCENTAGE, 'Foizda'),
    (FIXED, 'Aniq summa'),
)


class Coupon(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE, default=PERCENTAGE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Minimal buyurtma summasi"
    )
    max_discount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Maksimal chegirma summasi (foizda chegirma uchun)"
    )
    usage_limit = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Umumiy foydalanish limiti"
    )
    used_count = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveIntegerField(default=1)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    # Seller kuponi
    seller = models.ForeignKey(
        CustomUser, null=True, blank=True,
        on_delete=models.CASCADE, related_name='coupons'
    )

    class Meta:
        verbose_name = 'Kupon'
        verbose_name_plural = 'Kuponlar'
        ordering = ['-created_at']

    def __str__(self):
        if self.discount_type == PERCENTAGE:
            return f"{self.code} — {self.discount_value}%"
        return f"{self.code} — {self.discount_value} so'm"

    @property
    def is_valid(self):
        """Kupon haqiqiymi?"""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_to:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True

    def calculate_discount(self, order_total):
        """Chegirma summasini hisoblash"""
        if self.discount_type == PERCENTAGE:
            discount = order_total * (self.discount_value / 100)
            if self.max_discount:
                discount = min(discount, self.max_discount)
        else:
            discount = self.discount_value
        return min(discount, order_total)  # Narxdan oshmasligi kerak


class CouponUsage(BaseModel):
    coupon = models.ForeignKey(
        Coupon, on_delete=models.CASCADE, related_name='usages'
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='coupon_usages'
    )
    order = models.ForeignKey(
        'orders.Order', on_delete=models.CASCADE,
        related_name='coupon_usages', null=True, blank=True
    )
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Kupon foydalanishi'
        verbose_name_plural = 'Kupon foydalanishlari'

    def __str__(self):
        return f"{self.user.username} — {self.coupon.code}"

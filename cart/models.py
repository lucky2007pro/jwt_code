from django.db import models
from django.db.models import Q
from shared.models import BaseModel
from accounts.models import CustomUser
from products.models import Product


class Cart(BaseModel):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='carts', null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Savatcha'
        verbose_name_plural = 'Savatchalar'
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=Q(is_active=True),
                name='unique_active_cart_per_user'
            )
        ]

    def __str__(self):
        return f"Savatcha: {self.user.username if self.user else 'Mehmon'}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(BaseModel):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Savatcha mahsuloti'
        verbose_name_plural = 'Savatcha mahsulotlari'
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        return self.product.final_price * self.quantity

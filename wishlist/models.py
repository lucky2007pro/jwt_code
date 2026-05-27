from django.db import models
from shared.models import BaseModel
from accounts.models import CustomUser
from products.models import Product


class WishlistItem(BaseModel):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='wishlist'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='wishlisted_by'
    )

    class Meta:
        verbose_name = 'Sevimli mahsulot'
        verbose_name_plural = 'Sevimli mahsulotlar'
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.product.name}"

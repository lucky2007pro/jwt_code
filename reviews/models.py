from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from shared.models import BaseModel
from accounts.models import CustomUser
from products.models import Product


class Review(BaseModel):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='reviews'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 dan 5 gacha baho"
    )
    comment = models.TextField()
    pros = models.TextField(blank=True, help_text="Afzalliklari")
    cons = models.TextField(blank=True, help_text="Kamchiliklari")
    is_approved = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Sharh'
        verbose_name_plural = 'Sharhlar'
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.product.name} ({self.rating}⭐)"


class ReviewImage(BaseModel):
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='images'
    )
    image = models.ImageField(upload_to='reviews/')

    class Meta:
        verbose_name = 'Sharh rasmi'
        verbose_name_plural = 'Sharh rasmlari'

    def __str__(self):
        return f"Rasm: {self.review}"


class ReviewReply(BaseModel):
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='replies'
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='review_replies'
    )
    text = models.TextField()

    class Meta:
        verbose_name = 'Sharh javobi'
        verbose_name_plural = 'Sharh javoblari'
        ordering = ['created_at']

    def __str__(self):
        return f"Javob: {self.user.username} → {self.review}"

from django.db import models
from django.utils.text import slugify
from shared.models import BaseModel
from accounts.models import CustomUser


class SellerProfile(BaseModel):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='seller_profile'
    )
    shop_name = models.CharField(max_length=200)
    shop_slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='sellers/', null=True, blank=True)
    banner = models.ImageField(upload_to='sellers/banners/', null=True, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_sales = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Sotuvchi profili'
        verbose_name_plural = 'Sotuvchi profillari'

    def __str__(self):
        return f"{self.shop_name} ({self.user.username})"

    def save(self, *args, **kwargs):
        if not self.shop_slug:
            self.shop_slug = slugify(self.shop_name)
            original_slug = self.shop_slug
            counter = 1
            while SellerProfile.objects.filter(shop_slug=self.shop_slug).exclude(pk=self.pk).exists():
                self.shop_slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

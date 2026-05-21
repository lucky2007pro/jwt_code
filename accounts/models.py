from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from conf.settings import EMAIL_EXPIRATION_TIME, PHONE_EXPIRATION_TIME

ORDINARY_USER, SELLER, ADMIN = ('ordinary_user', 'seller', 'admin')
VIA_PHONE, VIA_EMAIL = ('via_phone', 'via_email')
NEW, CODE_VERIFY, CHANGE_INFO, DONE = ('new', 'code_verify', 'change_info', 'done')


class CustomUser(AbstractUser):
    USER_ROLE = (
        (ORDINARY_USER, ORDINARY_USER),
        (SELLER, SELLER),
        (ADMIN, ADMIN),
    )
    AUTH_TYPE = (
        (VIA_PHONE, VIA_PHONE),
        (VIA_EMAIL, VIA_EMAIL),
    )
    AUTH_STATUS = (
        (NEW, NEW),
        (CODE_VERIFY, CODE_VERIFY),
        (CHANGE_INFO, CHANGE_INFO),
        (DONE, DONE),
    )

    user_role = models.CharField(max_length=20, choices=USER_ROLE, default=ORDINARY_USER)
    auth_type = models.CharField(max_length=20, choices=AUTH_TYPE, null=True, blank=True)
    auth_status = models.CharField(max_length=20, choices=AUTH_STATUS, default=NEW)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    photo = models.ImageField(upload_to='users/', null=True, blank=True)

    def __str__(self):
        return self.username

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class CodeVerify(models.Model):
    VERIFY_TYPE = (
        (VIA_PHONE, VIA_PHONE),
        (VIA_EMAIL, VIA_EMAIL),
    )

    code = models.CharField(max_length=4, null=False)
    verify_type = models.CharField(max_length=20, choices=VERIFY_TYPE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='code_verifies')
    if_used = models.BooleanField(default=False)
    expiration_time = models.DateTimeField()

    def save(self, *args, **kwargs):
        if self.verify_type == VIA_EMAIL:
            self.expiration_time = timezone.now() + timezone.timedelta(minutes=EMAIL_EXPIRATION_TIME)
        else:
            self.expiration_time = timezone.now() + timezone.timedelta(minutes=PHONE_EXPIRATION_TIME)
        super().save(*args, **kwargs)

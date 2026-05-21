import random
import uuid
from shared.models import BaseModel
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from conf.settings import EMAIL_EXPIRATION_TIME, PHONE_EXPIRATION_TIME
from rest_framework_simplejwt.tokens import RefreshToken
import string

ORDINARY_USER, SELLER, ADMIN = ('ordinary_user', 'seller', 'admin')
VIA_PHONE, VIA_EMAIL = ('via_phone', 'via_email')
NEW, CODE_VERIFY, CHANGE_INFO, DONE = ('new', 'code_verify', 'change_info', 'done')


class CustomUser(BaseModel, AbstractUser):
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
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def create_code(self, verify_type):
        code = string.ascii_letters + string.digits
        code = ''.join(random.choice(code) for _ in range(4))
        CodeVerify.objects.create(
            user=self,
            code=code,
            verify_type=verify_type,
        )
        return code

    def token(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def ensure_username(self):
        if not self.username:
            temp_username = str(uuid.uuid4()).split('-')[-1]
            while CustomUser.objects.filter(username=temp_username).exists():
                temp_username += str(random.randint(0, 10))
            self.username = temp_username

    def ensure_password(self):
        if not self.password or not self.has_usable_password():
            temp_password = str(uuid.uuid4()).split('-')[-1]
            self.set_password(temp_password)

    def email_normalize(self):
        if self.email:
            self.email = self.email.lower()

    def clean(self):
        super().clean()
        self.email_normalize()
        self.ensure_username()
        self.ensure_password()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class CodeVerify(BaseModel):
    VERIFY_TYPE = (
        (VIA_PHONE, VIA_PHONE),
        (VIA_EMAIL, VIA_EMAIL),
    )

    code = models.CharField(max_length=4, null=False)
    verify_type = models.CharField(max_length=20, choices=VERIFY_TYPE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='code_verifies', null=False)
    if_used = models.BooleanField(default=False)
    expiration_time = models.DateTimeField()

    def save(self, *args, **kwargs):
        if self.verify_type == VIA_EMAIL:
            self.expiration_time = timezone.now() + timezone.timedelta(minutes=EMAIL_EXPIRATION_TIME)
        else:
            self.expiration_time = timezone.now() + timezone.timedelta(minutes=PHONE_EXPIRATION_TIME)
        super().save(*args, **kwargs)

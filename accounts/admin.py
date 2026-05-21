from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, CodeVerify


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Contact', {'fields': ('phone_number', 'photo')}),
        ('Auth', {'fields': ('user_role', 'auth_type', 'auth_status')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Contact', {'fields': ('phone_number', 'photo')}),
        ('Auth', {'fields': ('user_role', 'auth_type', 'auth_status')}),
    )
    list_display = ('username', 'email', 'phone_number', 'user_role', 'auth_status', 'is_staff', 'is_active')


@admin.register(CodeVerify)
class CodeVerifyAdmin(admin.ModelAdmin):
    list_display = ('user', 'verify_type', 'code', 'if_used', 'expiration_time')
    list_filter = ('verify_type', 'if_used')
    search_fields = ('user__username', 'user__email', 'user__phone_number', 'code')

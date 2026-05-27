from rest_framework import permissions
from accounts.models import SELLER, ADMIN


class IsSeller(permissions.BasePermission):
    message = "Faqat sotuvchilar uchun ruxsat berilgan."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.user_role in [SELLER, ADMIN]
        )


class IsProductOwner(permissions.BasePermission):
    message = "Siz bu mahsulotning egasi emassiz."

    def has_object_permission(self, request, view, obj):
        if request.user.user_role == ADMIN:
            return True
        return obj.seller == request.user


class IsAdminUser(permissions.BasePermission):
    message = "Faqat administratorlar uchun ruxsat berilgan."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.user_role == ADMIN
        )

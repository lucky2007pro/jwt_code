import re
import secrets
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.utils import timezone
from rest_framework import serializers

from .models import CodeVerify, VIA_EMAIL, VIA_PHONE, CODE_VERIFY, DONE


User = get_user_model()

PHONE_REGEX = re.compile(r'^\+?\d{7,15}$')


def _normalize_identifier(identifier: str) -> tuple[str, str]:
    identifier = identifier.strip()
    try:
        validate_email(identifier)
        return identifier.lower(), VIA_EMAIL
    except DjangoValidationError:
        pass

    cleaned = re.sub(r'[\s\-()]+', '', identifier)
    if not PHONE_REGEX.match(cleaned):
        raise serializers.ValidationError({'identifier': 'Enter a valid email or phone number.'})

    return cleaned, VIA_PHONE


def _generate_username(seed: str) -> str:
    base = str(uuid.uuid5(uuid.NAMESPACE_DNS, seed)).split('-')[-1]
    candidate = base
    suffix = 0
    while User.objects.filter(username=candidate).exists():
        suffix += 1
        candidate = f"{base}{suffix}"
    return candidate


def _generate_password() -> str:
    return secrets.token_urlsafe(8)


def _get_or_create_user(identifier: str, verify_type: str) -> User:
    if verify_type == VIA_EMAIL:
        user = User.objects.filter(email=identifier).first()
    else:
        user = User.objects.filter(phone_number=identifier).first()

    if user is None:
        user = User(
            username=_generate_username(identifier),
            email=identifier if verify_type == VIA_EMAIL else None,
            phone_number=identifier if verify_type == VIA_PHONE else None,
            auth_type=verify_type,
            auth_status=CODE_VERIFY,
        )
        user.set_unusable_password()
        user.save()
    else:
        updates = []
        if user.auth_type != verify_type:
            user.auth_type = verify_type
            updates.append('auth_type')
        if user.auth_status != CODE_VERIFY:
            user.auth_status = CODE_VERIFY
            updates.append('auth_status')
        if updates:
            user.save(update_fields=updates)

    return user


class RequestCodeSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=255, required=True)

    def validate(self, attrs):
        identifier, verify_type = _normalize_identifier(attrs['identifier'])
        attrs['identifier'] = identifier
        attrs['verify_type'] = verify_type
        return attrs

    def create(self, validated_data):
        user = _get_or_create_user(validated_data['identifier'], validated_data['verify_type'])
        code = f"{secrets.randbelow(10**4):04d}"
        record = CodeVerify.objects.create(
            user=user,
            verify_type=validated_data['verify_type'],
            code=code,
        )
        print(f"[DEBUG] Verification code for {validated_data['identifier']}: {code}")
        return record


class VerifyCodeSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=255, required=True)
    code = serializers.CharField(min_length=4, max_length=4, required=True)

    def validate(self, attrs):
        if not attrs['code'].isdigit():
            raise serializers.ValidationError({'code': 'Verification code must be numeric.'})

        identifier, verify_type = _normalize_identifier(attrs['identifier'])
        attrs['identifier'] = identifier
        attrs['verify_type'] = verify_type

        user = _get_or_create_user(identifier, verify_type)
        record = (
            CodeVerify.objects.filter(
                user=user,
                verify_type=verify_type,
                if_used=False,
            )
            .order_by('-id')
            .first()
        )
        if record is None:
            raise serializers.ValidationError({'code': 'Verification code not found.'})
        if record.expiration_time <= timezone.now():
            raise serializers.ValidationError({'code': 'Verification code expired.'})
        if record.code != attrs['code']:
            raise serializers.ValidationError({'code': 'Verification code is incorrect.'})

        attrs['user'] = user
        attrs['record'] = record
        return attrs

    def create(self, validated_data):
        record = validated_data['record']
        CodeVerify.objects.filter(pk=record.pk).update(if_used=True)

        user = validated_data['user']
        created_password = None
        if user.auth_status != DONE:
            created_password = _generate_password()
            user.set_password(created_password)
            user.auth_status = DONE
            user.save(update_fields=['password', 'auth_status'])

        return {
            'user': user,
            'password': created_password,
        }

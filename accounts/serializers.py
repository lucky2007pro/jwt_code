from rest_framework import serializers

from shared.utils import send_to_email
from .models import CustomUser, CodeVerify, VIA_EMAIL, VIA_PHONE, NEW, CODE_VERIFY, CHANGE_INFO, CHANGE_DONE
from shared.utility import check_email_or_phone
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password


class SignUpSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, *args, **kwargs):
        super().__init__(instance, *args, **kwargs)
        self.fields['email_or_phone'] = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ['email_or_phone', 'id', 'auth_type']
        extra_kwargs = {
            'id': {'read_only': True, 'required': False},
            'auth_type': {'read_only': True, 'required': False},
            'auth_status': {'read_only': True, 'required': False},
        }

    def create(self, validated_data):
        user = super(SignUpSerializer, self).create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.create_code(verify_type=VIA_EMAIL)
            send_to_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_code(verify_type=VIA_PHONE)
            print(code)
        else:
            raise ValidationError({"xatolik": "Autentifikatsiya turi noto'g'ri."})
        user.save()
        return user

    def validate(self, attrs):
        attrs = super().validate(attrs)
        return self.auth_validate(attrs)

    @staticmethod
    def auth_validate(data):
        user_input = data.get('email_or_phone')
        if not user_input:
            raise ValidationError({"email_or_phone": "Email yoki telefon raqami kiritilishi shart."})
        user_input_type, normalized = check_email_or_phone(user_input)
        if user_input_type == 'email':
            data['email'] = normalized
            data['auth_type'] = VIA_EMAIL
        elif user_input_type == 'phone':
            data['phone_number'] = normalized
            data['auth_type'] = VIA_PHONE
        else:
            raise ValidationError({"email_or_phone": "Noto'g'ri format. Email yoki telefon raqami kiriting."})
        data.pop('email_or_phone', None)
        return data

    def validate_email_or_phone(self, value):
        input_type, normalized = check_email_or_phone(value)
        if input_type == 'email':
            exists = CustomUser.objects.filter(email=normalized).exists()
        else:
            exists = CustomUser.objects.filter(phone_number=normalized).exists()
        if exists:
            raise ValidationError("Bu email yoki telefon raqami allaqachon ro'yxatdan o'tgan.")
        return value

    def to_representation(self, instance):
        user = super().to_representation(instance)
        user['token'] = instance.token()
        return user


class VerifySerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(required=True)
    code = serializers.CharField(required=True, max_length=4)

    def validate(self, attrs):
        user_input = attrs.get('email_or_phone', '')
        code = attrs.get('code', '')

        field_type, cleaned_value = check_email_or_phone(user_input)

        if field_type == 'email':
            user = CustomUser.objects.filter(email=cleaned_value).first()
            verify_type = VIA_EMAIL
        elif field_type == 'phone':
            user = CustomUser.objects.filter(phone_number=cleaned_value).first()
            verify_type = VIA_PHONE
        else:
            raise ValidationError({"email_or_phone": "Noto'g'ri format. Email yoki telefon raqami kiriting."})

        if not user:
            raise ValidationError({"email_or_phone": "Foydalanuvchi topilmadi."})

        verify = CodeVerify.objects.filter(
            user=user,
            code=code,
            verify_type=verify_type,
            if_used=False,
            expiration_time__gt=timezone.now(),
        ).first()
        if not verify:
            raise ValidationError({"code": "Kod noto'g'ri yoki muddati o'tgan."})

        attrs['user'] = user
        attrs['verify'] = verify
        attrs.pop('email_or_phone', None)
        return attrs


class GetNewCodeSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(required=True)

    def validate(self, attrs):
        user_input = attrs.get('email_or_phone')
        user_input_type, normalized = check_email_or_phone(user_input)
        if user_input_type == 'email':
            user = CustomUser.objects.filter(email=normalized).first()
        elif user_input_type == 'phone':
            user = CustomUser.objects.filter(phone_number=normalized).first()
        else:
            raise ValidationError({"email_or_phone": "Noto'g'ri format. Email yoki telefon raqami kiriting."})

        if not user:
            raise ValidationError({"email_or_phone": "Foydalanuvchi topilmadi."})

        active_code = CodeVerify.objects.filter(
            user=user,
            if_used=False,
            expiration_time__gt=timezone.now(),
        ).exists()
        if active_code:
            raise ValidationError({"xatolik": "Faol kod mavjud. Iltimos, uni ishlating yoki muddati tugashini kuting."})

        attrs['user'] = user
        return attrs


class ChangeProfileInfoSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True, max_length=100)
    last_name = serializers.CharField(required=True, max_length=100)
    user_role = serializers.CharField(required=True, max_length=100)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'password', 'confirm_password', 'user_role']

    def validate(self, attrs):
        if attrs.get('password') and attrs.get('confirm_password') and attrs['password'] != attrs['confirm_password']:
            raise ValidationError({"password": "Parollar bir-biriga mos kelmadi!"})
        return attrs

    def update(self, instance, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.user_role = validated_data.get('user_role', instance.user_role)

        if password:
            instance.set_password(password)

        instance.auth_status = CHANGE_INFO
        instance.save()
        return instance


class CompleteProfileInfoSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True, max_length=100)
    last_name = serializers.CharField(required=True, max_length=100)
    user_role = serializers.CharField(required=True, max_length=100)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'password', 'confirm_password', 'user_role']

    def validate(self, attrs):
        if attrs.get('password') and attrs.get('confirm_password') and attrs['password'] != attrs['confirm_password']:
            raise ValidationError({"password": "Parollar bir-biriga mos kelmadi!"})
        return attrs

    def update(self, instance, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.user_role = validated_data.get('user_role', instance.user_role)

        if password:
            instance.set_password(password)

        instance.auth_status = CHANGE_INFO
        instance.save()
        return instance


class UploadPhotoInfoSerializer(serializers.Serializer):
    photo = serializers.ImageField(required=False)

    def update(self, instance, validated_data):
        photo = validated_data.get('photo', None)
        if photo:
            instance.photo = photo
        instance.auth_status = CHANGE_DONE
        instance.save(update_fields=['photo', 'auth_status'])
        return instance


class LoginSerializer(serializers.Serializer):
    user_input = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        user_input = attrs.get('user_input')
        password = attrs.get('password')

        if not user_input:
            raise ValidationError({"user_input": "Email yoki telefon raqami kiritilishi shart."})
        if not password:
            raise ValidationError({"password": "Parol kiritilishi shart."})

        input_type, normalized = check_email_or_phone(user_input)
        if input_type == 'email':
            user = CustomUser.objects.filter(email=normalized).first()
        elif input_type == 'phone':
            user = CustomUser.objects.filter(phone_number=normalized).first()
        else:
            raise ValidationError({"user_input": "Noto'g'ri format. Email yoki telefon raqami kiriting."})

        if not user:
            raise ValidationError({"xatolik": "Foydalanuvchi topilmadi."})

        if not user.check_password(password):
            raise ValidationError({"xatolik": "Parol noto'g'ri."})

        if not user.is_active:
            raise ValidationError({"xatolik": "Foydalanuvchi hisobi faol emas."})

        attrs['user'] = user
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'email', 'phone_number', 'photo',
            'user_role', 'auth_type', 'auth_status',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'username', 'email', 'phone_number',
            'auth_type', 'auth_status', 'created_at', 'updated_at',
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'photo', 'user_role']

    def validate_first_name(self, value):
        if value and len(value.strip()) < 2:
            raise ValidationError("Ism kamida 2 ta belgidan iborat bo'lishi kerak.")
        return value

    def validate_last_name(self, value):
        if value and len(value.strip()) < 2:
            raise ValidationError("Familiya kamida 2 ta belgidan iborat bo'lishi kerak.")
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        if user.auth_status == NEW:
            raise ValidationError({"xatolik": "Profil ma'lumotlarini o'zgartirish uchun avval autentifikatsiyani yakunlang."})
        return attrs

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.user_role = validated_data.get('user_role', instance.user_role)
        photo = validated_data.get('photo', None)
        if photo:
            instance.photo = photo
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')

        if not user.check_password(old_password):
            raise ValidationError({"old_password": "Eski parol noto'g'ri."})
        if new_password != confirm_new_password:
            raise ValidationError({"confirm_new_password": "Yangi parollar bir-biriga mos kelmadi."})
        if old_password == new_password:
            raise ValidationError({"new_password": "Yangi parol eski paroldan farqli bo'lishi kerak."})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(required=True)

    def validate(self, attrs):
        user_input = attrs.get('email_or_phone')
        user_input_type, normalized = check_email_or_phone(user_input)
        if user_input_type == 'email':
            user = CustomUser.objects.filter(email=normalized).first()
        elif user_input_type == 'phone':
            user = CustomUser.objects.filter(phone_number=normalized).first()
        else:
            raise ValidationError({"email_or_phone": "Noto'g'ri format. Email yoki telefon raqami kiriting."})

        if not user:
            raise ValidationError({"email_or_phone": "Foydalanuvchi topilmadi."})

        active_code = CodeVerify.objects.filter(
            user=user,
            if_used=False,
            expiration_time__gt=timezone.now(),
        ).exists()
        if active_code:
            raise ValidationError({"xatolik": "Faol kod mavjud. Iltimos, uni ishlating yoki muddati tugashini kuting."})

        attrs['user'] = user
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(required=True)
    code = serializers.CharField(required=True, max_length=4)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        user_input = attrs.get('email_or_phone')
        code = attrs.get('code')
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')

        if new_password != confirm_new_password:
            raise ValidationError({"confirm_new_password": "Yangi parollar bir-biriga mos kelmadi."})

        user_input_type, normalized = check_email_or_phone(user_input)
        if user_input_type == 'email':
            user = CustomUser.objects.filter(email=normalized).first()
            verify_type = VIA_EMAIL
        elif user_input_type == 'phone':
            user = CustomUser.objects.filter(phone_number=normalized).first()
            verify_type = VIA_PHONE
        else:
            raise ValidationError({"email_or_phone": "Noto'g'ri format. Email yoki telefon raqami kiriting."})

        if not user:
            raise ValidationError({"email_or_phone": "Foydalanuvchi topilmadi."})

        verify = CodeVerify.objects.filter(
            user=user,
            code=code,
            verify_type=verify_type,
            if_used=False,
            expiration_time__gt=timezone.now(),
        ).first()
        if not verify:
            raise ValidationError({"code": "Kod noto'g'ri yoki muddati o'tgan."})

        attrs['user'] = user
        attrs['verify'] = verify
        return attrs
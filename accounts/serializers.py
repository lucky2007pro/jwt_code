from rest_framework import serializers

from shared.utils import send_to_email
from .models import CustomUser, CodeVerify, VIA_EMAIL, VIA_PHONE
from shared.utility import check_email_or_phone
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

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
            raise ValidationError('Invalid authentication type.')
        user.save()
        return user

    def validate(self, attrs):
        attrs = super().validate(attrs)
        return self.auth_validate(attrs)

    @staticmethod
    def auth_validate(data):
        user_input = data.get('email_or_phone')
        if not user_input:
            raise ValidationError('Invalid input type. Must be email or phone number.')
        user_input_type = check_email_or_phone(user_input)
        if user_input_type == 'email':
            data['email'] = user_input
            data['auth_type'] = VIA_EMAIL
        elif user_input_type == 'phone':
            user_input = '+' + user_input \
                if len(user_input) == 12 \
                else '+998' + user_input \
                if len(user_input) == 9 \
                else user_input
            data['phone_number'] = user_input
            data['auth_type'] = VIA_PHONE
        else:
            raise ValidationError('Invalid input type. Must be email or phone number.')
        data.pop('email_or_phone', None)
        return data

    def validate_email_or_phone(self, value):
        data = CustomUser.objects.filter(Q(email=value) | Q(phone_number=value)).exists()
        if data:
            raise ValidationError('User with this email or phone number already exists.')
        return value

    def to_representation(self, instance):
        user = super().to_representation(instance)
        user['token'] = instance.token()
        return user

class ChangeProfileInfoSerializer(serializers.ModelSerializer):
    conf_password = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number', 'password', 'conf_password']


    def validate(self, attrs):
        attrs = super().validate(attrs)
        password = attrs.get('password')
        conf_password = attrs.get('conf_password')
        if password and conf_password and password != conf_password:
            raise ValidationError('Password and confirm password do not match.')
        return attrs

    def validate_username(self, username):
        if username and CustomUser.objects.filter(username=username).exclude(id=self.instance.id).exists():
            raise ValidationError('Username already exists.')
        return username

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = self.validate_username(validated_data.get('username', instance.username))
        instance.email = validated_data.get('email', instance.email)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class VerifySerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(required=True)
    code = serializers.CharField(required=True, max_length=4)

    def validate(self, attrs):
        user_input = attrs.get('email_or_phone')
        user_input_type = check_email_or_phone(user_input)
        if user_input_type == 'email':
            user = CustomUser.objects.filter(email=user_input).first()
        elif user_input_type == 'phone':
            normalized = '+' + user_input if len(user_input) == 12 else '+998' + user_input if len(user_input) == 9 else user_input
            user = CustomUser.objects.filter(phone_number=normalized).first()
        else:
            raise ValidationError('Invalid input type. Must be email or phone number.')

        if not user:
            raise ValidationError('User not found.')

        code = attrs.get('code')
        verify = CodeVerify.objects.filter(
            user=user,
            code=code,
            if_used=False,
            expiration_time__gt=timezone.now(),
        ).first()
        if not verify:
            raise ValidationError('Invalid or expired code.')

        attrs['user'] = user
        attrs['verify'] = verify
        return attrs


class GetNewCodeSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(required=True)

    def validate(self, attrs):
        user_input = attrs.get('email_or_phone')
        user_input_type = check_email_or_phone(user_input)
        if user_input_type == 'email':
            user = CustomUser.objects.filter(email=user_input).first()
        elif user_input_type == 'phone':
            normalized = '+' + user_input if len(user_input) == 12 else '+998' + user_input if len(user_input) == 9 else user_input
            user = CustomUser.objects.filter(phone_number=normalized).first()
        else:
            raise ValidationError('Invalid input type. Must be email or phone number.')

        if not user:
            raise ValidationError('User not found.')

        active_code = CodeVerify.objects.filter(
            user=user,
            if_used=False,
            expiration_time__gt=timezone.now(),
        ).exists()
        if active_code:
            raise ValidationError('A valid code already exists. Please use it or wait until it expires.')

        attrs['user'] = user
        return attrs

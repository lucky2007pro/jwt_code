from rest_framework import serializers
from .models import CustomUser, VIA_EMAIL, VIA_PHONE
from shared.utility import check_email_or_phone
from rest_framework.exceptions import ValidationError

class SignUpSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, *args, **kwargs):
        super().__init__(instance, *args, **kwargs)
        self.fields['email_or_phone'] = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ['email_or_phone', 'id', 'auth_type']

    def create(self, validated_data):
        user = super(SignUpSerializer, self).create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.create_code(verify_type=VIA_EMAIL)
            print(code)
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
            data['phone_number'] = user_input
            data['auth_type'] = VIA_PHONE
        else:
            raise ValidationError('Invalid input type. Must be email or phone number.')
        data.pop('email_or_phone', None)
        return data

    def validate_email_or_phone(self, value):
        email = CustomUser.objects.filter(email=value).exists()
        phone = CustomUser.objects.filter(phone_number=value).exists()
        if email:
            raise ValidationError({'email_or_phone': 'This email is already registered.'})
        if phone:
            raise ValidationError({'email_or_phone': 'This phone number is already registered.'})
        return value

    def to_representation(self, instance):
        user = super().to_representation(instance)
        user['token'] = instance.token()
        return user
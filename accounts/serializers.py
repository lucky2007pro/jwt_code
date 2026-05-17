from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.serializers import Serializer, ModelSerializer
from rest_framework.validators import UniqueValidator


class SignUpSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password_conf = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='A user with this email already exists.',
            )
        ],
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'password_conf']

    def validate(self, attrs):
        password = attrs.get('password')
        password_conf = attrs.pop('password_conf', None)

        if password != password_conf:
            raise serializers.ValidationError({'password_conf': 'Passwords do not match.'})

        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password_conf', None)

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(Serializer):
    password = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError('Invalid credentials.')

        attrs['user'] = user
        return attrs


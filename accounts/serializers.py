from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.serializers import Serializer, ModelSerializer


class SignUpSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password_conf = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'password_conf']

    def create(self, validated_data):
        password = validated_data.pop('password')
        password_conf = validated_data.pop('password_conf')

        if password != password_conf:
            raise serializers.ValidationError("Passwords do not match")

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(Serializer):
    password = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(write_only=True, required=True)

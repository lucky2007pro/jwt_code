from .models import CustomUser
from rest_framework.generics import CreateAPIView
from .serializers import SignUpSerializer
from rest_framework import permissions

class SignUpView(CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = [permissions.AllowAny]
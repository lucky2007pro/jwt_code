from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework import permissions, status
from rest_framework.views import APIView
from .models import CustomUser, VIA_PHONE, VIA_EMAIL, NEW, CODE_VERIFY
from .serializers import (
    SignUpSerializer, VerifySerializer,
    GetNewCodeSerializer, ChangeProfileInfoSerializer,
    CompleteProfileInfoSerializer, UploadPhotoInfoSerializer,
    LoginSerializer, ProfileSerializer, ProfileUpdateSerializer,
    ResetPasswordSerializer, ForgotPasswordSerializer, ChangePasswordSerializer,
)
from shared.utils import send_to_email
from rest_framework_simplejwt.tokens import RefreshToken


class SignUpView(CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def xabar(request):
    send_to_email('worldcyber2007@gmail.com', '1234')
    return Response({
        'success': True,
        'message': "Xabar muvaffaqiyatli yuborildi.",
    }, status=status.HTTP_200_OK)


class VerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        verify = serializer.validated_data['verify']

        verify.if_used = True
        verify.save(update_fields=['if_used'])
        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFY
            user.save(update_fields=['auth_status'])

        return Response({
            'success': True,
            'message': "Kod muvaffaqiyatli tasdiqlandi.",
            'data': {
                'token': user.token(),
                'auth_status': user.auth_status,
            }
        }, status=status.HTTP_200_OK)


class GetNewCode(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GetNewCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if user.auth_type == VIA_EMAIL:
            code = user.create_code(verify_type=VIA_EMAIL)
            send_to_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_code(verify_type=VIA_PHONE)
            print(code)
        else:
            return Response({
                'success': False,
                'message': "Autentifikatsiya turi noto'g'ri.",
            }, status=status.HTTP_400_BAD_REQUEST)

        user.save()
        return Response({
            'success': True,
            'message': "Yangi kod yaratildi va yuborildi.",
        }, status=status.HTTP_200_OK)


class ChangeProfileInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        serializer = ChangeProfileInfoSerializer(instance=self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Ism, familiya va parol muvaffaqiyatli saqlandi.",
            'data': {
                'auth_status': self.get_object().auth_status,
                'user': serializer.data,
            }
        }, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        serializer = ChangeProfileInfoSerializer(instance=self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Ism, familiya va parol muvaffaqiyatli saqlandi.",
            'data': {
                'auth_status': self.get_object().auth_status,
                'user': serializer.data,
            }
        }, status=status.HTTP_200_OK)


class CompleteProfileInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        serializer = CompleteProfileInfoSerializer(instance=self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Ma'lumotlar muvaffaqiyatli saqlandi. Endi rasm yuklashingiz mumkin.",
            'data': {
                'auth_status': self.get_object().auth_status,
                'user': serializer.data,
            }
        }, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        serializer = CompleteProfileInfoSerializer(instance=self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Ma'lumotlar muvaffaqiyatli saqlandi. Endi rasm yuklashingiz mumkin.",
            'data': {
                'auth_status': self.get_object().auth_status,
                'user': serializer.data,
            }
        }, status=status.HTTP_200_OK)


class UploadPhotoInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        serializer = UploadPhotoInfoSerializer(instance=self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Rasm muvaffaqiyatli yuklandi.",
            'data': {
                'auth_status': self.get_object().auth_status,
            }
        }, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        serializer = UploadPhotoInfoSerializer(instance=self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Rasm muvaffaqiyatli yuklandi.",
            'data': {
                'auth_status': self.get_object().auth_status,
            }
        }, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        tokens = user.token()

        return Response({
            'success': True,
            'message': "Tizimga muvaffaqiyatli kirdingiz.",
            'data': {
                'token': tokens,
                'auth_status': user.auth_status,
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'photo': user.photo.url if user.photo else None,
                    'user_role': user.user_role,
                }
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'success': False,
                'message': "Refresh token kiritilishi shart.",
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'success': True,
                'message': "Tizimdan muvaffaqiyatli chiqdingiz.",
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'success': False,
                'message': "Token noto'g'ri yoki muddati o'tgan.",
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = ProfileSerializer(user)
        return Response({
            'success': True,
            'message': "Profil ma'lumotlari muvaffaqiyatli olindi.",
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class ProfileUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = ProfileUpdateSerializer(instance=user, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        profile_data = ProfileSerializer(user).data
        return Response({
            'success': True,
            'message': "Profil ma'lumotlari muvaffaqiyatli yangilandi.",
            'data': profile_data,
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user
        serializer = ProfileUpdateSerializer(
            instance=user, data=request.data,
            partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        profile_data = ProfileSerializer(user).data
        return Response({
            'success': True,
            'message': "Profil ma'lumotlari muvaffaqiyatli yangilandi.",
            'data': profile_data,
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        verify = serializer.validated_data['verify']
        new_password = serializer.validated_data['new_password']

        verify.if_used = True
        verify.save(update_fields=['if_used'])

        user.set_password(new_password)
        user.save()

        return Response({
            'success': True,
            'message': "Parol muvaffaqiyatli tiklandi.",
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if user.auth_type == VIA_EMAIL or user.email:
            code = user.create_code(verify_type=VIA_EMAIL)
            send_to_email(user.email, code)
            return Response({
                'success': True,
                'message': "Tasdiqlash kodi emailga yuborildi.",
            }, status=status.HTTP_200_OK)
        elif user.auth_type == VIA_PHONE or user.phone_number:
            code = user.create_code(verify_type=VIA_PHONE)
            print(code)
            return Response({
                'success': True,
                'message': "Tasdiqlash kodi telefon raqamiga yuborildi.",
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': "Foydalanuvchining aloqa ma'lumotlari topilmadi.",
            }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': "Parol muvaffaqiyatli o'zgartirildi.",
        }, status=status.HTTP_200_OK)

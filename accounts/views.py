from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework import permissions
from rest_framework.views import APIView

from .models import CustomUser, VIA_PHONE, VIA_EMAIL, NEW, CODE_VERIFY
from .serializers import SignUpSerializer, VerifySerializer, GetNewCodeSerializer, ChangeProfileInfoSerializer
from shared.utils import send_to_email

class SignUpView(CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = [permissions.AllowAny]

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def xabar(request):
    send_to_email('worldcyber2007@gmail.com', '1234')
    return Response('Xabar yuborildi')

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
            'message': 'Code verified successfully',
            'token': user.token(),
            'auth_status': user.auth_status,
        })


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
            return Response({'message': 'Invalid authentication type.'}, status=400)
        user.save()
        return Response({'message': 'New code generated and sent successfully.'})


class ChangeProfileInfoView(UpdateAPIView):
    serializer_class = ChangeProfileInfoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

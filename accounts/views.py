from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RequestCodeSerializer, VerifyCodeSerializer


class RequestCodeView(APIView):
    def post(self, request):
        serializer = RequestCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = serializer.save()

        return Response(
            {
                'message': 'Verification code sent.',
                'identifier': serializer.validated_data['identifier'],
                'expires_at': record.expiration_time,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyCodeView(APIView):
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        user = result['user']
        token = RefreshToken.for_user(user)

        response = {
            'message': 'Verification successful.',
            'access': str(token.access_token),
            'refresh': str(token),
            'username': user.username,
        }
        if result['password']:
            response['password'] = result['password']

        return Response(response, status=status.HTTP_200_OK)

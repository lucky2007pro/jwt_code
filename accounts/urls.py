from django.urls import path

from .views import RequestCodeView, VerifyCodeView

urlpatterns = [
    path('request-code/', RequestCodeView.as_view(), name='request-code'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
]

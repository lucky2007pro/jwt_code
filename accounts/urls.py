from django.urls import path
from .views import (
    SignUpView, xabar, VerifyView, GetNewCode,
    ChangeProfileInfoView, CompleteProfileInfoView, UploadPhotoInfoView,
    LoginView, LogoutView, ProfileView, ProfileUpdateView,
    ResetPasswordView, ForgotPasswordView, ChangePasswordView,
)

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('verify/', VerifyView.as_view(), name='verify'),
    path('new-code/', GetNewCode.as_view(), name='new_code'),
    path('change-profile-info/', ChangeProfileInfoView.as_view(), name='change-profile-info'),
    path('complete-profile/', CompleteProfileInfoView.as_view(), name='complete-profile'),
    path('upload-photo/', UploadPhotoInfoView.as_view(), name='upload-photo'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('xabar/', xabar, name='xabar'),
]
from django.urls import path
from .views import SignUpView, xabar, VerifyView, GetNewCode, ChangeProfileInfoView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('xabar/', xabar, name='xabar'),
    path('verify/', VerifyView.as_view(), name='verify'),
    path('new-code/', GetNewCode.as_view(), name='new_code'),
    path('change-profile/', ChangeProfileInfoView.as_view(), name='change_profile'),
]
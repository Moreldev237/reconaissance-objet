from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    ForgotPasswordView,
    VerifyOTPView,
    ResetPasswordView,
    UserView,
    LogoutView
)

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('forgot-password', ForgotPasswordView.as_view(), name='forgot_password'),
    path('verify-otp', VerifyOTPView.as_view(), name='verify_otp'),
    path('reset-password', ResetPasswordView.as_view(), name='reset_password'),
    path('user', UserView.as_view(), name='user'),
]
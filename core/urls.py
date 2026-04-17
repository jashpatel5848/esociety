from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.userSignupView, name='signup'),
    path('login/',views.userLoginView,name='login'),
    path('logout/',views.userLogoutView,name='logout'),
    path('profile/', views.userProfileView, name='profile'),
    path('password-change/', views.changePasswordView, name='change_password'),
    
    # Forgot Password Flow
    path('forgot-password/', views.forgotPasswordView, name='forgot_password'),
    path('verify-reset-otp/', views.verifyResetOtpView, name='verify_reset_otp'),
    path('reset-password/', views.resetPasswordView, name='reset_password'),
]
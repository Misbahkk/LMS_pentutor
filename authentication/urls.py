from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    UserLogoutView,
    EmailVerificationView,
    AdminUserListView,
    AdminRoleUpdateView,
    ResendVerificationEmailView
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('verify-email/<str:token>/', EmailVerificationView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/<uuid:user_id>/role/', AdminRoleUpdateView.as_view(), name='admin-role-update'),
]

# authenticate/view.py

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import get_object_or_404
from .models import User
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserSerializer,
    RoleUpdateSerializer
)

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate verification token
            verification_token = get_random_string(50)
            user.verification_token = verification_token
            user.save()
            
            # Send verification email
            self.send_verification_email(user, verification_token)
            
            return Response({
                'success': True,
                'message': 'Registration successful! Please check your email for verification.',
                'data': {
                    'user_id': user.id,
                    'email': user.email,
                    'username': user.username
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Registration failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def send_verification_email(self, user, token):
        subject = 'Verify Your Email - LMS'
        message = f'''
        Hi {user.username},
        
        Thank you for registering with our LMS platform!
        
        Please click the following link to verify your email:
        http://localhost:8000/api/auth/verify-email/{token}/
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        LMS Team
        '''
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception as e:
            print(f"Email sending failed: {e}")

class EmailVerificationView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        try:
            user = User.objects.get(verification_token=token)
            user.is_verified = True
            user.verification_token = None
            user.save()
            
            return Response({
                'success': True,
                'message': 'Email verified successfully! You can now login.'
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid or expired verification token.'
            }, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'data': {
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'user': UserSerializer(user).data
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Login failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Profile update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'success': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Logout failed'
            }, status=status.HTTP_400_BAD_REQUEST)

class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Check if user is admin or subadmin
        if request.user.role not in ['admin', 'subadmin']:
            return Response({
                'success': False,
                'message': 'Access denied. Admin privileges required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        users = User.objects.all()
        role = request.GET.get('role')
        is_verified = request.GET.get('is_verified')

        if role:
            users = users.filter(role=role)

        if is_verified is not None:
            if is_verified.lower() == 'true':
              users = users.filter(is_verified=True)
            elif is_verified.lower() == 'false':
                users = users.filter(is_verified=False)

        serializer = UserSerializer(users, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

class AdminRoleUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, user_id):
        # Check if user is admin
        if request.user.role != 'admin':
            return Response({
                'success': False,
                'message': 'Access denied. Admin privileges required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(id=user_id)
            old_role = user.role
            if old_role == 'teacher':
                return Response({'success': False, 'message': 'Cannot change role of a teacher. alredy role is teacher'}, status=status.HTTP_404_NOT_FOUND)
                                
            serializer = RoleUpdateSerializer(user, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()

                # If role change to teacher then create Teacher object
                new_role = serializer.validated_data.get('role')
                if new_role == 'teacher' and old_role != 'teacher':
                    from courses.models import Teacher
                    Teacher.objects.get_or_create(user=user) 

                
                return Response({
                    'success': True,
                    'message': 'User role updated successfully',
                    'data': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'success': False,
                'message': 'Role update failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'success': False,
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return Response({
                    'success': False,
                    'message': 'Email is already verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate new verification token
            verification_token = get_random_string(50)
            user.verification_token = verification_token
            user.save()
            
            # Send verification email
            self.send_verification_email(user, verification_token)
            
            return Response({
                'success': True,
                'message': 'Verification email sent successfully'
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def send_verification_email(self, user, token):
        subject = 'Verify Your Email - LMS'
        message = f'''
        Hi {user.username},
        
        Please click the following link to verify your email:
        http://localhost:8000/api/auth/verify-email/{token}/
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        LMS Team
        '''
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception as e:
            print(f"Email sending failed: {e}")
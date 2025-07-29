# admin_dashboard/views.py

from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from django.db import models

from authentication.models import User
from authentication.serializers import UserSerializer
from courses.models import Course, Teacher, Enrollment
from courses.serializers import CourseListSerializer
from payments.models import Payment


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard_overview(request):
    """
    Admin dashboard overview with statistics
    """
    # Check if user is admin
    if request.user.role != 'admin':
        return Response({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get statistics
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_teachers = User.objects.filter(role='teacher').count()
    total_admins = User.objects.filter(role='admin').count()
    total_subadmins = User.objects.filter(role='subadmin').count()
    
    # Course statistics
    total_courses = Course.objects.count()
    active_courses = Course.objects.filter(is_active=True).count()
    paid_courses = Course.objects.filter(course_type='paid').count()
    free_courses = Course.objects.filter(course_type='free').count()
    
    # Payment statistics
    total_payments = Payment.objects.count()
    successful_payments = Payment.objects.filter(is_successful=True).count()
    total_revenue = Payment.objects.filter(is_successful=True).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Recent activity
    recent_users = User.objects.order_by('-created_at')[:5]
    recent_courses = Course.objects.order_by('-created_at')[:5]
    recent_payments = Payment.objects.filter(is_successful=True).order_by('-created_at')[:5]
    
    return Response({
        'success': True,
        'data': {
            'user_statistics': {
                'total_users': total_users,
                'total_students': total_students,
                'total_teachers': total_teachers,
                'total_admins': total_admins,
                'total_subadmins': total_subadmins
            },
            'course_statistics': {
                'total_courses': total_courses,
                'active_courses': active_courses,
                'paid_courses': paid_courses,
                'free_courses': free_courses
            },
            'payment_statistics': {
                'total_payments': total_payments,
                'successful_payments': successful_payments,
                'total_revenue': float(total_revenue)
            },
            'recent_activity': {
                'recent_users': UserSerializer(recent_users, many=True).data,
                'recent_courses': CourseListSerializer(recent_courses, many=True).data,
                'recent_payments': [
                    {
                        'id': payment.id,
                        'user': payment.user.username,
                        'amount': float(payment.amount),
                        'gateway': payment.gateway,
                        'created_at': payment.created_at
                    } for payment in recent_payments
                ]
            }
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_users_list(request):
    """
    Get all users with filtering and role information
    """
    if request.user.role not in ['admin', 'subadmin']:
        return Response({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get query parameters
    role_filter = request.query_params.get('role', None)
    search = request.query_params.get('search', None)
    is_verified = request.query_params.get('is_verified', None)
    
    # Base queryset
    users = User.objects.all().order_by('-created_at')
    
    # Apply filters
    if role_filter:
        users = users.filter(role=role_filter)
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if is_verified is not None:
        users = users.filter(is_verified=is_verified.lower() == 'true')
    
    # Serialize users
    serializer = UserSerializer(users, many=True)
    
    return Response({
        'success': True,
        'data': {
            'total_users': users.count(),
            'users': serializer.data
        }
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def admin_update_user_role(request, user_id):
    """
    Update user role (Admin only)
    """
    if request.user.role != 'admin':
        return Response({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        new_role = request.data.get('role')
        
        if new_role not in ['student', 'teacher', 'admin', 'subadmin']:
            return Response({
                'success': False,
                'message': 'Invalid role specified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.role = new_role
        user.save()
        
        return Response({
            'success': True,
            'message': f'User role updated to {new_role}',
            'data': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_teachers_courses(request):
    """
    Get all teachers with their courses
    """
    if request.user.role not in ['admin', 'subadmin']:
        return Response({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all teachers
    teachers = Teacher.objects.select_related('user').prefetch_related('course_set')
    
    teachers_data = []
    for teacher in teachers:
        courses = Course.objects.filter(teacher=teacher)
        teacher_info = {
            'id': teacher.id,
            'user_id': teacher.user.id,
            'username': teacher.user.username,
            'email': teacher.user.email,
            'bio': teacher.bio,
            'is_verified': teacher.user.is_verified,
            'created_at': teacher.user.created_at,
            'courses': {
                'total_courses': courses.count(),
                'active_courses': courses.filter(is_active=True).count(),
                'paid_courses': courses.filter(course_type='paid').count(),
                'free_courses': courses.filter(course_type='free').count(),
                'course_list': CourseListSerializer(courses, many=True).data
            }
        }
        teachers_data.append(teacher_info)
    
    return Response({
        'success': True,
        'data': {
            'total_teachers': len(teachers_data),
            'teachers': teachers_data
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_course_payments(request):
    """
    Get all course payments with student and course details
    """
    if request.user.role not in ['admin', 'subadmin']:
        return Response({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get query parameters
    course_id = request.query_params.get('course_id', None)
    payment_status = request.query_params.get('status', None)
    gateway = request.query_params.get('gateway', None)
    
    # Base queryset
    payments = Payment.objects.select_related('user', 'course').order_by('-created_at')
    
    # Apply filters
    if course_id:
        payments = payments.filter(course__id=course_id)
    
    if payment_status:
        is_successful = payment_status.lower() == 'successful'
        payments = payments.filter(is_successful=is_successful)
    
    if gateway:
        payments = payments.filter(gateway=gateway)
    
    # Serialize payments
    payment_data = []
    for payment in payments:
        payment_info = {
            'id': payment.id,
            'transaction_ref': payment.txn_ref,
            'amount': float(payment.amount),
            'gateway': payment.gateway,
            'is_successful': payment.is_successful,
            'created_at': payment.created_at,
            'student': {
                'id': payment.user.id,
                'username': payment.user.username,
                'email': payment.user.email
            },
            'course': {
                'id': payment.meeting.id,
                'title': getattr(payment.meeting, 'title', 'N/A')
            }
        }
        payment_data.append(payment_info)
    
    # Payment summary
    total_amount = sum(p.amount for p in payments if p.is_successful)
    successful_count = payments.filter(is_successful=True).count()
    failed_count = payments.filter(is_successful=False).count()
    
    return Response({
        'success': True,
        'data': {
            'summary': {
                'total_payments': payments.count(),
                'successful_payments': successful_count,
                'failed_payments': failed_count,
                'total_revenue': float(total_amount)
            },
            'payments': payment_data
        }
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def admin_verify_payment(request, payment_id):
    """
    Verify/Update payment status (Admin only)
    """
    if request.user.role != 'admin':
        return Response({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        payment = Payment.objects.get(id=payment_id)
        is_successful = request.data.get('is_successful', payment.is_successful)
        
        payment.is_successful = is_successful
        payment.save()
        
        return Response({
            'success': True,
            'message': f'Payment {"verified" if is_successful else "marked as failed"}',
            'data': {
                'payment_id': payment.id,
                'is_successful': payment.is_successful,
                'amount': float(payment.amount)
            }
        }, status=status.HTTP_200_OK)
        
    except Payment.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Payment not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_course_enrollments(request):
    """
    Get all course enrollments with student details
    """
    if request.user.role not in ['admin', 'subadmin']:
        return Response({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get query parameters
    course_id = request.query_params.get('course_id', None)
    
    # Base queryset
    enrollments = Enrollment.objects.select_related('course').order_by('-enrolled_at')
    
    if course_id:
        enrollments = enrollments.filter(course_id=course_id)
    
    # Serialize enrollments
    enrollment_data = []
    for enrollment in enrollments:
        enrollment_info = {
            'id': enrollment.id,
            'enrolled_at': enrollment.enrolled_at,
            'is_completed': enrollment.is_completed,
            'course': {
                'id': enrollment.course.id,
                'title': enrollment.course.title,
                'course_type': enrollment.course.course_type,
                'price': float(enrollment.course.price)
            }
        }
        enrollment_data.append(enrollment_info)
    
    return Response({
        'success': True,
        'data': {
            'total_enrollments': enrollments.count(),
            'enrollments': enrollment_data
        }
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def admin_delete_user(request, user_id):
    """
    Delete user (Admin only)
    """
    if request.user.role != 'admin':
        return Response({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        
        # Prevent admin from deleting themselves
        if user.id == request.user.id:
            return Response({
                'success': False,
                'message': 'Cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        username = user.username
        user.delete()
        
        return Response({
            'success': True,
            'message': f'User {username} deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_user_detail(request, user_id):
    """
    Get detailed information about a specific user
    """
    if request.user.role not in ['admin', 'subadmin']:
        return Response({
            'success': False,
            'message': 'Access denied. Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        
        # Get user's additional information based on role
        additional_info = {}
        
        if user.role == 'teacher':
            try:
                teacher = Teacher.objects.get(user=user)
                courses = Course.objects.filter(teacher=teacher)
                additional_info = {
                    'teacher_profile': {
                        'bio': teacher.bio,
                        'total_courses': courses.count(),
                        'active_courses': courses.filter(is_active=True).count()
                    }
                }
            except Teacher.DoesNotExist:
                additional_info = {'teacher_profile': None}
        
        elif user.role == 'student':
            enrollments = Enrollment.objects.filter(course__in=Course.objects.all())
            payments = Payment.objects.filter(user=user)
            additional_info = {
                'student_profile': {
                    'total_enrollments': enrollments.count(),
                    'completed_courses': enrollments.filter(is_completed=True).count(),
                    'total_payments': payments.filter(is_successful=True).count(),
                    'total_spent': float(payments.filter(is_successful=True).aggregate(
                        total=Sum('amount'))['total'] or 0)
                }
            }
        
        user_data = UserSerializer(user).data
        user_data.update(additional_info)
        
        return Response({
            'success': True,
            'data': user_data
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    







# support_feedback/views.py
from support_feedback.models import SupportTicket, CourseFeedback, TeacherFeedback
from support_feedback.serializers import (
    SupportTicketSerializer,
    CourseFeedbackSerializer, TeacherFeedbackSerializer,
     TicketReplyCreateSerializer
)
    
# Admin Views (for admin dashboard app)
class AdminSupportTicketListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = SupportTicketSerializer
    queryset = SupportTicket.objects.all()

class AdminSupportTicketDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAdminUser] 
    serializer_class = SupportTicketSerializer
    queryset = SupportTicket.objects.all()

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_reply_ticket(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    serializer = TicketReplyCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save(ticket=ticket, user=request.user, is_admin_reply=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminCourseFeedbackListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = CourseFeedbackSerializer
    queryset = CourseFeedback.objects.all()

class AdminTeacherFeedbackListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = TeacherFeedbackSerializer  
    queryset = TeacherFeedback.objects.all()
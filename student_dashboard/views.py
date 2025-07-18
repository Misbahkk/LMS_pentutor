# student_dashboard/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone

from courses.models import Course, Video, Quiz, Assignment, Enrollment, Progress
from courses.serializers import CourseListSerializer, CourseDetailSerializer
from payments.models import Payment


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_dashboard(request):
    """
    Student dashboard overview
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    student = request.user
    
    # Get student's enrollments
    enrollments = Enrollment.objects.filter(student=student)
    total_enrollments = enrollments.count()
    completed_courses = enrollments.filter(is_completed=True).count()
    in_progress_courses = enrollments.filter(is_completed=False).count()
    
    # Get payment statistics
    payments = Payment.objects.filter(user=student, is_successful=True)
    total_spent = payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get recent activities
    recent_enrollments = enrollments.order_by('-enrolled_at')[:5]
    recent_progress = Progress.objects.filter(student=student).order_by('-completed_at')[:10]
    
    # Available courses (not enrolled)
    enrolled_course_ids = enrollments.values_list('course_id', flat=True)
    available_courses = Course.objects.filter(
        is_active=True
    ).exclude(id__in=enrolled_course_ids)[:6]
    
    return Response({
        'success': True,
        'data': {
            'student_name': student.username,
            'student_email': student.email,
            'statistics': {
                'total_enrollments': total_enrollments,
                'completed_courses': completed_courses,
                'in_progress_courses': in_progress_courses,
                'total_spent': float(total_spent)
            },
            'recent_enrollments': [{
                'id': enrollment.id,
                'course': {
                    'id': enrollment.course.id,
                    'title': enrollment.course.title,
                    'course_type': enrollment.course.course_type,
                    'price': float(enrollment.course.price)
                },
                'enrolled_at': enrollment.enrolled_at,
                'is_completed': enrollment.is_completed
            } for enrollment in recent_enrollments],
            'available_courses': CourseListSerializer(available_courses, many=True).data
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_enrolled_courses(request):
    """
    Get all courses the student is enrolled in
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    student = request.user
    enrollments = Enrollment.objects.filter(student=student).select_related('course')
    
    courses_data = []
    for enrollment in enrollments:
        course = enrollment.course
        
        # Calculate progress
        total_items = (
            course.videos.count() + 
            course.quizzes.count() + 
            course.assignments.count()
        )
        
        completed_items = Progress.objects.filter(
            student=student,
            course=course
        ).count()
        
        progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
        
        # Get payment status
        payment_status = 'free'
        if course.course_type == 'paid':
            payment = Payment.objects.filter(
                user=student,
                course=course.id,  # Assuming meeting_id maps to course_id
                is_successful=True
            ).first()
            payment_status = 'paid' if payment else 'pending'
        
        course_data = {
            'enrollment_id': enrollment.id,
            'course': CourseDetailSerializer(course).data,
            'enrolled_at': enrollment.enrolled_at,
            'is_completed': enrollment.is_completed,
            'progress_percentage': round(progress_percentage, 2),
            'completed_items': completed_items,
            'total_items': total_items,
            'payment_status': payment_status
        }
        courses_data.append(course_data)
    
    return Response({
        'success': True,
        'data': {
            'total_enrolled': len(courses_data),
            'courses': courses_data
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll_in_course(request, course_id):
    """
    Enroll student in a course
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    student = request.user
    
    try:
        course = Course.objects.get(id=course_id, is_active=True)
        
        # Check if already enrolled
        existing_enrollment = Enrollment.objects.filter(
            student=student,
            course=course
        ).first()
        
        if existing_enrollment:
            return Response({
                'success': False,
                'message': 'Already enrolled in this course'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # For paid courses, check payment status
        if course.course_type == 'paid':
            payment = Payment.objects.filter(
                user=student,
                course=course.id,
                is_successful=True
            ).first()
            
            if not payment:
                return Response({
                    'success': False,
                    'message': 'Payment required for this course'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create enrollment
        enrollment = Enrollment.objects.create(
            student=student,
            course=course
        )
        
        return Response({
            'success': True,
            'message': 'Successfully enrolled in course',
            'data': {
                'enrollment_id': enrollment.id,
                'course_title': course.title,
                'enrolled_at': enrollment.enrolled_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Course.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Course not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_course_progress(request, course_id):
    """
    Get detailed progress for a specific course
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    student = request.user
    
    try:
        course = Course.objects.get(id=course_id, is_active=True)
        
        # Check if student is enrolled
        enrollment = Enrollment.objects.filter(
            student=student,
            course=course
        ).first()
        
        if not enrollment:
            return Response({
                'success': False,
                'message': 'Not enrolled in this course'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get progress data
        progress_records = Progress.objects.filter(
            student=student,
            course=course
        )
        
        # Videos progress
        videos = course.videos.all()
        completed_videos = progress_records.filter(video__isnull=False).values_list('video_id', flat=True)
        
        videos_data = []
        for video in videos:
            videos_data.append({
                'id': video.id,
                'title': video.title,
                'duration': video.duration,
                'order': video.order,
                'completed': video.id in completed_videos
            })
        
        # Quizzes progress
        quizzes = course.quizzes.all()
        completed_quizzes = progress_records.filter(quiz__isnull=False).values_list('quiz_id', flat=True)
        
        quizzes_data = []
        for quiz in quizzes:
            quizzes_data.append({
                'id': quiz.id,
                'title': quiz.title,
                'passing_score': quiz.passing_score,
                'completed': quiz.id in completed_quizzes
            })
        
        # Assignments progress
        assignments = course.assignments.all()
        completed_assignments = progress_records.filter(assignment__isnull=False).values_list('assignment_id', flat=True)
        
        assignments_data = []
        for assignment in assignments:
            assignments_data.append({
                'id': assignment.id,
                'title': assignment.title,
                'due_date': assignment.due_date,
                'completed': assignment.id in completed_assignments
            })
        
        # Calculate overall progress
        total_items = len(videos_data) + len(quizzes_data) + len(assignments_data)
        completed_items = len(completed_videos) + len(completed_quizzes) + len(completed_assignments)
        progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
        
        return Response({
            'success': True,
            'data': {
                'course': {
                    'id': course.id,
                    'title': course.title,
                    'description': course.description
                },
                'enrollment': {
                    'enrolled_at': enrollment.enrolled_at,
                    'is_completed': enrollment.is_completed
                },
                'progress': {
                    'percentage': round(progress_percentage, 2),
                    'completed_items': completed_items,
                    'total_items': total_items
                },
                'videos': {
                    'total': len(videos_data),
                    'completed': len(completed_videos),
                    'pending': len(videos_data) - len(completed_videos),
                    'list': videos_data
                },
                'quizzes': {
                    'total': len(quizzes_data),
                    'completed': len(completed_quizzes),
                    'pending': len(quizzes_data) - len(completed_quizzes),
                    'list': quizzes_data
                },
                'assignments': {
                    'total': len(assignments_data),
                    'completed': len(completed_assignments),
                    'pending': len(assignments_data) - len(completed_assignments),
                    'list': assignments_data
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Course not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_video_completed(request, video_id):
    """
    Mark a video as completed
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    student = request.user
    
    try:
        video = Video.objects.get(id=video_id)
        
        # Check if student is enrolled in the course
        enrollment = Enrollment.objects.filter(
            student=student,
            course=video.course
        ).first()
        
        if not enrollment:
            return Response({
                'success': False,
                'message': 'Not enrolled in this course'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark video as completed
        progress, created = Progress.objects.get_or_create(
            student=student,
            course=video.course,
            video=video,
            defaults={'completed_at': timezone.now()}
        )
        
        if created:
            return Response({
                'success': True,
                'message': 'Video marked as completed'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': True,
                'message': 'Video already marked as completed'
            }, status=status.HTTP_200_OK)
            
    except Video.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Video not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_quiz_completed(request, quiz_id):
    """
    Mark a quiz as completed
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    student = request.user
    
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        
        # Check if student is enrolled in the course
        enrollment = Enrollment.objects.filter(
            student=student,
            course=quiz.course
        ).first()
        
        if not enrollment:
            return Response({
                'success': False,
                'message': 'Not enrolled in this course'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark quiz as completed
        progress, created = Progress.objects.get_or_create(
            student=student,
            course=quiz.course,
            quiz=quiz,
            defaults={'completed_at': timezone.now()}
        )
        
        if created:
            return Response({
                'success': True,
                'message': 'Quiz marked as completed'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': True,
                'message': 'Quiz already marked as completed'
            }, status=status.HTTP_200_OK)
            
    except Quiz.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Quiz not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_payment_history(request):
    """
    Get student's payment history with course details
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)

    student = request.user
    payments = Payment.objects.filter(user=student).order_by('-created_at')

    payment_data = []
    for payment in payments:
        course_info = {
            'id': payment.course.id if payment.course else None,
            'title': payment.course.title if payment.course else 'Course not found',
            'price': float(payment.course.price) if payment.course else 0
        }

        payment_info = {
            'id': payment.id,
            'txn_ref': payment.txn_ref,
            'amount': float(payment.amount),
            'gateway': payment.gateway,
            'is_successful': payment.is_successful,
            'created_at': payment.created_at,
            'course': course_info
        }
        payment_data.append(payment_info)

    total_payments = payments.count()
    successful_payments = payments.filter(is_successful=True).count()
    total_spent = payments.filter(is_successful=True).aggregate(total=Sum('amount'))['total'] or 0

    return Response({
        'success': True,
        'data': {
            'summary': {
                'total_payments': total_payments,
                'successful_payments': successful_payments,
                'failed_payments': total_payments - successful_payments,
                'total_spent': float(total_spent)
            },
            'payments': payment_data
        }
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_courses(request):
    """
    Get courses available for enrollment (not enrolled by student)
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    student = request.user
    
    # Get enrolled course IDs
    enrolled_course_ids = Enrollment.objects.filter(
        student=student
    ).values_list('course_id', flat=True)
    
    # Get available courses
    available_courses = Course.objects.filter(
        is_active=True
    ).exclude(id__in=enrolled_course_ids)
    
    # Apply filters
    course_type = request.query_params.get('type', None)
    if course_type:
        available_courses = available_courses.filter(course_type=course_type)
    
    search = request.query_params.get('search', None)
    if search:
        available_courses = available_courses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(teacher__user__username__icontains=search)
        )
    
    serializer = CourseListSerializer(available_courses, many=True)
    
    return Response({
        'success': True,
        'data': {
            'total_available': available_courses.count(),
            'courses': serializer.data
        }
    }, status=status.HTTP_200_OK)
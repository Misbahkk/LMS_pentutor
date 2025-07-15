# teacher_dashboard/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from courses.models import Course, Video, Quiz, Assignment, Enrollment, Teacher
from courses.serializers import CourseListSerializer, VideoDetailSerializer, QuizSerializer, AssignmentSerializer
from .serializers import TeacherCourseSerializer, TeacherVideoSerializer, TeacherQuizSerializer, EnrolledStudentSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_dashboard(request):
    """
    Teacher dashboard overview
    """
    # Check if user is teacher
    if request.user.role != 'teacher':
        return Response({
            'success': False,
            'message': 'Access denied. Teacher privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Teacher profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get teacher's courses statistics
    courses = Course.objects.filter(teacher=teacher)
    total_courses = courses.count()
    active_courses = courses.filter(is_active=True).count()
    total_students = Enrollment.objects.filter(course__teacher=teacher).count()
    total_videos = Video.objects.filter(course__teacher=teacher).count()
    total_quizzes = Quiz.objects.filter(course__teacher=teacher).count()
    
    # Recent courses
    recent_courses = courses.order_by('-created_at')[:5]
    
    return Response({
        'success': True,
        'data': {
            'teacher_name': teacher.user.username,
            'teacher_bio': teacher.bio,
            'statistics': {
                'total_courses': total_courses,
                'active_courses': active_courses,
                'total_students': total_students,
                'total_videos': total_videos,
                'total_quizzes': total_quizzes
            },
            'recent_courses': CourseListSerializer(recent_courses, many=True).data
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def teacher_courses(request):
    """
    Get teacher's courses or create new course
    """
    if request.user.role != 'teacher':
        return Response({
            'success': False,
            'message': 'Access denied. Teacher privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Teacher profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        courses = Course.objects.filter(teacher=teacher).order_by('-created_at')
        serializer = TeacherCourseSerializer(courses, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = TeacherCourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(teacher=teacher)
            return Response({
                'success': True,
                'message': 'Course created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Course creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def teacher_course_detail(request, course_id):
    """
    Get, update or delete teacher's specific course
    """
    if request.user.role != 'teacher':
        return Response({
            'success': False,
            'message': 'Access denied. Teacher privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        teacher = Teacher.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, teacher=teacher)
    except Teacher.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Teacher profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Course.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Course not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = TeacherCourseSerializer(course)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = TeacherCourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Course updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Course update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        course.delete()
        return Response({
            'success': True,
            'message': 'Course deleted successfully'
        }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def teacher_course_videos(request, course_id):
    """
    Get course videos or add new video to course
    """
    if request.user.role != 'teacher':
        return Response({
            'success': False,
            'message': 'Access denied. Teacher privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        teacher = Teacher.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, teacher=teacher)
    except Teacher.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Teacher profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Course.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Course not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        videos = Video.objects.filter(course=course).order_by('order')
        serializer = TeacherVideoSerializer(videos, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = TeacherVideoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(course=course)
            return Response({
                'success': True,
                'message': 'Video added successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Video upload failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def teacher_video_detail(request, video_id):
    """
    Get, update or delete specific video
    """
    if request.user.role != 'teacher':
        return Response({
            'success': False,
            'message': 'Access denied. Teacher privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        teacher = Teacher.objects.get(user=request.user)
        video = Video.objects.get(id=video_id, course__teacher=teacher)
    except Teacher.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Teacher profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Video.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Video not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = TeacherVideoSerializer(video)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = TeacherVideoSerializer(video, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Video updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Video update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        video.delete()
        return Response({
            'success': True,
            'message': 'Video deleted successfully'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_course_students(request, course_id):
    """
    Get enrolled students for a specific course
    """
    if request.user.role != 'teacher':
        return Response({
            'success': False,
            'message': 'Access denied. Teacher privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        teacher = Teacher.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, teacher=teacher)
    except Teacher.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Teacher profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Course.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Course not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    enrollments = Enrollment.objects.filter(course=course).order_by('-enrolled_at')
    serializer = EnrolledStudentSerializer(enrollments, many=True)
    
    return Response({
        'success': True,
        'data': {
            'course_title': course.title,
            'total_students': enrollments.count(),
            'students': serializer.data
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def teacher_course_quizzes(request, course_id):
    """
    Get course quizzes or create new quiz
    """
    if request.user.role != 'teacher':
        return Response({
            'success': False,
            'message': 'Access denied. Teacher privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        teacher = Teacher.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, teacher=teacher)
    except Teacher.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Teacher profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Course.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Course not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        quizzes = Quiz.objects.filter(course=course).order_by('order')
        serializer = TeacherQuizSerializer(quizzes, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = TeacherQuizSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(course=course)
            return Response({
                'success': True,
                'message': 'Quiz created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Quiz creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def teacher_quiz_detail(request, quiz_id):
    """
    Get, update or delete specific quiz
    """
    if request.user.role != 'teacher':
        return Response({
            'success': False,
            'message': 'Access denied. Teacher privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        teacher = Teacher.objects.get(user=request.user)
        quiz = Quiz.objects.get(id=quiz_id, course__teacher=teacher)
    except Teacher.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Teacher profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Quiz.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Quiz not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = TeacherQuizSerializer(quiz)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = TeacherQuizSerializer(quiz, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Quiz updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Quiz update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        quiz.delete()
        return Response({
            'success': True,
            'message': 'Quiz deleted successfully'
        }, status=status.HTTP_200_OK)
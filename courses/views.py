# courses/views.py

from rest_framework import status, filters
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from authentication import models
from .models import Course, Video, Quiz, Assignment, Enrollment, Progress
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, VideoDetailSerializer,
    QuizSerializer, AssignmentSerializer, EnrollmentSerializer, ProgressSerializer
)
from django.utils import timezone

class CourseListView(ListAPIView):
    """
    Course listing with filtering and search functionality
    """
    serializer_class = CourseListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course_type', 'teacher', 'is_active']
    search_fields = ['title', 'description', 'teacher__user__username']
    ordering_fields = ['created_at', 'title', 'price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Course.objects.filter(is_active=True).select_related('teacher__user')
        
        # Additional filtering by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
            
        return queryset


@api_view(['GET'])
def course_detail(request, course_id):
    """
    Get detailed information about a specific course
    """
    try:
        course = Course.objects.select_related('teacher__user').prefetch_related(
            'videos', 'quizzes', 'assignments'
        ).get(id=course_id, is_active=True)
        
        serializer = CourseDetailSerializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def video_detail(request, video_id):
    """
    Get detailed information about a specific video with related quizzes and assignments
    """
    try:
        video = Video.objects.select_related('course').prefetch_related(
            'quizzes', 'assignments'
        ).get(id=video_id)
        
        serializer = VideoDetailSerializer(video)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Video.DoesNotExist:
        return Response(
            {'error': 'Video not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def course_videos(request, course_id):
    """
    Get all videos for a specific course (for sidebar playlist)
    """
    try:
        course = Course.objects.get(id=course_id, is_active=True)
        videos = Video.objects.filter(course=course).order_by('order')
        
        # Add progress information for each video (you can expand this later)
        video_data = []
        for video in videos:
            video_info = {
                'id': video.id,
                'title': video.title,
                'duration': video.duration,
                'order': video.order,
                'has_quiz': video.quizzes.exists(),
                'has_assignment': video.assignments.exists(),
                'completed': False  # You can add logic to check completion status
            }
            video_data.append(video_info)
        
        return Response({
            'course_id': course_id,
            'course_title': course.title,
            'videos': video_data
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def video_quiz_assignments(request, video_id):
    """
    Get quizzes and assignments for a specific video
    """
    try:
        video = Video.objects.get(id=video_id)
        
        quizzes = Quiz.objects.filter(video=video).order_by('order')
        assignments = Assignment.objects.filter(video=video).order_by('order')
        
        quiz_serializer = QuizSerializer(quizzes, many=True)
        assignment_serializer = AssignmentSerializer(assignments, many=True)
        
        return Response({
            'video_id': video_id,
            'video_title': video.title,
            'quizzes': quiz_serializer.data,
            'assignments': assignment_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Video.DoesNotExist:
        return Response(
            {'error': 'Video not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Add this decorator
def enroll_course(request, course_id):
    """
    Enroll in a course (updated to use authenticated user)
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        course = Course.objects.get(id=course_id, is_active=True)
        
        # Check if already enrolled
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,  # Use authenticated user
            course=course,
            defaults={'is_completed': False}
        )
        
        if created:
            return Response(
                {'message': 'Successfully enrolled in course', 'enrollment_id': enrollment.id},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Already enrolled in this course'},
                status=status.HTTP_200_OK
            )
            
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Add this decorator
def mark_video_complete(request, video_id):
    """
    Mark a video as completed (updated to use authenticated user)
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        video = Video.objects.get(id=video_id)
        
        # Create progress record
        progress, created = Progress.objects.get_or_create(
            student=request.user,  # Use authenticated user
            course=video.course,
            video=video,
            defaults={'completed_at': timezone.now()}
        )
        
        if created:
            return Response(
                {'message': 'Video marked as completed'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Video already marked as completed'},
                status=status.HTTP_200_OK
            )
            
    except Video.DoesNotExist:
        return Response(
            {'error': 'Video not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Add this decorator
def mark_quiz_complete(request, quiz_id):
    """
    Mark a quiz as completed (updated to use authenticated user)
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        
        # Create progress record
        progress, created = Progress.objects.get_or_create(
            student=request.user,  # Use authenticated user
            course=quiz.course,
            quiz=quiz,
            defaults={'completed_at': timezone.now()}
        )
        
        if created:
            return Response(
                {'message': 'Quiz marked as completed'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Quiz already marked as completed'},
                status=status.HTTP_200_OK
            )
            
    except Quiz.DoesNotExist:
        return Response(
            {'error': 'Quiz not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Add this decorator
def course_progress(request, course_id):
    """
    Get progress information for a specific course (updated to use authenticated user)
    """
    if request.user.role != 'student':
        return Response({
            'success': False,
            'message': 'Access denied. Student privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        course = Course.objects.get(id=course_id, is_active=True)
        
        # Get all progress records for this course and student
        progress_records = Progress.objects.filter(
            student=request.user,  # Use authenticated user
            course=course
        )
        
        # Calculate progress statistics
        total_videos = course.videos.count()
        total_quizzes = course.quizzes.count()
        total_assignments = course.assignments.count()
        
        completed_videos = progress_records.filter(video__isnull=False).count()
        completed_quizzes = progress_records.filter(quiz__isnull=False).count()
        completed_assignments = progress_records.filter(assignment__isnull=False).count()
        
        total_items = total_videos + total_quizzes + total_assignments
        completed_items = completed_videos + completed_quizzes + completed_assignments
        
        progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
        
        return Response({
            'course_id': course_id,
            'course_title': course.title,
            'progress_percentage': round(progress_percentage, 2),
            'total_videos': total_videos,
            'completed_videos': completed_videos,
            'total_quizzes': total_quizzes,
            'completed_quizzes': completed_quizzes,
            'total_assignments': total_assignments,
            'completed_assignments': completed_assignments,
            'total_items': total_items,
            'completed_items': completed_items
        }, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    


@api_view(['GET'])
def featured_courses(request):
    """
    Get featured courses (you can modify the logic for what makes a course featured)
    """
    # For now, we'll consider courses with most enrollments as featured
    courses = Course.objects.filter(is_active=True).annotate(
        enrollment_count=models.Count('enrollments')
    ).order_by('-enrollment_count')[:6]
    
    serializer = CourseListSerializer(courses, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def search_courses(request):
    """
    Advanced search for courses
    """
    query = request.query_params.get('q', '')
    course_type = request.query_params.get('type', '')
    teacher = request.query_params.get('teacher', '')
    
    courses = Course.objects.filter(is_active=True)
    
    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(teacher__user__username__icontains=query)
        )
    
    if course_type:
        courses = courses.filter(course_type=course_type)
    
    if teacher:
        courses = courses.filter(teacher__user__username__icontains=teacher)
    
    serializer = CourseListSerializer(courses, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
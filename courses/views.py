# courses/views.py

from rest_framework import status, filters
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from rest_framework.permissions import   AllowAny
from django.db.models import Count

from support_feedback.models import CourseFeedback
from django.db.models import Prefetch
from .models import Course, Video, Quiz, Assignment
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, VideoDetailSerializer,
    QuizSerializer, AssignmentSerializer
)

class CourseListView(ListAPIView):
    """
    Course listing with filtering, search, ordering, and featured option
    """
    serializer_class = CourseListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course_type', 'teacher', 'is_active']
    search_fields = ['title', 'description', 'teacher__user__username']
    ordering_fields = ['created_at', 'title', 'price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Course.objects.filter(is_active=True).select_related('teacher__user')
        
        # 🔍 Search by ?q=
        query = self.request.query_params.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(teacher__user__username__icontains=query)
            )

        # 🎯 Filter by price
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # 🌟 Featured courses (most enrolled)
        is_featured = self.request.query_params.get('featured')
        if is_featured == 'true':
            queryset = queryset.annotate(
                enrollment_count=Count('enrollments')
            ).order_by('-enrollment_count')[:6]

        return queryset


@api_view(['GET'])
@permission_classes([AllowAny])
def course_detail(request, course_id):
    """
    Get detailed information about a specific course
    """
    try:
        course = Course.objects.select_related('teacher__user').prefetch_related(
            'videos', 'quizzes', 'assignments', 'reviews'    ).get(id=course_id, is_active=True)
        
        serializer = CourseDetailSerializer(course,context = {'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
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

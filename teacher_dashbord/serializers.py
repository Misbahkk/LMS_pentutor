# teacher_dashboard/serializers.py

from rest_framework import serializers
from courses.models import Course, Video, Quiz, Assignment, Enrollment, Teacher
from django.contrib.auth.models import User


class TeacherCourseSerializer(serializers.ModelSerializer):
    total_videos = serializers.SerializerMethodField()
    total_enrollments = serializers.SerializerMethodField()
    total_quizzes = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'course_type', 
            'thumbnail', 'created_at', 'is_active', 'total_videos', 
            'total_enrollments', 'total_quizzes'
        ]
        read_only_fields = ['id', 'created_at', 'total_videos', 'total_enrollments', 'total_quizzes']
    
    def get_total_videos(self, obj):
        return obj.videos.count()
    
    def get_total_enrollments(self, obj):
        return obj.enrollments.count()
    
    def get_total_quizzes(self, obj):
        return obj.quizzes.count()


class TeacherVideoSerializer(serializers.ModelSerializer):
    has_quiz = serializers.SerializerMethodField()
    has_assignment = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'video_file', 'duration', 
            'order', 'created_at', 'has_quiz', 'has_assignment'
        ]
        read_only_fields = ['id', 'created_at', 'has_quiz', 'has_assignment']
    
    def get_has_quiz(self, obj):
        return obj.quizzes.exists()
    
    def get_has_assignment(self, obj):
        return obj.assignments.exists()


class TeacherQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'passing_score', 'order', 'video'
        ]
        read_only_fields = ['id']


class EnrolledStudentSerializer(serializers.ModelSerializer):
    # student_username = serializers.CharField(source='student.username', read_only=True)
    # student_email = serializers.CharField(source='student.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'course_title', 'enrolled_at', 'is_completed'
            # 'student_username', 'student_email'  # Add these when student model is ready
        ]
        read_only_fields = ['id', 'enrolled_at', 'course_title']


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'due_date', 'order', 'video'
        ]
        read_only_fields = ['id']
from django.urls import path
from . import views

urlpatterns = [
    # Course listing and search
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/featured/', views.featured_courses, name='featured_courses'),
    path('courses/search/', views.search_courses, name='search_courses'),
    
    # Course detail
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/videos/', views.course_videos, name='course_videos'),
    path('courses/<int:course_id>/progress/', views.course_progress, name='course_progress'),
    
    # Video detail
    path('videos/<int:video_id>/', views.video_detail, name='video_detail'),
    path('videos/<int:video_id>/quiz-assignments/', views.video_quiz_assignments, name='video_quiz_assignments'),
    
    # Enrollment
    path('courses/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    
    # Progress tracking
    path('videos/<int:video_id>/complete/', views.mark_video_complete, name='mark_video_complete'),
    path('quizzes/<int:quiz_id>/complete/', views.mark_quiz_complete, name='mark_quiz_complete'),
    # path('assignments/<int:assignment_id>/complete/', views.mark_assignment_complete, name='mark_assignment_complete'),
]
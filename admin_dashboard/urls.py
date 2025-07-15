# admin_dashboard/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Admin Dashboard Overview
    path('overview/', views.admin_dashboard_overview, name='admin_dashboard_overview'),
    
    # User Management
    path('users/', views.admin_users_list, name='admin_users_list'),
    path('users/<uuid:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('users/<uuid:user_id>/update-role/', views.admin_update_user_role, name='admin_update_user_role'),
    path('users/<uuid:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    
    # Teachers and Courses Management
    path('teachers-courses/', views.admin_teachers_courses, name='admin_teachers_courses'),
    
    # Course Enrollments
    path('enrollments/', views.admin_course_enrollments, name='admin_course_enrollments'),
    
    # Payment Management
    path('payments/', views.admin_course_payments, name='admin_course_payments'),
    path('payments/<int:payment_id>/verify/', views.admin_verify_payment, name='admin_verify_payment'),
]
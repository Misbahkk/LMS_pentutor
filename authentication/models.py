# authetication/model.py

from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.conf import settings

class User(AbstractUser):
    USER_ROLES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
        ('subadmin', 'SubAdmin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='student')
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], blank=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    class Meta:
        db_table = 'users'


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    email = models.EmailField(unique=True, null=True,blank=True)
    # Personal Information
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    profile_picture = models.ImageField(upload_to='student_profiles/', null=True, blank=True)

    # Academic Info
    enrollment_number = models.CharField(max_length=100, blank=True, null=True)
    course = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    year = models.IntegerField(blank=True, null=True)
    section = models.CharField(max_length=10, blank=True)
    gpa = models.FloatField(blank=True, null=True)

    # LMS Specific
    attendance_percentage = models.FloatField(default=0.0)
    completed_assignments = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Student: {self.user.email}"




class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile')
    email = models.EmailField(unique=True, null=True,blank=True)
    # Personal Information
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='teacher_profiles/', null=True, blank=True)

    # Professional Info
    employee_id = models.CharField(max_length=100, blank=True, null=True)
    qualification = models.CharField(max_length=200, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    experience_years = models.PositiveIntegerField(default=0)

    # LMS Specific
    total_courses = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Teacher: {self.user.email}"

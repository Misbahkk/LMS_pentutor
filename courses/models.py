# course/model.py

from django.db import models
from authentication.models import User
from django.utils import timezone

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='teacher_pics/', blank=True)
    
    def __str__(self):
        return self.user.username

class Course(models.Model):
    COURSE_TYPES = [
        ('free', 'Free'),
        ('paid', 'Paid'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    course_type = models.CharField(max_length=10, choices=COURSE_TYPES, default='free')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    def get_total_videos(self):
        return self.videos.count()
    
    def get_total_enrollments(self):
        return self.enrollments.count()
    
    def has_user_paid(self, user):

        if self.course_type == 'free':
            return True
        
        from payments.models import Payment
        return Payment.objects.filter(
            user=user,
            course=self,
            is_successful=True
        ).exists()



class Video(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to='course_videos/')
    duration = models.CharField(max_length=10, blank=True)  # Format: "10:30"
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    passing_score = models.IntegerField(default=70)
    order = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)  # Student portal k liye baad me use karenge
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(default=timezone.now)
    is_completed = models.BooleanField(default=False)
    class Meta:
        unique_together = ['student', 'course']  # Prevent duplicate enrollments
    
    def __str__(self):
        return f"{self.student.username} - Enrollment in {self.course.title}"

class Progress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)  # Student portal k liye baad me use karenge
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, null=True, blank=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, null=True, blank=True)
    completed_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['student', 'course', 'video', 'quiz', 'assignment']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
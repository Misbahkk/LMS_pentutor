# authentication/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from courses.models import Teacher, Studentprofile 

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create profile for Teacher or Student when a new user is created
    """
    if created:
        if instance.role == 'teacher':
            Teacher.objects.create(user=instance)
        elif instance.role == 'student':
            StudentProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the profile when user is saved (if exists)
    """
    if instance.role == 'teacher':
        teacher, created = Teacher.objects.get_or_create(user=instance)
        teacher.save()
    elif instance.role == 'student':
        student, created = StudentProfile.objects.get_or_create(user=instance)
        student.save()

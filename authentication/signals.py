# authentication/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from courses.models import Teacher

@receiver(post_save, sender=User)
def create_teacher_profile(sender, instance, created, **kwargs):
    """
    Create Teacher profile when user with role 'teacher' is created
    """
    if created and instance.role == 'teacher':
        Teacher.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_teacher_profile(sender, instance, **kwargs):
    """
    Save Teacher profile when user is saved
    """
    if instance.role == 'teacher':
        teacher, created = Teacher.objects.get_or_create(user=instance)
        teacher.save()
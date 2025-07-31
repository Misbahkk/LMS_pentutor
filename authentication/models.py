# authetication/model.py

from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    class Meta:
        db_table = 'users'

"""
URL configuration for lms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/payments/',include('payments.urls')),
    path('api/meetings/',include('meetings.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/teacher/', include('teacher_dashbord.urls')),
    path('api/students/',include('student_dashboard.urls')),
    path('api/calendar/', include('calendersync.urls')),
    path('api/alerts/', include('alerts.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('', include('email_automation.urls')),
    path('api/feedback/',include('support_feedback.urls')),
    path('api/job-board/', include('job_portal.urls')),
    path('api/chat/', include('chat.urls')),
]


# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
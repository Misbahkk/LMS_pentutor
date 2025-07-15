
from django.urls import path
from . import views

urlpatterns = [
path('<str:room_id>/', views.ChatHistoryView.as_view(), name='chat-history'),
]
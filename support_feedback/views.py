# support_feedback/views.py
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import SupportTicket, CourseFeedback, TeacherFeedback, TicketReply
from .serializers import (
    SupportTicketSerializer, SupportTicketCreateSerializer,
    CourseFeedbackSerializer, TeacherFeedbackSerializer,
    TicketReplySerializer, TicketReplyCreateSerializer
)

# Support Ticket Views
class SupportTicketListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SupportTicketCreateSerializer
        return SupportTicketSerializer
    
    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SupportTicketDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SupportTicketSerializer
    
    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user)

# Course Feedback Views
class CourseFeedbackListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseFeedbackSerializer
    
    def get_queryset(self):
        return CourseFeedback.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Teacher Feedback Views  
class TeacherFeedbackListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeacherFeedbackSerializer
    
    def get_queryset(self):
        return TeacherFeedback.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Ticket Reply View
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_ticket_reply(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    serializer = TicketReplyCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save(ticket=ticket, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

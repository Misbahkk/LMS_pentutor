# meetings/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    MeetingSerializer, ParticipantSerializer, CreateMeetingSerializer,
    JoinMeetingSerializer, SendInviteSerializer, HandleJoinRequestSerializer,
    JoinRequestSerializer, MeetingInviteSerializer
)
from .models import Meeting, Participant, MeetingInvite, JoinRequest
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import random
from authentication.models import User
from django.utils.text import slugify
from django.core.mail import send_mail
from django.conf import settings
from calendersync.utils import create_google_event

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_meeting(request):
    """Create a new meeting with access control"""
    serializer = CreateMeetingSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'errors': serializer.errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    print("Running create_google_event")
    create_google_event(request.user, meeting)
    print("Done create_google_event")
    
    data = serializer.validated_data
    is_password_required = data.get('is_password_required', False)
    
    # Create meeting
    meeting = Meeting.objects.create(
        host=request.user,
        title=data.get('title', f'{request.user.username}\'s Meeting'),
        meeting_type=data.get('meeting_type', 'instant'),
        access_type=data.get('access_type', 'public'),
        scheduled_time=data.get('scheduled_time'),
        max_participants=data.get('max_participants', 100),
        is_waiting_room_enabled=data.get('waiting_room', False),
        allow_participant_share_screen=data.get('allow_screen_share', True),
        allow_participant_unmute=data.get('allow_unmute', True),
        enable_chat=data.get('enable_chat', True),
        enable_reactions=data.get('enable_reactions', True),
          is_password_required=is_password_required
    )
    
    # Set custom password if provided
    if data.get('password'):
        meeting.password = data['password']
        meeting.save()
    
    # Create invites for private meetings
    if meeting.access_type == 'private' and data.get('invites'):
        for email in data['invites']:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None
            
            MeetingInvite.objects.create(
                meeting=meeting,
                email=email,
                user=user,
                invited_by=request.user
            )
    
    # Host automatically joins as participant
    participant = Participant.objects.create(
        meeting=meeting,
        user=request.user,
        role='host'
    )
    
    # Start meeting if instant
    if meeting.meeting_type == 'instant':
        meeting.start_meeting()
    
    return Response({
        'meeting_id': meeting.meeting_id,
        'password': meeting.password,
        'join_url': f'/meeting/join/{meeting.meeting_id}',
        'status': 'created',
        'meeting': MeetingSerializer(meeting).data,
        'participant': ParticipantSerializer(participant).data,
        'message': 'Meeting created successfully'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([])
def join_meeting(request, meeting_id):
    """Join an existing meeting with access control"""
    serializer = JoinMeetingSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'errors': serializer.errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        meeting = Meeting.objects.get(meeting_id=meeting_id)
        
        # Check if meeting exists and is active
        if meeting.status == 'ended':
            return Response({
                'error': 'Meeting has ended'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check password if provided
        password = serializer.validated_data.get('password', '')
        if meeting.password and password != meeting.password:
            return Response({
                'error': 'Invalid meeting password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check max participants
        active_participants = meeting.participants.filter(left_at__isnull=True).count()
        if active_participants >= meeting.max_participants:
            return Response({
                'error': 'Meeting is full'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create user
        name = serializer.validated_data.get('name')
        email = serializer.validated_data.get('email')
        
        if request.user.is_authenticated:
             user = request.user
        else:
            try:
                # Check if user already exists with this email
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Create new user
                username = slugify(name) + str(random.randint(1000, 9999))
                user = User.objects.create_user(
                    username=username,
                    password=User.objects.make_random_password(),
                    email=email
                )

        
        # Check access permissions
        access_granted = False
        
        if meeting.access_type == 'public':
            access_granted = True
        
        elif meeting.access_type == 'private':
            # Check if user is invited
            invite_exists = MeetingInvite.objects.filter(
                meeting=meeting,
                email=email
            ).exists()
            
            if invite_exists or user == meeting.host:
                access_granted = True
            else:
                return Response({
                    'error': 'You are not invited to this private meeting'
                }, status=status.HTTP_403_FORBIDDEN)
        
        elif meeting.access_type == 'approval_required':
            # Check if user is host
            if user == meeting.host:
                access_granted = True
            else:
                # Create or get existing join request
                join_request, created = JoinRequest.objects.get_or_create(
                    meeting=meeting,
                    user=user if request.user.is_authenticated else None,
                    defaults={
                        'guest_name': name,
                        'guest_email': email
                    }
                )
                
                if join_request.status == 'approved':
                    access_granted = True
                elif join_request.status == 'pending':
                    # Notify host about join request
                    notify_host_about_join_request(meeting, join_request)
                    
                    return Response({
                        'status': 'waiting_approval',
                        'message': 'Your join request has been sent to the host. Please wait for approval.',
                        'request_id': join_request.id
                    }, status=status.HTTP_202_ACCEPTED)
                
                elif join_request.status == 'denied':
                    return Response({
                        'error': 'Your join request was denied by the host'
                    }, status=status.HTTP_403_FORBIDDEN)
        
        if not access_granted:
            return Response({
                'error': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if user already in meeting
        participant, created = Participant.objects.get_or_create(
            meeting=meeting,
            user=user,
            defaults={
                'role': 'participant',
                'guest_name': name
            }
        )
        
        if not created and participant.is_active:
            return Response({
                'error': 'You are already in this meeting'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Rejoin if previously left
        if not created:
            participant.left_at = None
            participant.guest_name = name
            participant.save()
        
        # Start meeting if host joins
        if meeting.status == 'waiting' and participant.role == 'host':
            meeting.start_meeting()
        
        # Notify other participants
        notify_participant_joined(meeting_id, participant, user)
        
        return Response({
            'participant': ParticipantSerializer(participant).data,
            'meeting': MeetingSerializer(meeting).data,
            'message': 'Successfully joined meeting'
        }, status=status.HTTP_200_OK)
        
    except Meeting.DoesNotExist:
        return Response({
            'error': 'Meeting not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_join_request(request, meeting_id):
    """Approve or deny join requests (host/co-host only)"""
    serializer = HandleJoinRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        meeting = Meeting.objects.get(meeting_id=meeting_id)
        
        # Check if user is host or co-host
        participant = Participant.objects.get(
            meeting=meeting,
            user=request.user,
            role__in=['host', 'co_host'],
            left_at__isnull=True
        )
        
        request_id = serializer.validated_data['request_id']
        action = serializer.validated_data['action']
        
        join_request = JoinRequest.objects.get(
            id=request_id,
            meeting=meeting,
            status='pending'
        )
        
        if action == 'approve':
            join_request.approve(request.user)
            
            # Notify the requester
            notify_join_request_response(join_request, 'approved')
            
            message = f"Join request from {join_request.display_name} approved"
        
        else:  # deny
            join_request.deny(request.user)
            
            # Notify the requester
            notify_join_request_response(join_request, 'denied')
            
            message = f"Join request from {join_request.display_name} denied"
        
        return Response({
            'message': message,
            'request': JoinRequestSerializer(join_request).data
        }, status=status.HTTP_200_OK)
        
    except Meeting.DoesNotExist:
        return Response({
            'error': 'Meeting not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Participant.DoesNotExist:
        return Response({
            'error': 'Only host or co-host can handle join requests'
        }, status=status.HTTP_403_FORBIDDEN)
    
    except JoinRequest.DoesNotExist:
        return Response({
            'error': 'Join request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_join_requests(request, meeting_id):
    """Get pending join requests for a meeting (host/co-host only)"""
    try:
        meeting = Meeting.objects.get(meeting_id=meeting_id)
        
        # Check if user is host or co-host
        participant = Participant.objects.get(
            meeting=meeting,
            user=request.user,
            role__in=['host', 'co_host'],
            left_at__isnull=True
        )
        
        pending_requests = meeting.join_requests.filter(status='pending')
        
        return Response({
            'requests': JoinRequestSerializer(pending_requests, many=True).data
        }, status=status.HTTP_200_OK)
        
    except Meeting.DoesNotExist:
        return Response({
            'error': 'Meeting not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Participant.DoesNotExist:
        return Response({
            'error': 'Only host or co-host can view join requests'
        }, status=status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_invites(request, meeting_id):
    """Send invites to additional participants"""
    serializer = SendInviteSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        meeting = Meeting.objects.get(meeting_id=meeting_id)
        
        # Check if user is host or co-host
        participant = Participant.objects.get(
            meeting=meeting,
            user=request.user,
            role__in=['host', 'co_host'],
            left_at__isnull=True
        )
        
        emails = serializer.validated_data['emails']
        created_invites = []
        
        for email in emails:
            invite, created = MeetingInvite.objects.get_or_create(
                meeting=meeting,
                email=email,
                defaults={'invited_by': request.user}
            )
            
            if created:
                # Try to link to existing user
                try:
                    user = User.objects.get(email=email)
                    invite.user = user
                    invite.save()
                except User.DoesNotExist:
                    pass
                
                created_invites.append(invite)
                
                # Send email invitation (implement as needed)
                send_meeting_invitation(invite)
        
        return Response({
            'message': f'Sent {len(created_invites)} new invitations',
            'invites': MeetingInviteSerializer(created_invites, many=True).data
        }, status=status.HTTP_200_OK)
        
    except Meeting.DoesNotExist:
        return Response({
            'error': 'Meeting not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Participant.DoesNotExist:
        return Response({
            'error': 'Only host or co-host can send invites'
        }, status=status.HTTP_403_FORBIDDEN)


# Keep existing views with minor modifications
@api_view(['POST'])
@permission_classes([])
def leave_meeting(request, meeting_id):
    """Leave a meeting"""
    guest_name = request.data.get('guest_name', None)
    user = request.user if request.user.is_authenticated else None
    
    try:
        participant = Participant.objects.get(
            meeting__meeting_id=meeting_id,
            user=user,
            left_at__isnull=True
        )
        
        participant.leave_meeting()
        
        # Notify other participants
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'meeting_{meeting_id}',
                {
                    'type': 'participant_left',
                    'participant_id': participant.id,
                    'user': user.username if user else guest_name
                }
            )
        
        return Response({
            'message': 'Successfully left meeting'
        }, status=status.HTTP_200_OK)
        
    except Participant.DoesNotExist:
        return Response({
            'error': 'You are not in this meeting'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_meeting(request, meeting_id):
    """End a meeting (only host can do this)"""
    try:
        participant = Participant.objects.get(
            meeting__meeting_id=meeting_id,
            user=request.user,
            role__in=['host', 'co_host'],
            left_at__isnull=True
        )
        
        meeting = participant.meeting
        meeting.end_meeting()
        
        # Notify all participants
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'meeting_{meeting_id}',
                {
                    'type': 'meeting_ended',
                    'ended_by': request.user.username,
                    'message': 'Meeting has been ended by host'
                }
            )
        
        return Response({
            'message': 'Meeting ended successfully'
        }, status=status.HTTP_200_OK)
        
    except Participant.DoesNotExist:
        return Response({
            'error': 'Only host or co-host can end meeting'
        }, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meeting_participants(request, meeting_id):
    """Get list of all participants in meeting"""
    try:
        meeting = Meeting.objects.get(meeting_id=meeting_id)
        
        # Check if user is in meeting
        user_participant = meeting.participants.filter(
            user=request.user,
            left_at__isnull=True
        ).first()
        
        if not user_participant:
            return Response({
                'error': 'You are not in this meeting'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all active participants
        participants = meeting.participants.filter(left_at__isnull=True)
        
        return Response({
            'participants': ParticipantSerializer(participants, many=True).data
        }, status=status.HTTP_200_OK)
        
    except Meeting.DoesNotExist:
        return Response({
            'error': 'Meeting not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([])
def check_join_request_status(request, meeting_id, request_id):
    """Check status of join request (for polling)"""
    try:
        join_request = JoinRequest.objects.get(
            id=request_id,
            meeting__meeting_id=meeting_id
        )
        
        return Response({
            'status': join_request.status,
            'request': JoinRequestSerializer(join_request).data
        }, status=status.HTTP_200_OK)
        
    except JoinRequest.DoesNotExist:
        return Response({
            'error': 'Join request not found'
        }, status=status.HTTP_404_NOT_FOUND)


# Helper functions
def notify_host_about_join_request(meeting, join_request):
    """Notify host about new join request via WebSocket"""
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'meeting_{meeting.meeting_id}_host',
            {
                'type': 'join_request_received',
                'request': {
                    'id': join_request.id,
                    'name': join_request.guest_name or (join_request.user.get_full_name() if join_request.user else ''),
                    'email': join_request.guest_email,
                    'requested_at': join_request.requested_at.isoformat()
                }
            }
        )


def notify_join_request_response(join_request, response):
    """Notify requester about join request response"""
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'join_request_{join_request.id}',
            {
                'type': 'join_request_response',
                'status': response,
                'message': f'Your join request was {response}'
            }
        )


def notify_participant_joined(meeting_id, participant, user):
    """Notify other participants about new participant"""
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'meeting_{meeting_id}',
            {
                'type': 'participant_joined',
                'participant': {
                    'id': participant.id,
                    'user': user.username,
                    'guest_name': participant.guest_name,
                    'role': participant.role,
                    'joined_at': participant.joined_at.isoformat()
                }
            }
        )


def send_meeting_invitation(invite):
    """Send email invitation (implement based on your email service)"""
    try:
        subject = f'You are invited to join "{invite.meeting.title}"'
        message = f"""
        Hello,
        
        You have been invited to join a meeting:
        
        Meeting: {invite.meeting.title}
        Host: {invite.meeting.host.get_full_name() or invite.meeting.host.username}
        
        Join URL: {settings.FRONTEND_URL}/meeting/join/{invite.meeting.meeting_id}
        Password: {invite.meeting.password if invite.meeting.password else 'No password required'}
        
        Best regards,
        Meeting Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [invite.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email invitation: {e}")
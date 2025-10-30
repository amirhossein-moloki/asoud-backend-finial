"""
Advanced Chat and Support Services for ASOUD Platform
Comprehensive chat system with real-time messaging, file sharing, and support tickets
"""

import logging
import time
import os
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Count, Avg, Max
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from .models import (
    ChatRoom, ChatParticipant, ChatMessage, ChatMessageRead,
    SupportTicket, ChatAnalytics
)

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatService:
    """
    Main chat service for handling all chat operations
    """
    
    def __init__(self):
        self.max_file_size = getattr(settings, 'CHAT_MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB
        self.allowed_file_types = getattr(settings, 'CHAT_ALLOWED_FILE_TYPES', [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'audio/mpeg', 'audio/wav', 'video/mp4', 'video/avi'
        ])
    
    def create_chat_room(
        self,
        name: str,
        room_type: str = ChatRoom.PRIVATE,
        description: str = '',
        created_by: User = None,
        participants: List[User] = None,
        content_object=None,
        **kwargs
    ) -> ChatRoom:
        """
        Create a new chat room
        
        Args:
            name: Room name
            room_type: Type of room (private, group, support, market)
            description: Room description
            created_by: User who created the room
            participants: List of participants
            content_object: Related object (e.g., Market, Order)
            **kwargs: Additional room settings
            
        Returns:
            ChatRoom: Created chat room
        """
        try:
            with transaction.atomic():
                # Create chat room
                chat_room = ChatRoom.objects.create(
                    name=name,
                    room_type=room_type,
                    description=description,
                    created_by=created_by,
                    content_object=content_object,
                    **kwargs
                )
                
                # Add creator as admin
                if created_by:
                    ChatParticipant.objects.create(
                        chat_room=chat_room,
                        user=created_by,
                        role=ChatParticipant.ADMIN,
                        can_manage_room=True,
                        can_invite_users=True
                    )
                
                # Add participants
                if participants:
                    for participant in participants:
                        if participant != created_by:  # Don't add creator twice
                            ChatParticipant.objects.create(
                                chat_room=chat_room,
                                user=participant,
                                role=ChatParticipant.MEMBER
                            )
                
                # Initialize analytics
                ChatAnalytics.objects.create(chat_room=chat_room)
                
                logger.info(f"Created chat room {chat_room.id} of type {room_type}")
                return chat_room
                
        except Exception as e:
            logger.error(f"Error creating chat room: {e}")
            raise
    
    def send_message(
        self,
        chat_room: ChatRoom,
        sender: User,
        content: str,
        message_type: str = ChatMessage.TEXT,
        file=None,
        reply_to: ChatMessage = None,
        **kwargs
    ) -> ChatMessage:
        """
        Send a message to a chat room
        
        Args:
            chat_room: Target chat room
            sender: Message sender
            content: Message content
            message_type: Type of message (text, image, file, etc.)
            file: File attachment
            reply_to: Message being replied to
            **kwargs: Additional message data
            
        Returns:
            ChatMessage: Created message
        """
        try:
            # Check if user is participant
            if not chat_room.is_participant(sender):
                raise ValidationError("User is not a participant in this chat room")
            
            # Check participant permissions
            participant = ChatParticipant.objects.get(
                chat_room=chat_room,
                user=sender
            )
            
            if not participant.can_send_messages:
                raise ValidationError("User is not allowed to send messages")
            
            # Validate file if provided
            file_data = None
            if file and message_type in [ChatMessage.IMAGE, ChatMessage.FILE, ChatMessage.AUDIO, ChatMessage.VIDEO]:
                file_data = self._validate_and_process_file(file)
            
            with transaction.atomic():
                # Create message
                message = ChatMessage.objects.create(
                    chat_room=chat_room,
                    sender=sender,
                    content=content,
                    message_type=message_type,
                    reply_to=reply_to,
                    file=file_data['file'] if file_data else None,
                    file_name=file_data['file_name'] if file_data else None,
                    file_size=file_data['file_size'] if file_data else None,
                    file_type=file_data['file_type'] if file_data else None,
                    **kwargs
                )
                
                # Update room last message time
                chat_room.last_message_at = timezone.now()
                chat_room.update_last_activity()
                chat_room.save(update_fields=['last_message_at', 'last_activity_at'])
                
                # Update analytics
                self._update_message_analytics(chat_room)
                
                logger.info(f"Message {message.id} sent to room {chat_room.id}")
                return message
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    def get_messages(
        self,
        chat_room: ChatRoom,
        user: User,
        limit: int = 50,
        offset: int = 0,
        message_type: str = None
    ) -> List[ChatMessage]:
        """
        Get messages from a chat room
        
        Args:
            chat_room: Target chat room
            user: Requesting user
            limit: Number of messages to return
            offset: Number of messages to skip
            message_type: Filter by message type
            
        Returns:
            List[ChatMessage]: List of messages
        """
        try:
            # Check if user is participant
            if not chat_room.is_participant(user):
                raise ValidationError("User is not a participant in this chat room")
            
            # Build query
            query = Q(chat_room=chat_room, is_deleted=False)
            
            if message_type:
                query &= Q(message_type=message_type)
            
            # Get messages
            messages = ChatMessage.objects.filter(query).select_related(
                'sender', 'reply_to'
            ).order_by('-sent_at')[offset:offset + limit]
            
            # Mark messages as delivered for this user
            self._mark_messages_as_delivered(messages, user)
            
            return list(messages)
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            raise
    
    def mark_message_as_read(self, message: ChatMessage, user: User) -> bool:
        """
        Mark a message as read by a user
        
        Args:
            message: Message to mark as read
            user: User who read the message
            
        Returns:
            bool: Success status
        """
        try:
            # Check if user is participant
            if not message.chat_room.is_participant(user):
                return False
            
            # Create or update read record
            ChatMessageRead.objects.update_or_create(
                message=message,
                user=user,
                defaults={'read_at': timezone.now()}
            )
            
            # Update message status if all participants have read it
            self._update_message_read_status(message)
            
            # Update participant last read time
            participant = ChatParticipant.objects.get(
                chat_room=message.chat_room,
                user=user
            )
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_at'])
            
            logger.info(f"Message {message.id} marked as read by {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False
    
    def get_unread_count(self, chat_room: ChatRoom, user: User) -> int:
        """
        Get unread message count for a user in a chat room
        
        Args:
            chat_room: Target chat room
            user: User to check
            
        Returns:
            int: Number of unread messages
        """
        try:
            # Get participant's last read time
            participant = ChatParticipant.objects.filter(
                chat_room=chat_room,
                user=user
            ).first()
            
            if not participant or not participant.last_read_at:
                # If never read, count all messages
                return ChatMessage.objects.filter(
                    chat_room=chat_room,
                    is_deleted=False
                ).count()
            
            # Count messages after last read time
            return ChatMessage.objects.filter(
                chat_room=chat_room,
                sent_at__gt=participant.last_read_at,
                is_deleted=False
            ).exclude(sender=user).count()
            
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    def add_participant(
        self,
        chat_room: ChatRoom,
        user: User,
        added_by: User,
        role: str = ChatParticipant.MEMBER
    ) -> bool:
        """
        Add a participant to a chat room
        
        Args:
            chat_room: Target chat room
            user: User to add
            added_by: User who is adding
            role: Role for the new participant
            
        Returns:
            bool: Success status
        """
        try:
            # Check if adder has permission
            adder_participant = ChatParticipant.objects.get(
                chat_room=chat_room,
                user=added_by
            )
            
            if not adder_participant.can_invite_users:
                raise ValidationError("User is not allowed to invite users")
            
            # Check room capacity
            if chat_room.participants.count() >= chat_room.max_participants:
                raise ValidationError("Chat room is at maximum capacity")
            
            # Add participant
            ChatParticipant.objects.get_or_create(
                chat_room=chat_room,
                user=user,
                defaults={'role': role}
            )
            
            logger.info(f"Added {user.username} to chat room {chat_room.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding participant: {e}")
            raise
    
    def remove_participant(
        self,
        chat_room: ChatRoom,
        user: User,
        removed_by: User
    ) -> bool:
        """
        Remove a participant from a chat room
        
        Args:
            chat_room: Target chat room
            user: User to remove
            removed_by: User who is removing
            
        Returns:
            bool: Success status
        """
        try:
            # Check if remover has permission
            remover_participant = ChatParticipant.objects.get(
                chat_room=chat_room,
                user=removed_by
            )
            
            if not remover_participant.can_manage_room and removed_by != user:
                raise ValidationError("User is not allowed to remove participants")
            
            # Remove participant
            ChatParticipant.objects.filter(
                chat_room=chat_room,
                user=user
            ).delete()
            
            logger.info(f"Removed {user.username} from chat room {chat_room.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing participant: {e}")
            raise
    
    def _validate_and_process_file(self, file) -> Dict[str, Any]:
        """
        Validate and process uploaded file
        
        Args:
            file: Uploaded file
            
        Returns:
            Dict[str, Any]: File data
        """
        # Check file size
        if file.size > self.max_file_size:
            raise ValidationError(f"File size exceeds maximum allowed size of {self.max_file_size} bytes")
        
        # Check file type
        file_type = mimetypes.guess_type(file.name)[0]
        if file_type not in self.allowed_file_types:
            raise ValidationError(f"File type {file_type} is not allowed")
        
        return {
            'file': file,
            'file_name': file.name,
            'file_size': file.size,
            'file_type': file_type
        }
    
    def _mark_messages_as_delivered(self, messages: List[ChatMessage], user: User):
        """Mark messages as delivered for a user"""
        for message in messages:
            if message.sender != user and message.status == ChatMessage.SENT:
                message.mark_as_delivered()
    
    def _update_message_read_status(self, message: ChatMessage):
        """Update message read status based on participants"""
        # Count participants who have read the message
        read_count = ChatMessageRead.objects.filter(message=message).count()
        participant_count = message.chat_room.participants.count()
        
        # If all participants have read, mark as read
        if read_count >= participant_count - 1:  # -1 to exclude sender
            message.mark_as_read()
    
    def _update_message_analytics(self, chat_room: ChatRoom):
        """Update message analytics for a chat room"""
        try:
            analytics = ChatAnalytics.objects.get(chat_room=chat_room)
            
            # Update message counts
            analytics.total_messages = ChatMessage.objects.filter(
                chat_room=chat_room,
                is_deleted=False
            ).count()
            
            today = timezone.now().date()
            analytics.messages_today = ChatMessage.objects.filter(
                chat_room=chat_room,
                sent_at__date=today,
                is_deleted=False
            ).count()
            
            week_ago = timezone.now() - timedelta(days=7)
            analytics.messages_this_week = ChatMessage.objects.filter(
                chat_room=chat_room,
                sent_at__gte=week_ago,
                is_deleted=False
            ).count()
            
            month_ago = timezone.now() - timedelta(days=30)
            analytics.messages_this_month = ChatMessage.objects.filter(
                chat_room=chat_room,
                sent_at__gte=month_ago,
                is_deleted=False
            ).count()
            
            # Update participant counts
            analytics.active_participants = ChatParticipant.objects.filter(
                chat_room=chat_room,
                last_read_at__gte=timezone.now() - timedelta(days=1)
            ).count()
            
            analytics.new_participants_today = ChatParticipant.objects.filter(
                chat_room=chat_room,
                joined_at__date=today
            ).count()
            
            # Update file statistics
            file_messages = ChatMessage.objects.filter(
                chat_room=chat_room,
                message_type__in=[ChatMessage.IMAGE, ChatMessage.FILE, ChatMessage.AUDIO, ChatMessage.VIDEO],
                is_deleted=False
            )
            
            analytics.files_shared = file_messages.count()
            analytics.total_file_size = sum(
                msg.file_size or 0 for msg in file_messages
            )
            
            analytics.save()
            
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")


class SupportService:
    """
    Support service for handling support tickets
    """
    
    def create_support_ticket(
        self,
        user: User,
        subject: str,
        description: str,
        category: str = SupportTicket.GENERAL,
        priority: str = SupportTicket.MEDIUM,
        **kwargs
    ) -> SupportTicket:
        """
        Create a new support ticket
        
        Args:
            user: User creating the ticket
            subject: Ticket subject
            description: Ticket description
            category: Ticket category
            priority: Ticket priority
            **kwargs: Additional ticket data
            
        Returns:
            SupportTicket: Created ticket
        """
        try:
            with transaction.atomic():
                # Create support chat room
                chat_room = ChatRoom.objects.create(
                    name=f"Support Ticket - {subject}",
                    room_type=ChatRoom.SUPPORT,
                    description=description,
                    created_by=user
                )
                
                # Create support ticket
                ticket = SupportTicket.objects.create(
                    user=user,
                    subject=subject,
                    description=description,
                    category=category,
                    priority=priority,
                    chat_room=chat_room,
                    **kwargs
                )
                
                # Add user as participant
                ChatParticipant.objects.create(
                    chat_room=chat_room,
                    user=user,
                    role=ChatParticipant.MEMBER
                )
                
                # Initialize analytics
                ChatAnalytics.objects.create(chat_room=chat_room)
                
                logger.info(f"Created support ticket {ticket.ticket_number}")
                return ticket
                
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
            raise
    
    def assign_ticket(
        self,
        ticket: SupportTicket,
        agent: User,
        assigned_by: User
    ) -> bool:
        """
        Assign a support ticket to an agent
        
        Args:
            ticket: Support ticket
            agent: Agent to assign to
            assigned_by: User who is assigning
            
        Returns:
            bool: Success status
        """
        try:
            # Check if assigned_by has permission to assign tickets
            if not assigned_by.is_staff:
                raise ValidationError("Only staff members can assign tickets")
            
            # Assign ticket
            ticket.assign_to(agent)
            
            # Add agent as participant
            ChatParticipant.objects.get_or_create(
                chat_room=ticket.chat_room,
                user=agent,
                defaults={'role': ChatParticipant.ADMIN}
            )
            
            logger.info(f"Assigned ticket {ticket.ticket_number} to {agent.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning ticket: {e}")
            raise
    
    def resolve_ticket(
        self,
        ticket: SupportTicket,
        resolution: str,
        resolved_by: User
    ) -> bool:
        """
        Resolve a support ticket
        
        Args:
            ticket: Support ticket
            resolution: Resolution description
            resolved_by: User who is resolving
            
        Returns:
            bool: Success status
        """
        try:
            # Check if resolved_by has permission
            if not resolved_by.is_staff and resolved_by != ticket.assigned_to:
                raise ValidationError("User is not authorized to resolve this ticket")
            
            # Resolve ticket
            ticket.resolve(resolution)
            
            logger.info(f"Resolved ticket {ticket.ticket_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving ticket: {e}")
            raise
    
    def get_ticket_stats(self, user: User = None) -> Dict[str, Any]:
        """
        Get support ticket statistics
        
        Args:
            user: User to filter by (if None, get all tickets)
            
        Returns:
            Dict[str, Any]: Statistics
        """
        try:
            query = Q()
            if user:
                query = Q(user=user)
            
            tickets = SupportTicket.objects.filter(query)
            
            stats = {
                'total_tickets': tickets.count(),
                'open_tickets': tickets.filter(status=SupportTicket.OPEN).count(),
                'in_progress_tickets': tickets.filter(status=SupportTicket.IN_PROGRESS).count(),
                'resolved_tickets': tickets.filter(status=SupportTicket.RESOLVED).count(),
                'closed_tickets': tickets.filter(status=SupportTicket.CLOSED).count(),
                'avg_resolution_time_hours': 0,
                'satisfaction_rating': 0,
            }
            
            # Calculate average resolution time
            resolved_tickets = tickets.filter(
                status=SupportTicket.RESOLVED,
                resolved_at__isnull=False
            )
            
            if resolved_tickets.exists():
                resolution_times = []
                for ticket in resolved_tickets:
                    if ticket.resolved_at and ticket.opened_at:
                        resolution_time = ticket.resolved_at - ticket.opened_at
                        resolution_times.append(resolution_time.total_seconds() / 3600)  # Convert to hours
                
                if resolution_times:
                    stats['avg_resolution_time_hours'] = sum(resolution_times) / len(resolution_times)
            
            # Calculate average satisfaction rating
            rated_tickets = tickets.filter(
                satisfaction_rating__isnull=False
            )
            
            if rated_tickets.exists():
                avg_rating = rated_tickets.aggregate(
                    avg_rating=Avg('satisfaction_rating')
                )['avg_rating']
                stats['satisfaction_rating'] = round(avg_rating, 2) if avg_rating else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting ticket stats: {e}")
            return {}


class ChatAnalyticsService:
    """
    Service for chat analytics and reporting
    """
    
    def get_room_analytics(self, chat_room: ChatRoom) -> Dict[str, Any]:
        """
        Get analytics for a specific chat room
        
        Args:
            chat_room: Target chat room
            
        Returns:
            Dict[str, Any]: Analytics data
        """
        try:
            analytics = ChatAnalytics.objects.get(chat_room=chat_room)
            
            # Get recent activity
            recent_messages = ChatMessage.objects.filter(
                chat_room=chat_room,
                sent_at__gte=timezone.now() - timedelta(days=7)
            ).order_by('-sent_at')[:10]
            
            # Get top participants
            top_participants = ChatMessage.objects.filter(
                chat_room=chat_room,
                is_deleted=False
            ).values('sender__username').annotate(
                message_count=Count('id')
            ).order_by('-message_count')[:5]
            
            return {
                'room_info': {
                    'id': str(chat_room.id),
                    'name': chat_room.name,
                    'type': chat_room.room_type,
                    'created_at': chat_room.created_at,
                    'participant_count': chat_room.get_participant_count(),
                },
                'message_stats': {
                    'total_messages': analytics.total_messages,
                    'messages_today': analytics.messages_today,
                    'messages_this_week': analytics.messages_this_week,
                    'messages_this_month': analytics.messages_this_month,
                },
                'participant_stats': {
                    'active_participants': analytics.active_participants,
                    'new_participants_today': analytics.new_participants_today,
                },
                'file_stats': {
                    'files_shared': analytics.files_shared,
                    'total_file_size': analytics.total_file_size,
                    'total_file_size_mb': round(analytics.total_file_size / (1024 * 1024), 2),
                },
                'recent_messages': [
                    {
                        'id': str(msg.id),
                        'sender': msg.sender.username,
                        'content': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
                        'message_type': msg.message_type,
                        'sent_at': msg.sent_at,
                    }
                    for msg in recent_messages
                ],
                'top_participants': list(top_participants),
                'last_calculated': analytics.last_calculated_at,
            }
            
        except Exception as e:
            logger.error(f"Error getting room analytics: {e}")
            return {}
    
    def get_global_analytics(self) -> Dict[str, Any]:
        """
        Get global chat analytics
        
        Returns:
            Dict[str, Any]: Global analytics data
        """
        try:
            # Get all chat rooms
            total_rooms = ChatRoom.objects.count()
            active_rooms = ChatRoom.objects.filter(
                status=ChatRoom.ACTIVE
            ).count()
            
            # Get all messages
            total_messages = ChatMessage.objects.filter(
                is_deleted=False
            ).count()
            
            messages_today = ChatMessage.objects.filter(
                sent_at__date=timezone.now().date(),
                is_deleted=False
            ).count()
            
            # Get support tickets
            total_tickets = SupportTicket.objects.count()
            open_tickets = SupportTicket.objects.filter(
                status=SupportTicket.OPEN
            ).count()
            
            # Get file sharing stats
            file_messages = ChatMessage.objects.filter(
                message_type__in=[ChatMessage.IMAGE, ChatMessage.FILE, ChatMessage.AUDIO, ChatMessage.VIDEO],
                is_deleted=False
            )
            
            total_files = file_messages.count()
            total_file_size = sum(msg.file_size or 0 for msg in file_messages)
            
            return {
                'room_stats': {
                    'total_rooms': total_rooms,
                    'active_rooms': active_rooms,
                    'archived_rooms': total_rooms - active_rooms,
                },
                'message_stats': {
                    'total_messages': total_messages,
                    'messages_today': messages_today,
                    'avg_messages_per_room': round(total_messages / total_rooms, 2) if total_rooms > 0 else 0,
                },
                'support_stats': {
                    'total_tickets': total_tickets,
                    'open_tickets': open_tickets,
                    'resolved_tickets': SupportTicket.objects.filter(
                        status=SupportTicket.RESOLVED
                    ).count(),
                },
                'file_stats': {
                    'total_files': total_files,
                    'total_file_size': total_file_size,
                    'total_file_size_mb': round(total_file_size / (1024 * 1024), 2),
                },
                'generated_at': timezone.now(),
            }
            
        except Exception as e:
            logger.error(f"Error getting global analytics: {e}")
            return {}

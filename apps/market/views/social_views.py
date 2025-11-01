from django.shortcuts import get_object_or_404
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.utils import timezone
from rest_framework import views, status, permissions, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from utils.response import ApiResponse
from apps.core.base_views import BaseAPIView
from apps.market.models import (
    Market, MarketLike, MarketBookmark, MarketShare, 
    MarketReport, MarketView
)
from apps.comment.models import Comment
from apps.notification.models import Notification
from apps.market.serializers.social_serializers import (
    MarketLikeSerializer, MarketBookmarkSerializer, MarketShareSerializer,
    MarketReportSerializer, MarketViewSerializer, SocialStatsSerializer,
    NotificationIconSerializer
)


class MarketLikeAPIView(BaseAPIView):
    """Handle market like/unlike functionality"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, market_id):
        """Toggle like status for a market"""
        market = get_object_or_404(Market, id=market_id)
        user = request.user

        with transaction.atomic():
            like_obj, created = MarketLike.objects.get_or_create(
                user=user,
                market=market,
                defaults={'is_active': True}
            )

            if not created:
                # Toggle the like status
                like_obj.is_active = not like_obj.is_active
                like_obj.save()
                action = 'liked' if like_obj.is_active else 'unliked'
            else:
                action = 'liked'

            # Update market like count cache
            cache_key = f"market_likes_{market_id}"
            cache.delete(cache_key)

            # Create notification for market owner (only for likes, not unlikes)
            if like_obj.is_active and user != market.user:
                Notification.objects.create(
                    recipient=market.user,
                    sender=user,
                    notification_type='market_like',
                    title=_('New Like'),
                    message=_('%(user)s liked your market "%(market)s"') % {
                        'user': user.get_full_name() or user.username,
                        'market': market.title
                    },
                    data={
                        'market_id': market.id,
                        'market_title': market.title,
                        'user_id': user.id,
                        'action': 'like'
                    }
                )

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data={
                    'is_liked': like_obj.is_active,
                    'total_likes': market.liked_by.filter(is_active=True).count(),
                    'action': action
                },
                message=_('Market %(action)s successfully') % {'action': action}
            ),
            status=status.HTTP_200_OK
        )

    def get(self, request, market_id):
        """Get like status and count for a market"""
        market = get_object_or_404(Market, id=market_id)
        user = request.user

        is_liked = False
        if user.is_authenticated:
            is_liked = MarketLike.objects.filter(
                user=user,
                market=market,
                is_active=True
            ).exists()

        # Use cache for like count
        cache_key = f"market_likes_{market_id}"
        total_likes = cache.get(cache_key)
        if total_likes is None:
            total_likes = market.liked_by.filter(is_active=True).count()
            cache.set(cache_key, total_likes, 300)  # Cache for 5 minutes

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data={
                    'is_liked': is_liked,
                    'total_likes': total_likes
                }
            )
        )


class MarketBookmarkToggleAPIView(BaseAPIView):
    """Enhanced bookmark functionality with better UX"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, market_id):
        """Toggle bookmark status"""
        market = get_object_or_404(Market, id=market_id)
        user = request.user

        bookmark_obj, created = MarketBookmark.objects.get_or_create(
            user=user,
            market=market,
            defaults={'is_active': True}
        )

        if not created:
            bookmark_obj.is_active = not bookmark_obj.is_active
            bookmark_obj.save()

        action = 'bookmarked' if bookmark_obj.is_active else 'unbookmarked'

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data={
                    'is_bookmarked': bookmark_obj.is_active,
                    'total_bookmarks': market.bookmarked_by.filter(is_active=True).count(),
                    'action': action
                },
                message=_('Market %(action)s successfully') % {'action': action}
            )
        )


class MarketViewTrackAPIView(BaseAPIView):
    """Track market views for analytics"""
    permission_classes = [permissions.AllowAny]

    def post(self, request, market_id):
        """Track a market view"""
        market = get_object_or_404(Market, id=market_id)
        user = request.user if request.user.is_authenticated else None

        # Prevent duplicate views from same user within 1 hour
        if user:
            recent_view = MarketView.objects.filter(
                user=user,
                market=market,
                created_at__gte=timezone.now() - timezone.timedelta(hours=1)
            ).exists()
            
            if not recent_view:
                MarketView.objects.create(user=user, market=market)
        else:
            # For anonymous users, track by IP (with rate limiting)
            ip_address = self.get_client_ip(request)
            cache_key = f"market_view_{market_id}_{ip_address}"
            
            if not cache.get(cache_key):
                MarketView.objects.create(market=market)
                cache.set(cache_key, True, 3600)  # 1 hour cache

        # Update view count cache
        cache_key = f"market_views_{market_id}"
        cache.delete(cache_key)

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data={
                    'total_views': market.viewed_by.count()
                },
                message=_('View tracked successfully')
            )
        )

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MarketShareTrackAPIView(BaseAPIView):
    """Enhanced share tracking with platform analytics"""
    permission_classes = [permissions.AllowAny]

    def post(self, request, market_id):
        """Track a share action"""
        market = get_object_or_404(Market, id=market_id)
        platform = request.data.get('platform', 'direct')
        user = request.user if request.user.is_authenticated else None

        # Validate platform
        valid_platforms = [choice[0] for choice in MarketShare.SHARE_PLATFORMS]
        if platform not in valid_platforms:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    message=_('Invalid share platform')
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create share record
        share_data = {
            'market': market,
            'platform': platform,
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referrer': request.META.get('HTTP_REFERER', '')
        }

        if user:
            share_data['shared_by'] = user

        MarketShare.objects.create(**share_data)

        # Create notification for market owner
        if user and user != market.user:
            Notification.objects.create(
                recipient=market.user,
                sender=user,
                notification_type='market_share',
                title=_('Market Shared'),
                message=_('%(user)s shared your market "%(market)s" on %(platform)s') % {
                    'user': user.get_full_name() or user.username,
                    'market': market.title,
                    'platform': dict(MarketShare.SHARE_PLATFORMS).get(platform, platform)
                },
                data={
                    'market_id': market.id,
                    'platform': platform,
                    'user_id': user.id
                }
            )

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data={
                    'total_shares': market.shares.count(),
                    'platform': platform,
                    'share_url': market.get_absolute_url()
                },
                message=_('Share tracked successfully')
            )
        )

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MarketReportCreateAPIView(BaseAPIView):
    """Create market reports with enhanced validation"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, market_id):
        """Create a report for a market"""
        market = get_object_or_404(Market, id=market_id)
        user = request.user

        # Prevent users from reporting their own markets
        if user == market.user:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    message=_('You cannot report your own market')
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already reported this market
        existing_report = MarketReport.objects.filter(
            creator=user,
            market=market
        ).exists()

        if existing_report:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    message=_('You have already reported this market')
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MarketReportSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            report = serializer.save(
                market=market,
                creator=user
            )

            # Create notification for admin
            Notification.objects.create(
                notification_type='market_report',
                title=_('New Market Report'),
                message=_('Market "%(market)s" has been reported by %(user)s') % {
                    'market': market.title,
                    'user': user.get_full_name() or user.username
                },
                data={
                    'market_id': market.id,
                    'report_id': report.id,
                    'reporter_id': user.id
                }
            )

            return Response(
                ApiResponse(
                    success=True,
                    code=201,
                    data=serializer.data,
                    message=_('Report submitted successfully')
                ),
                status=status.HTTP_201_CREATED
            )

        return Response(
            ApiResponse(
                success=False,
                code=400,
                error=serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST
        )


class MarketSocialStatsAPIView(BaseAPIView):
    """Get comprehensive social statistics for a market"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, market_id):
        """Get all social stats for a market"""
        market = get_object_or_404(Market, id=market_id)
        user = request.user

        # Get cached stats or calculate them
        cache_key = f"market_social_stats_{market_id}"
        stats = cache.get(cache_key)

        if stats is None:
            stats = {
                'likes': market.liked_by.filter(is_active=True).count(),
                'bookmarks': market.bookmarked_by.filter(is_active=True).count(),
                'shares': market.shares.count(),
                'views': market.viewed_by.count(),
                'comments': Comment.objects.filter(
                    content_type=ContentType.objects.get_for_model(Market),
                    object_id=market.id
                ).count(),
                'reports': market.marketreport_set.count()
            }
            cache.set(cache_key, stats, 300)  # Cache for 5 minutes

        # Add user-specific data if authenticated
        user_data = {}
        if user.is_authenticated:
            user_data = {
                'is_liked': MarketLike.objects.filter(
                    user=user, market=market, is_active=True
                ).exists(),
                'is_bookmarked': MarketBookmark.objects.filter(
                    user=user, market=market, is_active=True
                ).exists(),
                'has_reported': MarketReport.objects.filter(
                    creator=user, market=market
                ).exists()
            }

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data={
                    'stats': stats,
                    'user_interactions': user_data
                }
            )
        )


class NotificationIconsAPIView(BaseAPIView):
    """Get notification icons data for UI"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get notification counts for different types"""
        user = request.user
        
        # Get unread notification counts by type
        notification_counts = {
            'total': Notification.objects.filter(
                recipient=user,
                is_read=False
            ).count(),
            'likes': Notification.objects.filter(
                recipient=user,
                notification_type='market_like',
                is_read=False
            ).count(),
            'shares': Notification.objects.filter(
                recipient=user,
                notification_type='market_share',
                is_read=False
            ).count(),
            'comments': Notification.objects.filter(
                recipient=user,
                notification_type__in=['comment', 'comment_reply'],
                is_read=False
            ).count(),
            'reports': Notification.objects.filter(
                recipient=user,
                notification_type='market_report',
                is_read=False
            ).count(),
            'bookmarks': user.bookmarks.filter(is_active=True).count(),
            'help_requests': Notification.objects.filter(
                recipient=user,
                notification_type='help_request',
                is_read=False
            ).count()
        }

        return Response(
            ApiResponse(
                success=True,
                code=200,
                data=notification_counts
            )
        )


class HelpRequestAPIView(BaseAPIView):
    """Handle help requests from users"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Create a help request"""
        user = request.user
        subject = request.data.get('subject', '')
        message = request.data.get('message', '')
        category = request.data.get('category', 'general')

        if not subject or not message:
            return Response(
                ApiResponse(
                    success=False,
                    code=400,
                    message=_('Subject and message are required')
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create notification for admin
        Notification.objects.create(
            notification_type='help_request',
            title=_('Help Request: %(subject)s') % {'subject': subject},
            message=message,
            data={
                'user_id': user.id,
                'category': category,
                'subject': subject,
                'user_email': user.email,
                'user_name': user.get_full_name() or user.username
            }
        )

        return Response(
            ApiResponse(
                success=True,
                code=201,
                message=_('Help request submitted successfully. We will get back to you soon.')
            ),
            status=status.HTTP_201_CREATED
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notifications_read(request):
    """Mark notifications as read"""
    notification_ids = request.data.get('notification_ids', [])
    notification_type = request.data.get('type', None)
    
    queryset = Notification.objects.filter(recipient=request.user)
    
    if notification_ids:
        queryset = queryset.filter(id__in=notification_ids)
    elif notification_type:
        queryset = queryset.filter(notification_type=notification_type)
    else:
        # Mark all as read
        pass
    
    updated_count = queryset.update(is_read=True, read_at=timezone.now())
    
    return Response(
        ApiResponse(
            success=True,
            code=200,
            data={'updated_count': updated_count},
            message=_('Notifications marked as read')
        )
    )
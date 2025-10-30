"""
Analytics WebSocket Consumers for Real-time Analytics
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import asyncio

from .services import RealTimeAnalyticsService, AnalyticsService, MLService

User = get_user_model()
logger = logging.getLogger(__name__)


class AnalyticsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time analytics
    """
    
    async def connect(self):
        """Connect to analytics WebSocket"""
        self.user = self.scope["user"]
        self.analytics_group_name = f"analytics_{self.user.id}"
        
        # Join analytics group
        await self.channel_layer.group_add(
            self.analytics_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial analytics data
        await self.send_analytics_data()
        
        # Start periodic updates
        self.update_task = asyncio.create_task(self.periodic_update())
        
        logger.info(f"Analytics WebSocket connected for user {self.user.username}")
    
    async def disconnect(self, close_code):
        """Disconnect from analytics WebSocket"""
        # Cancel periodic updates
        if hasattr(self, 'update_task'):
            self.update_task.cancel()
        
        # Leave analytics group
        await self.channel_layer.group_discard(
            self.analytics_group_name,
            self.channel_name
        )
        
        logger.info(f"Analytics WebSocket disconnected for user {self.user.username}")
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_analytics':
                await self.send_analytics_data()
            elif message_type == 'get_recommendations':
                await self.send_recommendations()
            elif message_type == 'get_real_time_metrics':
                await self.send_real_time_metrics()
            elif message_type == 'subscribe_to_events':
                await self.subscribe_to_events(data.get('event_types', []))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Unknown message type'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in analytics WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def send_analytics_data(self):
        """Send analytics data to client"""
        try:
            analytics_service = AnalyticsService()
            dashboard_data = await database_sync_to_async(analytics_service.get_dashboard_data)(self.user)
            
            await self.send(text_data=json.dumps({
                'type': 'analytics_data',
                'data': dashboard_data,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error sending analytics data: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to get analytics data'
            }))
    
    async def send_recommendations(self):
        """Send ML recommendations to client"""
        try:
            ml_service = MLService()
            recommendations = await database_sync_to_async(ml_service.get_user_recommendations)(self.user)
            
            await self.send(text_data=json.dumps({
                'type': 'recommendations',
                'data': recommendations,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error sending recommendations: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to get recommendations'
            }))
    
    async def send_real_time_metrics(self):
        """Send real-time metrics to client"""
        try:
            real_time_service = RealTimeAnalyticsService()
            metrics = await database_sync_to_async(real_time_service.get_real_time_metrics)()
            
            await self.send(text_data=json.dumps({
                'type': 'real_time_metrics',
                'data': metrics,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error sending real-time metrics: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to get real-time metrics'
            }))
    
    async def subscribe_to_events(self, event_types):
        """Subscribe to specific event types"""
        try:
            # Store subscribed event types
            self.subscribed_events = event_types
            
            await self.send(text_data=json.dumps({
                'type': 'subscription_confirmed',
                'event_types': event_types,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error subscribing to events: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to subscribe to events'
            }))
    
    async def periodic_update(self):
        """Send periodic updates"""
        try:
            while True:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                # Send real-time metrics
                await self.send_real_time_metrics()
                
        except asyncio.CancelledError:
            logger.info("Periodic update task cancelled")
        except Exception as e:
            logger.error(f"Error in periodic update: {e}")
    
    async def analytics_update(self, event):
        """Handle analytics update from group"""
        try:
            data = event['data']
            message_type = event['type']
            
            await self.send(text_data=json.dumps({
                'type': message_type,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling analytics update: {e}")


class RealTimeDashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time dashboard
    """
    
    async def connect(self):
        """Connect to real-time dashboard WebSocket"""
        self.user = self.scope["user"]
        self.dashboard_group_name = "real_time_dashboard"
        
        # Check if user has permission to view dashboard
        if not self.user.is_staff:
            await self.close(code=4001)
            return
        
        # Join dashboard group
        await self.channel_layer.group_add(
            self.dashboard_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial dashboard data
        await self.send_dashboard_data()
        
        # Start periodic updates
        self.update_task = asyncio.create_task(self.periodic_dashboard_update())
        
        logger.info(f"Real-time dashboard WebSocket connected for user {self.user.username}")
    
    async def disconnect(self, close_code):
        """Disconnect from real-time dashboard WebSocket"""
        # Cancel periodic updates
        if hasattr(self, 'update_task'):
            self.update_task.cancel()
        
        # Leave dashboard group
        await self.channel_layer.group_discard(
            self.dashboard_group_name,
            self.channel_name
        )
        
        logger.info(f"Real-time dashboard WebSocket disconnected for user {self.user.username}")
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_dashboard':
                await self.send_dashboard_data()
            elif message_type == 'get_alerts':
                await self.send_alerts()
            elif message_type == 'get_system_metrics':
                await self.send_system_metrics()
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Unknown message type'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in dashboard WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def send_dashboard_data(self):
        """Send dashboard data to client"""
        try:
            analytics_service = AnalyticsService()
            real_time_service = RealTimeAnalyticsService()
            
            # Get comprehensive dashboard data
            dashboard_data = await database_sync_to_async(analytics_service.get_dashboard_data)(self.user)
            real_time_metrics = await database_sync_to_async(real_time_service.get_real_time_metrics)()
            
            # Combine data
            combined_data = {
                'analytics': dashboard_data,
                'real_time': real_time_metrics,
                'timestamp': timezone.now().isoformat()
            }
            
            await self.send(text_data=json.dumps({
                'type': 'dashboard_data',
                'data': combined_data
            }))
            
        except Exception as e:
            logger.error(f"Error sending dashboard data: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to get dashboard data'
            }))
    
    async def send_alerts(self):
        """Send alerts to client"""
        try:
            real_time_service = RealTimeAnalyticsService()
            metrics = await database_sync_to_async(real_time_service.get_real_time_metrics)()
            
            alerts = metrics.get('alerts', [])
            warnings = metrics.get('warnings', [])
            
            await self.send(text_data=json.dumps({
                'type': 'alerts',
                'data': {
                    'alerts': alerts,
                    'warnings': warnings,
                    'timestamp': timezone.now().isoformat()
                }
            }))
            
        except Exception as e:
            logger.error(f"Error sending alerts: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to get alerts'
            }))
    
    async def send_system_metrics(self):
        """Send system metrics to client"""
        try:
            real_time_service = RealTimeAnalyticsService()
            metrics = await database_sync_to_async(real_time_service.get_real_time_metrics)()
            
            system_metrics = {
                'server_load': metrics.get('server_load', 0),
                'database_connections': metrics.get('database_connections', 0),
                'cache_hit_rate': metrics.get('cache_hit_rate', 0),
                'active_users': metrics.get('active_users', 0),
                'active_sessions': metrics.get('active_sessions', 0)
            }
            
            await self.send(text_data=json.dumps({
                'type': 'system_metrics',
                'data': system_metrics,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error sending system metrics: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to get system metrics'
            }))
    
    async def periodic_dashboard_update(self):
        """Send periodic dashboard updates"""
        try:
            while True:
                await asyncio.sleep(10)  # Update every 10 seconds
                
                # Send real-time metrics
                await self.send_system_metrics()
                
        except asyncio.CancelledError:
            logger.info("Periodic dashboard update task cancelled")
        except Exception as e:
            logger.error(f"Error in periodic dashboard update: {e}")
    
    async def dashboard_update(self, event):
        """Handle dashboard update from group"""
        try:
            data = event['data']
            message_type = event['type']
            
            await self.send(text_data=json.dumps({
                'type': message_type,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling dashboard update: {e}")


class EventTrackingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for event tracking
    """
    
    async def connect(self):
        """Connect to event tracking WebSocket"""
        self.user = self.scope["user"]
        self.tracking_group_name = f"event_tracking_{self.user.id}"
        
        # Join tracking group
        await self.channel_layer.group_add(
            self.tracking_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f"Event tracking WebSocket connected for user {self.user.username}")
    
    async def disconnect(self, close_code):
        """Disconnect from event tracking WebSocket"""
        # Leave tracking group
        await self.channel_layer.group_discard(
            self.tracking_group_name,
            self.channel_name
        )
        
        logger.info(f"Event tracking WebSocket disconnected for user {self.user.username}")
    
    async def receive(self, text_data):
        """Receive event tracking data from WebSocket"""
        try:
            data = json.loads(text_data)
            event_type = data.get('event_type')
            
            if not event_type:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Event type is required'
                }))
                return
            
            # Track the event
            await self.track_event(data)
            
            # Send confirmation
            await self.send(text_data=json.dumps({
                'type': 'event_tracked',
                'event_type': event_type,
                'timestamp': timezone.now().isoformat()
            }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in event tracking WebSocket: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def track_event(self, event_data):
        """Track user event"""
        try:
            from .signals import track_user_behavior
            
            # Extract event data
            event_type = event_data.get('event_type')
            session_id = event_data.get('session_id', 'unknown')
            page_url = event_data.get('page_url')
            referrer_url = event_data.get('referrer_url')
            user_agent = event_data.get('user_agent')
            ip_address = event_data.get('ip_address')
            device_type = event_data.get('device_type')
            browser = event_data.get('browser')
            os = event_data.get('os')
            country = event_data.get('country')
            city = event_data.get('city')
            latitude = event_data.get('latitude')
            longitude = event_data.get('longitude')
            
            # Additional event data
            additional_data = event_data.get('event_data', {})
            
            # Track the event
            await database_sync_to_async(track_user_behavior)(
                user=self.user,
                session_id=session_id,
                event_type=event_type,
                page_url=page_url,
                referrer_url=referrer_url,
                user_agent=user_agent,
                ip_address=ip_address,
                device_type=device_type,
                browser=browser,
                os=os,
                country=country,
                city=city,
                latitude=latitude,
                longitude=longitude,
                event_data=additional_data
            )
            
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
    
    async def event_tracked(self, event):
        """Handle event tracked notification"""
        try:
            data = event['data']
            
            await self.send(text_data=json.dumps({
                'type': 'event_tracked',
                'data': data,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling event tracked notification: {e}")


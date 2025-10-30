"""
Analytics Dashboard Views for ASOUD Platform
Real-time dashboard and analytics visualization
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

from .services import AnalyticsService, RealTimeAnalyticsService, MLService

User = get_user_model()


def is_staff_user(user):
    """Check if user is staff"""
    return user.is_staff


@login_required
def analytics_dashboard(request):
    """Main analytics dashboard"""
    context = {
        'user': request.user,
        'is_staff': request.user.is_staff,
        'websocket_url': 'ws://localhost:8000/ws/analytics/',
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def real_time_dashboard(request):
    """Real-time dashboard for staff"""
    context = {
        'user': request.user,
        'websocket_url': 'ws://localhost:8000/ws/analytics/dashboard/',
    }
    return render(request, 'analytics/real_time_dashboard.html', context)


@login_required
def user_analytics(request):
    """User-specific analytics"""
    context = {
        'user': request.user,
        'websocket_url': 'ws://localhost:8000/ws/analytics/',
    }
    return render(request, 'analytics/user_analytics.html', context)


@login_required
def product_analytics(request):
    """Product analytics dashboard"""
    context = {
        'user': request.user,
        'websocket_url': 'ws://localhost:8000/ws/analytics/',
    }
    return render(request, 'analytics/product_analytics.html', context)


@login_required
def market_analytics(request):
    """Market analytics dashboard"""
    context = {
        'user': request.user,
        'websocket_url': 'ws://localhost:8000/ws/analytics/',
    }
    return render(request, 'analytics/market_analytics.html', context)


@login_required
def ml_recommendations(request):
    """ML recommendations dashboard"""
    context = {
        'user': request.user,
        'websocket_url': 'ws://localhost:8000/ws/analytics/',
    }
    return render(request, 'analytics/ml_recommendations.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class AnalyticsAPIView(View):
    """API view for analytics data"""
    
    def get(self, request):
        """Get analytics data"""
        try:
            analytics_service = AnalyticsService()
            data = analytics_service.get_dashboard_data(request.user)
            
            return JsonResponse({
                'success': True,
                'data': data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=500)
    
    def post(self, request):
        """Handle analytics requests"""
        try:
            data = json.loads(request.body)
            request_type = data.get('type')
            
            if request_type == 'time_series':
                days = data.get('days', 30)
                metric = data.get('metric', 'revenue')
                
                analytics_service = AnalyticsService()
                time_series_data = analytics_service.get_time_series_data(days=days, metric=metric)
                
                return JsonResponse({
                    'success': True,
                    'data': time_series_data,
                    'timestamp': timezone.now().isoformat()
                })
            
            elif request_type == 'top_performers':
                entity_type = data.get('entity_type', 'products')
                limit = data.get('limit', 10)
                
                analytics_service = AnalyticsService()
                top_performers = analytics_service.get_top_performers(
                    entity_type=entity_type,
                    limit=limit
                )
                
                return JsonResponse({
                    'success': True,
                    'data': top_performers,
                    'timestamp': timezone.now().isoformat()
                })
            
            elif request_type == 'conversion_funnel':
                days = data.get('days', 30)
                
                analytics_service = AnalyticsService()
                funnel_data = analytics_service.get_conversion_funnel(days=days)
                
                return JsonResponse({
                    'success': True,
                    'data': funnel_data,
                    'timestamp': timezone.now().isoformat()
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Unknown request type',
                    'timestamp': timezone.now().isoformat()
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON',
                'timestamp': timezone.now().isoformat()
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class RealTimeAnalyticsAPIView(View):
    """API view for real-time analytics"""
    
    def get(self, request):
        """Get real-time analytics data"""
        try:
            real_time_service = RealTimeAnalyticsService()
            data = real_time_service.get_real_time_metrics()
            
            return JsonResponse({
                'success': True,
                'data': data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MLRecommendationsAPIView(View):
    """API view for ML recommendations"""
    
    def get(self, request):
        """Get ML recommendations"""
        try:
            ml_service = MLService()
            recommendations = ml_service.get_user_recommendations(request.user)
            
            return JsonResponse({
                'success': True,
                'data': recommendations,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=500)
    
    def post(self, request):
        """Handle ML recommendation requests"""
        try:
            data = json.loads(request.body)
            request_type = data.get('type')
            
            if request_type == 'product_recommendations':
                limit = data.get('limit', 10)
                
                ml_service = MLService()
                recommendations = ml_service.get_product_recommendations(
                    user_id=request.user.id,
                    limit=limit
                )
                
                return JsonResponse({
                    'success': True,
                    'data': recommendations,
                    'timestamp': timezone.now().isoformat()
                })
            
            elif request_type == 'similar_products':
                product_id = data.get('product_id')
                limit = data.get('limit', 10)
                
                if not product_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Product ID is required',
                        'timestamp': timezone.now().isoformat()
                    }, status=400)
                
                ml_service = MLService()
                similar_products = ml_service.get_similar_products(
                    product_id=product_id,
                    limit=limit
                )
                
                return JsonResponse({
                    'success': True,
                    'data': similar_products,
                    'timestamp': timezone.now().isoformat()
                })
            
            elif request_type == 'price_optimization':
                product_id = data.get('product_id')
                
                if not product_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Product ID is required',
                        'timestamp': timezone.now().isoformat()
                    }, status=400)
                
                ml_service = MLService()
                price_suggestions = ml_service.get_price_optimization(
                    product_id=product_id
                )
                
                return JsonResponse({
                    'success': True,
                    'data': price_suggestions,
                    'timestamp': timezone.now().isoformat()
                })
            
            elif request_type == 'demand_forecast':
                product_id = data.get('product_id')
                days = data.get('days', 30)
                
                if not product_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Product ID is required',
                        'timestamp': timezone.now().isoformat()
                    }, status=400)
                
                ml_service = MLService()
                forecast = ml_service.get_demand_forecast(
                    product_id=product_id,
                    days=days
                )
                
                return JsonResponse({
                    'success': True,
                    'data': forecast,
                    'timestamp': timezone.now().isoformat()
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Unknown request type',
                    'timestamp': timezone.now().isoformat()
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON',
                'timestamp': timezone.now().isoformat()
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EventTrackingAPIView(View):
    """API view for event tracking"""
    
    def post(self, request):
        """Track user event"""
        try:
            data = json.loads(request.body)
            event_type = data.get('event_type')
            
            if not event_type:
                return JsonResponse({
                    'success': False,
                    'error': 'Event type is required',
                    'timestamp': timezone.now().isoformat()
                }, status=400)
            
            # Track the event
            from .signals import track_user_behavior
            
            event = track_user_behavior(
                user=request.user,
                session_id=data.get('session_id', 'unknown'),
                event_type=event_type,
                page_url=data.get('page_url'),
                referrer_url=data.get('referrer_url'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                ip_address=request.META.get('REMOTE_ADDR'),
                device_type=data.get('device_type'),
                browser=data.get('browser'),
                os=data.get('os'),
                country=data.get('country'),
                city=data.get('city'),
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                event_data=data.get('event_data', {})
            )
            
            if event:
                return JsonResponse({
                    'success': True,
                    'event_id': event.id,
                    'timestamp': timezone.now().isoformat()
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to track event',
                    'timestamp': timezone.now().isoformat()
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON',
                'timestamp': timezone.now().isoformat()
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=500)


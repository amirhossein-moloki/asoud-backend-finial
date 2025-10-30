"""
Fraud Detection and Customer Segmentation Views for ASOUD Platform
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from typing import List, Dict, Any
import logging

from .fraud_detection import FraudDetectionEngine, CustomerSegmentationEngine

logger = logging.getLogger(__name__)


class FraudDetectionViewSet(viewsets.ViewSet):
    """
    ViewSet for fraud detection
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = None  # Custom responses
    
    def list(self, request):
        """Get fraud detection overview"""
        try:
            days = int(request.query_params.get('days', 30))
            
            fraud_engine = FraudDetectionEngine()
            fraud_analytics = fraud_engine.get_fraud_analytics(days)
            
            return Response({
                'success': True,
                'data': fraud_analytics,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting fraud detection overview: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def detect_transaction(self, request):
        """Detect fraud for a specific transaction"""
        try:
            transaction_data = request.data
            
            if not transaction_data:
                return Response({
                    'success': False,
                    'error': 'Transaction data is required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            fraud_engine = FraudDetectionEngine()
            result = fraud_engine.detect_fraud(transaction_data)
            
            return Response({
                'success': True,
                'data': result,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error detecting transaction fraud: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def batch_detect(self, request):
        """Batch detect fraud for multiple transactions"""
        try:
            transactions = request.data.get('transactions', [])
            
            if not transactions:
                return Response({
                    'success': False,
                    'error': 'Transactions data is required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            fraud_engine = FraudDetectionEngine()
            result = fraud_engine.batch_detect_fraud(transactions)
            
            return Response({
                'success': True,
                'data': result,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in batch fraud detection: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def fraud_patterns(self, request):
        """Get fraud patterns analysis"""
        try:
            days = int(request.query_params.get('days', 30))
            
            fraud_engine = FraudDetectionEngine()
            fraud_analytics = fraud_engine.get_fraud_analytics(days)
            
            patterns_data = {
                'fraud_patterns': fraud_analytics.get('fraud_patterns', {}),
                'risk_factors': fraud_analytics.get('risk_factors', []),
                'fraud_rate': fraud_analytics.get('fraud_rate', 0),
                'total_transactions': fraud_analytics.get('total_transactions', 0)
            }
            
            return Response({
                'success': True,
                'data': patterns_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting fraud patterns: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def risk_factors(self, request):
        """Get risk factors analysis"""
        try:
            days = int(request.query_params.get('days', 30))
            
            fraud_engine = FraudDetectionEngine()
            fraud_analytics = fraud_engine.get_fraud_analytics(days)
            
            risk_factors = fraud_analytics.get('risk_factors', [])
            
            return Response({
                'success': True,
                'data': {
                    'risk_factors': risk_factors,
                    'total_factors': len(risk_factors),
                    'high_risk_factors': [rf for rf in risk_factors if rf.get('severity') == 'high'],
                    'medium_risk_factors': [rf for rf in risk_factors if rf.get('severity') == 'medium'],
                    'low_risk_factors': [rf for rf in risk_factors if rf.get('severity') == 'low']
                },
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting risk factors: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def block_transaction(self, request):
        """Block a fraudulent transaction"""
        try:
            transaction_id = request.data.get('transaction_id')
            reason = request.data.get('reason', 'Fraud detected')
            
            if not transaction_id:
                return Response({
                    'success': False,
                    'error': 'Transaction ID is required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Log the blocked transaction
            from .models import UserBehaviorEvent
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # Create fraud event
            UserBehaviorEvent.objects.create(
                user=User.objects.get(id=request.user.id),
                session_id=f'fraud_block_{transaction_id}',
                event_type='fraud_blocked',
                event_data={
                    'transaction_id': transaction_id,
                    'reason': reason,
                    'blocked_by': request.user.username,
                    'timestamp': timezone.now().isoformat()
                },
                page_url='fraud_detection',
                ip_address=request.META.get('REMOTE_ADDR'),
                device_type='system',
                browser='fraud_detection',
                os='system',
                country='system',
                city='system'
            )
            
            return Response({
                'success': True,
                'data': {
                    'transaction_id': transaction_id,
                    'blocked': True,
                    'reason': reason,
                    'blocked_by': request.user.username,
                    'timestamp': timezone.now().isoformat()
                },
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error blocking transaction: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerSegmentationViewSet(viewsets.ViewSet):
    """
    ViewSet for customer segmentation
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = None  # Custom responses
    
    def list(self, request):
        """Get customer segmentation overview"""
        try:
            days = int(request.query_params.get('days', 90))
            
            segmentation_engine = CustomerSegmentationEngine()
            segments = segmentation_engine.segment_customers(days)
            
            return Response({
                'success': True,
                'data': segments,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting customer segmentation: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def get_customer_segment(self, request):
        """Get segment for a specific customer"""
        try:
            customer_id = request.query_params.get('customer_id')
            days = int(request.query_params.get('days', 90))
            
            if not customer_id:
                return Response({
                    'success': False,
                    'error': 'Customer ID is required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            segmentation_engine = CustomerSegmentationEngine()
            result = segmentation_engine.get_customer_segment(int(customer_id), days)
            
            return Response({
                'success': True,
                'data': result,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting customer segment: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def segment_analysis(self, request):
        """Get detailed segment analysis"""
        try:
            days = int(request.query_params.get('days', 90))
            
            segmentation_engine = CustomerSegmentationEngine()
            segments = segmentation_engine.segment_customers(days)
            
            analysis_data = {
                'segment_analysis': segments.get('segment_analysis', {}),
                'insights': segments.get('insights', []),
                'model_performance': segments.get('model_performance', {}),
                'total_customers': segments.get('total_customers', 0)
            }
            
            return Response({
                'success': True,
                'data': analysis_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting segment analysis: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def segment_insights(self, request):
        """Get segment insights and recommendations"""
        try:
            days = int(request.query_params.get('days', 90))
            
            segmentation_engine = CustomerSegmentationEngine()
            segments = segmentation_engine.segment_customers(days)
            
            insights_data = {
                'insights': segments.get('insights', []),
                'segment_distribution': segments.get('segment_analysis', {}).get('segment_distribution', {}),
                'recommendations': self._generate_segment_recommendations(segments)
            }
            
            return Response({
                'success': True,
                'data': insights_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting segment insights: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def segment_comparison(self, request):
        """Get segment comparison analysis"""
        try:
            days = int(request.query_params.get('days', 90))
            
            segmentation_engine = CustomerSegmentationEngine()
            segments = segmentation_engine.segment_customers(days)
            
            comparison_data = {
                'segment_comparison': segments.get('segment_analysis', {}).get('segment_comparison', {}),
                'segment_characteristics': segments.get('segment_analysis', {}).get('segment_characteristics', {}),
                'total_segments': len(segments.get('segments', {}))
            }
            
            return Response({
                'success': True,
                'data': comparison_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting segment comparison: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_segment_recommendations(self, segments: dict) -> List[Dict[str, Any]]:
        """Generate recommendations based on segments"""
        recommendations = []
        
        try:
            segment_analysis = segments.get('segment_analysis', {})
            segment_distribution = segment_analysis.get('segment_distribution', {})
            
            # High value loyal customers
            if 'high_value_loyal' in segment_distribution:
                hvl_percentage = segment_distribution['high_value_loyal']['percentage']
                if hvl_percentage > 10:
                    recommendations.append({
                        'segment': 'high_value_loyal',
                        'title': 'Focus on High Value Customers',
                        'description': f"{hvl_percentage:.1f}% of customers are high-value loyal",
                        'priority': 'high',
                        'actions': [
                            'Implement VIP program',
                            'Provide exclusive offers',
                            'Assign dedicated support',
                            'Regular check-ins and feedback'
                        ]
                    })
            
            # Churned customers
            if 'churned_customers' in segment_distribution:
                churned_percentage = segment_distribution['churned_customers']['percentage']
                if churned_percentage > 20:
                    recommendations.append({
                        'segment': 'churned_customers',
                        'title': 'Address High Churn Rate',
                        'description': f"{churned_percentage:.1f}% of customers have churned",
                        'priority': 'high',
                        'actions': [
                            'Implement win-back campaigns',
                            'Analyze churn reasons',
                            'Improve customer experience',
                            'Offer special incentives for return'
                        ]
                    })
            
            # New customers
            if 'new_customers' in segment_distribution:
                new_percentage = segment_distribution['new_customers']['percentage']
                if new_percentage > 30:
                    recommendations.append({
                        'segment': 'new_customers',
                        'title': 'Optimize New Customer Experience',
                        'description': f"{new_percentage:.1f}% of customers are new",
                        'priority': 'medium',
                        'actions': [
                            'Improve onboarding process',
                            'Provide welcome offers',
                            'Create educational content',
                            'Implement first-purchase incentives'
                        ]
                    })
            
            # Low value occasional customers
            if 'low_value_occasional' in segment_distribution:
                lvo_percentage = segment_distribution['low_value_occasional']['percentage']
                if lvo_percentage > 40:
                    recommendations.append({
                        'segment': 'low_value_occasional',
                        'title': 'Increase Engagement of Low Value Customers',
                        'description': f"{lvo_percentage:.1f}% of customers are low-value occasional",
                        'priority': 'medium',
                        'actions': [
                            'Send targeted promotions',
                            'Improve product recommendations',
                            'Create loyalty program',
                            'Increase communication frequency'
                        ]
                    })
            
        except Exception as e:
            logger.error(f"Error generating segment recommendations: {e}")
        
        return recommendations


class SecurityAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for security analytics
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = None  # Custom responses
    
    @action(detail=False, methods=['get'])
    def security_overview(self, request):
        """Get security analytics overview"""
        try:
            days = int(request.query_params.get('days', 30))
            
            # Get fraud analytics
            fraud_engine = FraudDetectionEngine()
            fraud_analytics = fraud_engine.get_fraud_analytics(days)
            
            # Get customer segmentation
            segmentation_engine = CustomerSegmentationEngine()
            segments = segmentation_engine.segment_customers(days)
            
            # Get security events
            security_events = self._get_security_events(days)
            
            overview = {
                'fraud_analytics': fraud_analytics,
                'customer_segments': segments,
                'security_events': security_events,
                'security_score': self._calculate_security_score(fraud_analytics, security_events),
                'recommendations': self._generate_security_recommendations(fraud_analytics, segments, security_events)
            }
            
            return Response({
                'success': True,
                'data': overview,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting security overview: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_security_events(self, days: int) -> Dict[str, Any]:
        """Get security events"""
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            # Get security-related events
            security_events = UserBehaviorEvent.objects.filter(
                event_type__in=['fraud_detected', 'fraud_blocked', 'suspicious_activity', 'security_alert'],
                timestamp__gte=start_date
            )
            
            events_by_type = {}
            for event in security_events:
                event_type = event.event_type
                if event_type not in events_by_type:
                    events_by_type[event_type] = 0
                events_by_type[event_type] += 1
            
            return {
                'total_events': security_events.count(),
                'events_by_type': events_by_type,
                'recent_events': list(security_events.order_by('-timestamp')[:10].values(
                    'event_type', 'timestamp', 'event_data'
                ))
            }
            
        except Exception as e:
            logger.error(f"Error getting security events: {e}")
            return {'total_events': 0, 'events_by_type': {}, 'recent_events': []}
    
    def _calculate_security_score(self, fraud_analytics: dict, security_events: dict) -> float:
        """Calculate overall security score"""
        try:
            score = 100.0
            
            # Deduct points for fraud
            fraud_rate = fraud_analytics.get('fraud_rate', 0)
            if fraud_rate > 5:
                score -= 30
            elif fraud_rate > 2:
                score -= 15
            elif fraud_rate > 1:
                score -= 5
            
            # Deduct points for security events
            total_events = security_events.get('total_events', 0)
            if total_events > 100:
                score -= 20
            elif total_events > 50:
                score -= 10
            elif total_events > 20:
                score -= 5
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating security score: {e}")
            return 50.0
    
    def _generate_security_recommendations(self, fraud_analytics: dict, segments: dict, security_events: dict) -> List[Dict[str, Any]]:
        """Generate security recommendations"""
        recommendations = []
        
        try:
            fraud_rate = fraud_analytics.get('fraud_rate', 0)
            total_events = security_events.get('total_events', 0)
            
            if fraud_rate > 2:
                recommendations.append({
                    'type': 'fraud_prevention',
                    'title': 'High Fraud Rate Detected',
                    'description': f"Fraud rate is {fraud_rate:.2f}%, above acceptable threshold",
                    'priority': 'high',
                    'actions': [
                        'Implement stricter fraud detection rules',
                        'Increase transaction monitoring',
                        'Review and update fraud prevention policies',
                        'Consider additional verification steps'
                    ]
                })
            
            if total_events > 50:
                recommendations.append({
                    'type': 'security_monitoring',
                    'title': 'High Security Event Volume',
                    'description': f"{total_events} security events detected in the period",
                    'priority': 'medium',
                    'actions': [
                        'Review security event patterns',
                        'Investigate root causes',
                        'Update security monitoring rules',
                        'Consider additional security measures'
                    ]
                })
            
            # Customer segmentation recommendations
            segment_insights = segments.get('insights', [])
            for insight in segment_insights:
                if insight.get('type') == 'negative' and insight.get('title') == 'High Churn Rate':
                    recommendations.append({
                        'type': 'customer_retention',
                        'title': 'Address Customer Churn',
                        'description': insight.get('description', ''),
                        'priority': 'medium',
                        'actions': [
                            'Implement customer retention strategies',
                            'Analyze churn reasons',
                            'Improve customer experience',
                            'Create win-back campaigns'
                        ]
                    })
            
        except Exception as e:
            logger.error(f"Error generating security recommendations: {e}")
        
        return recommendations

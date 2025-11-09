"""
ML Optimization Views for ASOUD Platform
Price Optimization and Demand Forecasting Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import logging

from .ml_optimization import PriceOptimizationEngine, DemandForecastingEngine

logger = logging.getLogger(__name__)


class PriceOptimizationViewSet(viewsets.ViewSet):
    """
    ViewSet for price optimization
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = None  # Custom responses
    
    def list(self, request):
        """Get price optimization overview"""
        try:
            # Get all products that need price optimization
            from apps.item.models import Item
            
            products = Product.objects.all()[:10]  # Limit for overview
            
            price_engine = PriceOptimizationEngine()
            optimizations = []
            
            for product in products:
                try:
                    result = price_engine.optimize_product_price(product.id, 90)
                    if result.get('recommended_price', 0) > 0:
                        optimizations.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'current_price': result['current_price'],
                            'recommended_price': result['recommended_price'],
                            'price_change_percent': result['price_change_percent'],
                            'expected_revenue': result['expected_revenue'],
                            'confidence': result['confidence']
                        })
                except Exception as e:
                    logger.error(f"Error optimizing price for product {product.id}: {e}")
                    continue
            
            return Response({
                'success': True,
                'data': {
                    'optimizations': optimizations,
                    'total_products': len(products),
                    'optimized_products': len(optimizations)
                },
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting price optimization overview: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def optimize_product(self, request):
        """Optimize price for a specific product"""
        try:
            product_id = request.query_params.get('product_id')
            days = int(request.query_params.get('days', 90))
            
            if not product_id:
                return Response({
                    'success': False,
                    'error': 'Product ID is required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            price_engine = PriceOptimizationEngine()
            result = price_engine.optimize_product_price(int(product_id), days)
            
            return Response({
                'success': True,
                'data': result,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error optimizing product price: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def batch_optimize(self, request):
        """Batch optimize prices for multiple products"""
        try:
            product_ids = request.data.get('product_ids', [])
            days = request.data.get('days', 90)
            
            if not product_ids:
                return Response({
                    'success': False,
                    'error': 'Product IDs are required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            price_engine = PriceOptimizationEngine()
            result = price_engine.batch_optimize_prices(product_ids, days)
            
            return Response({
                'success': True,
                'data': result,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in batch price optimization: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def price_elasticity(self, request):
        """Get price elasticity analysis"""
        try:
            product_id = request.query_params.get('product_id')
            days = int(request.query_params.get('days', 90))
            
            if not product_id:
                return Response({
                    'success': False,
                    'error': 'Product ID is required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            price_engine = PriceOptimizationEngine()
            result = price_engine.optimize_product_price(int(product_id), days)
            
            elasticity_data = {
                'product_id': int(product_id),
                'price_elasticity': result.get('price_elasticity', 0),
                'sensitivity_analysis': result.get('sensitivity_analysis', {}),
                'current_price': result.get('current_price', 0),
                'recommended_price': result.get('recommended_price', 0)
            }
            
            return Response({
                'success': True,
                'data': elasticity_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting price elasticity: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def price_sensitivity(self, request):
        """Get price sensitivity analysis"""
        try:
            product_id = request.query_params.get('product_id')
            days = int(request.query_params.get('days', 90))
            
            if not product_id:
                return Response({
                    'success': False,
                    'error': 'Product ID is required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            price_engine = PriceOptimizationEngine()
            result = price_engine.optimize_product_price(int(product_id), days)
            
            sensitivity_data = result.get('sensitivity_analysis', {})
            
            return Response({
                'success': True,
                'data': sensitivity_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting price sensitivity: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DemandForecastingViewSet(viewsets.ViewSet):
    """
    ViewSet for demand forecasting
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = None  # Custom responses
    
    def list(self, request):
        """Get demand forecasting overview"""
        try:
            # Get all products that need demand forecasting
            from apps.item.models import Item
            
            products = Product.objects.all()[:10]  # Limit for overview
            
            forecast_engine = DemandForecastingEngine()
            forecasts = []
            
            for product in products:
                try:
                    result = forecast_engine.forecast_demand(product.id, 90, 7)
                    if result.get('forecast'):
                        forecasts.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'forecast_days': len(result['forecast']),
                            'avg_predicted_demand': sum(f['predicted_demand'] for f in result['forecast']) / len(result['forecast']),
                            'trend': result['trend'],
                            'accuracy': result['accuracy']
                        })
                except Exception as e:
                    logger.error(f"Error forecasting demand for product {product.id}: {e}")
                    continue
            
            return Response({
                'success': True,
                'data': {
                    'forecasts': forecasts,
                    'total_products': len(products),
                    'forecasted_products': len(forecasts)
                },
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting demand forecasting overview: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def forecast_product(self, request):
        """Forecast demand for a specific product"""
        try:
            product_id = request.query_params.get('product_id')
            days = int(request.query_params.get('days', 90))
            forecast_days = int(request.query_params.get('forecast_days', 7))
            
            if not product_id:
                return Response({
                    'success': False,
                    'error': 'Product ID is required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            forecast_engine = DemandForecastingEngine()
            result = forecast_engine.forecast_demand(int(product_id), days, forecast_days)
            
            return Response({
                'success': True,
                'data': result,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error forecasting product demand: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def batch_forecast(self, request):
        """Batch forecast demand for multiple products"""
        try:
            product_ids = request.data.get('product_ids', [])
            days = request.data.get('days', 90)
            forecast_days = request.data.get('forecast_days', 7)
            
            if not product_ids:
                return Response({
                    'success': False,
                    'error': 'Product IDs are required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            forecast_engine = DemandForecastingEngine()
            result = forecast_engine.batch_forecast_demand(product_ids, days, forecast_days)
            
            return Response({
                'success': True,
                'data': result,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in batch demand forecasting: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def demand_trends(self, request):
        """Get demand trends analysis"""
        try:
            product_id = request.query_params.get('product_id')
            days = int(request.query_params.get('days', 90))
            
            if not product_id:
                return Response({
                    'success': False,
                    'error': 'Product ID is required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            forecast_engine = DemandForecastingEngine()
            result = forecast_engine.forecast_demand(int(product_id), days, 7)
            
            trends_data = {
                'product_id': int(product_id),
                'trend': result.get('trend', {}),
                'seasonality': result.get('seasonality', {}),
                'historical_data': result.get('historical_data', []),
                'forecast': result.get('forecast', [])
            }
            
            return Response({
                'success': True,
                'data': trends_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting demand trends: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def demand_insights(self, request):
        """Get demand insights"""
        try:
            product_id = request.query_params.get('product_id')
            days = int(request.query_params.get('days', 90))
            
            if not product_id:
                return Response({
                    'success': False,
                    'error': 'Product ID is required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            forecast_engine = DemandForecastingEngine()
            result = forecast_engine.forecast_demand(int(product_id), days, 7)
            
            insights_data = {
                'product_id': int(product_id),
                'insights': result.get('insights', []),
                'accuracy': result.get('accuracy', {}),
                'trend': result.get('trend', {}),
                'seasonality': result.get('seasonality', {})
            }
            
            return Response({
                'success': True,
                'data': insights_data,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting demand insights: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MLOptimizationViewSet(viewsets.ViewSet):
    """
    ViewSet for ML optimization features
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = None  # Custom responses
    
    @action(detail=False, methods=['get'])
    def optimization_summary(self, request):
        """Get ML optimization summary"""
        try:
            days = int(request.query_params.get('days', 90))
            
            # Get price optimization summary
            price_engine = PriceOptimizationEngine()
            
            # Get demand forecasting summary
            forecast_engine = DemandForecastingEngine()
            
            # Get products that need optimization
            from apps.item.models import Item
            products = Product.objects.all()[:20]  # Limit for summary
            
            price_optimizations = []
            demand_forecasts = []
            
            for product in products:
                try:
                    # Price optimization
                    price_result = price_engine.optimize_product_price(product.id, days)
                    if price_result.get('recommended_price', 0) > 0:
                        price_optimizations.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'current_price': price_result['current_price'],
                            'recommended_price': price_result['recommended_price'],
                            'price_change_percent': price_result['price_change_percent'],
                            'confidence': price_result['confidence']
                        })
                    
                    # Demand forecasting
                    forecast_result = forecast_engine.forecast_demand(product.id, days, 7)
                    if forecast_result.get('forecast'):
                        avg_demand = sum(f['predicted_demand'] for f in forecast_result['forecast']) / len(forecast_result['forecast'])
                        demand_forecasts.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'avg_predicted_demand': avg_demand,
                            'trend': forecast_result['trend']['direction'],
                            'accuracy': forecast_result['accuracy']['r2']
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing product {product.id}: {e}")
                    continue
            
            summary = {
                'total_products': len(products),
                'price_optimizations': {
                    'count': len(price_optimizations),
                    'data': price_optimizations
                },
                'demand_forecasts': {
                    'count': len(demand_forecasts),
                    'data': demand_forecasts
                },
                'recommendations': self._generate_optimization_recommendations(price_optimizations, demand_forecasts)
            }
            
            return Response({
                'success': True,
                'data': summary,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting optimization summary: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def apply_optimizations(self, request):
        """Apply ML optimizations to products"""
        try:
            optimizations = request.data.get('optimizations', [])
            
            if not optimizations:
                return Response({
                    'success': False,
                    'error': 'Optimizations data is required',
                    'timestamp': timezone.now().isoformat()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            applied_optimizations = []
            failed_optimizations = []
            
            for optimization in optimizations:
                try:
                    product_id = optimization.get('product_id')
                    optimization_type = optimization.get('type')
                    
                    if optimization_type == 'price':
                        # Apply price optimization
                        new_price = optimization.get('recommended_price')
                        if new_price and new_price > 0:
                            from apps.item.models import Item
                            product = Product.objects.get(id=product_id)
                            old_price = product.price
                            product.price = new_price
                            product.save()
                            
                            applied_optimizations.append({
                                'product_id': product_id,
                                'type': 'price',
                                'old_price': float(old_price),
                                'new_price': float(new_price),
                                'change_percent': ((new_price - old_price) / old_price) * 100
                            })
                    
                except Exception as e:
                    logger.error(f"Error applying optimization for product {product_id}: {e}")
                    failed_optimizations.append({
                        'product_id': product_id,
                        'error': str(e)
                    })
            
            return Response({
                'success': True,
                'data': {
                    'applied_optimizations': applied_optimizations,
                    'failed_optimizations': failed_optimizations,
                    'total_applied': len(applied_optimizations),
                    'total_failed': len(failed_optimizations)
                },
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error applying optimizations: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_optimization_recommendations(self, price_optimizations, demand_forecasts):
        """Generate optimization recommendations"""
        recommendations = []
        
        try:
            # Price optimization recommendations
            high_confidence_optimizations = [opt for opt in price_optimizations if opt['confidence'] > 0.7]
            if high_confidence_optimizations:
                recommendations.append({
                    'type': 'price_optimization',
                    'title': 'High Confidence Price Optimizations',
                    'description': f"{len(high_confidence_optimizations)} products have high-confidence price optimization recommendations",
                    'priority': 'high',
                    'count': len(high_confidence_optimizations)
                })
            
            # Demand forecasting recommendations
            increasing_demand = [forecast for forecast in demand_forecasts if forecast['trend'] == 'increasing']
            if increasing_demand:
                recommendations.append({
                    'type': 'demand_forecast',
                    'title': 'Increasing Demand Products',
                    'description': f"{len(increasing_demand)} products show increasing demand trends",
                    'priority': 'medium',
                    'count': len(increasing_demand)
                })
            
            # High accuracy forecasts
            high_accuracy_forecasts = [forecast for forecast in demand_forecasts if forecast['accuracy'] > 0.8]
            if high_accuracy_forecasts:
                recommendations.append({
                    'type': 'demand_forecast',
                    'title': 'High Accuracy Demand Forecasts',
                    'description': f"{len(high_accuracy_forecasts)} products have high-accuracy demand forecasts",
                    'priority': 'medium',
                    'count': len(high_accuracy_forecasts)
                })
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
        
        return recommendations

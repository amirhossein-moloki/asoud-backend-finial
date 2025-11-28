"""
Machine Learning Models for ASOUD Platform
Advanced ML models for recommendations, predictions, and analytics
"""

try:
    import numpy as np
    import pandas as pd
    HAS_ML_LIBS = True
except ImportError:
    HAS_ML_LIBS = False
    # Define dummy classes for when ML libraries are not available
    class DummyArray:
        def __init__(self, *args, **kwargs):
            pass
        def __getitem__(self, key):
            return 0
        def __setitem__(self, key, value):
            pass
        def __len__(self):
            return 0
        def mean(self):
            return 0
        def sum(self):
            return 0
        def std(self):
            return 0
        def max(self):
            return 0
        def min(self):
            return 0
    
    np = type('numpy', (), {
        'array': lambda x: DummyArray(),
        'mean': lambda x: 0,
        'std': lambda x: 0,
        'sum': lambda x: 0,
        'max': lambda x: 0,
        'min': lambda x: 0,
    })()
    
    pd = type('pandas', (), {
        'DataFrame': lambda x: x,
        'Series': lambda x: x,
    })()
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F
from django.core.cache import cache
import logging
import json
from typing import List, Dict, Any, Optional, Tuple

from .models import UserBehaviorEvent, UserSession, ItemAnalytics, UserAnalytics

logger = logging.getLogger(__name__)


class CollaborativeFilteringModel:
    """
    Collaborative Filtering for Product Recommendations
    """
    
    def __init__(self):
        self.user_item_matrix = None
        self.user_similarity = None
        self.item_similarity = None
        self.cache_timeout = 3600  # 1 hour
    
    def fit(self, user_events: List[UserBehaviorEvent]):
        """Fit the collaborative filtering model"""
        try:
            # Create user-item matrix
            df = pd.DataFrame([
                {
                    'user_id': event.user_id,
                    'product_id': event.object_id,
                    'rating': self._calculate_rating(event)
                }
                for event in user_events
                if event.event_type in ['purchase', 'add_to_cart', 'product_view']
                and event.object_id is not None
            ])
            
            if df.empty:
                logger.warning("No data available for collaborative filtering")
                return
            
            # Create user-item matrix
            self.user_item_matrix = df.pivot_table(
                index='user_id', 
                columns='product_id', 
                values='rating', 
                fill_value=0
            )
            
            # Calculate user similarity
            self.user_similarity = self._calculate_user_similarity()
            
            # Calculate item similarity
            self.item_similarity = self._calculate_item_similarity()
            
            logger.info("Collaborative filtering model fitted successfully")
            
        except Exception as e:
            logger.error(f"Error fitting collaborative filtering model: {e}")
    
    def predict(self, user_id: int, product_id: int) -> float:
        """Predict rating for user-item pair"""
        if self.user_item_matrix is None:
            return 0.0
        
        try:
            if user_id in self.user_item_matrix.index and product_id in self.user_item_matrix.columns:
                return float(self.user_item_matrix.loc[user_id, product_id])
            
            # Use collaborative filtering prediction
            if user_id in self.user_item_matrix.index:
                # User-based collaborative filtering
                user_ratings = self.user_item_matrix.loc[user_id]
                similar_users = self.user_similarity[user_id].sort_values(ascending=False)[1:6]  # Top 5 similar users
                
                prediction = 0.0
                similarity_sum = 0.0
                
                for similar_user_id, similarity in similar_users.items():
                    if similar_user_id in self.user_item_matrix.index and product_id in self.user_item_matrix.columns:
                        rating = self.user_item_matrix.loc[similar_user_id, product_id]
                        if rating > 0:
                            prediction += similarity * rating
                            similarity_sum += abs(similarity)
                
                if similarity_sum > 0:
                    return prediction / similarity_sum
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error predicting rating: {e}")
            return 0.0
    
    def get_recommendations(self, user_id: int, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N recommendations for a user"""
        if self.user_item_matrix is None:
            return []
        
        try:
            if user_id not in self.user_item_matrix.index:
                # Return popular items for new users
                return self._get_popular_items(n)
            
            user_ratings = self.user_item_matrix.loc[user_id]
            unrated_items = user_ratings[user_ratings == 0].index
            
            recommendations = []
            for product_id in unrated_items:
                predicted_rating = self.predict(user_id, product_id)
                if predicted_rating > 0:
                    recommendations.append({
                        'product_id': product_id,
                        'predicted_rating': predicted_rating
                    })
            
            # Sort by predicted rating and return top N
            recommendations.sort(key=lambda x: x['predicted_rating'], reverse=True)
            return recommendations[:n]
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    def _calculate_rating(self, event: UserBehaviorEvent) -> float:
        """Calculate implicit rating from event"""
        rating_map = {
            'purchase': 5.0,
            'add_to_cart': 4.0,
            'product_view': 3.0,
            'remove_from_cart': 1.0
        }
        return rating_map.get(event.event_type, 0.0)
    
    def _calculate_user_similarity(self) -> pd.DataFrame:
        """Calculate user similarity matrix"""
        if self.user_item_matrix is None:
            return pd.DataFrame()
        
        # Use cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        
        user_similarity = cosine_similarity(self.user_item_matrix.fillna(0))
        user_similarity_df = pd.DataFrame(
            user_similarity,
            index=self.user_item_matrix.index,
            columns=self.user_item_matrix.index
        )
        
        return user_similarity_df
    
    def _calculate_item_similarity(self) -> pd.DataFrame:
        """Calculate item similarity matrix"""
        if self.user_item_matrix is None:
            return pd.DataFrame()
        
        # Use cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        
        item_similarity = cosine_similarity(self.user_item_matrix.fillna(0).T)
        item_similarity_df = pd.DataFrame(
            item_similarity,
            index=self.user_item_matrix.columns,
            columns=self.user_item_matrix.columns
        )
        
        return item_similarity_df
    
    def _get_popular_items(self, n: int) -> List[Dict[str, Any]]:
        """Get popular items for new users"""
        try:
            popular_products = ItemAnalytics.objects.order_by('-popularity_score')[:n]
            return [
                {
                    'product_id': product.item_id,
                    'predicted_rating': float(product.popularity_score) / 100.0
                }
                for product in popular_products
            ]
        except Exception as e:
            logger.error(f"Error getting popular items: {e}")
            return []


class ContentBasedFilteringModel:
    """
    Content-Based Filtering for Product Recommendations
    """
    
    def __init__(self):
        self.product_features = None
        self.similarity_matrix = None
        self.cache_timeout = 3600  # 1 hour
    
    def fit(self, products_data: List[Dict[str, Any]]):
        """Fit the content-based filtering model"""
        try:
            if not products_data:
                logger.warning("No product data available for content-based filtering")
                return
            
            # Create product features matrix
            df = pd.DataFrame(products_data)
            
            # Select relevant features
            feature_columns = ['category_id', 'price', 'rating', 'popularity_score']
            available_features = [col for col in feature_columns if col in df.columns]
            
            if not available_features:
                logger.warning("No relevant features found for content-based filtering")
                return
            
            self.product_features = df[['product_id'] + available_features].set_index('product_id')
            
            # Normalize features
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            self.product_features[available_features] = scaler.fit_transform(
                self.product_features[available_features]
            )
            
            # Calculate similarity matrix
            self.similarity_matrix = self._calculate_similarity_matrix()
            
            logger.info("Content-based filtering model fitted successfully")
            
        except Exception as e:
            logger.error(f"Error fitting content-based filtering model: {e}")
    
    def get_similar_products(self, product_id: int, n: int = 10) -> List[Dict[str, Any]]:
        """Get similar products based on content"""
        if self.similarity_matrix is None or product_id not in self.similarity_matrix.index:
            return []
        
        try:
            similarities = self.similarity_matrix.loc[product_id].sort_values(ascending=False)
            similar_products = []
            
            for similar_product_id, similarity in similarities.items():
                if similar_product_id != product_id and similarity > 0:
                    similar_products.append({
                        'product_id': similar_product_id,
                        'similarity': float(similarity)
                    })
            
            return similar_products[:n]
            
        except Exception as e:
            logger.error(f"Error getting similar products: {e}")
            return []
    
    def _calculate_similarity_matrix(self) -> pd.DataFrame:
        """Calculate product similarity matrix"""
        if self.product_features is None:
            return pd.DataFrame()
        
        from sklearn.metrics.pairwise import cosine_similarity
        
        similarity = cosine_similarity(self.product_features)
        similarity_df = pd.DataFrame(
            similarity,
            index=self.product_features.index,
            columns=self.product_features.index
        )
        
        return similarity_df


class PriceOptimizationModel:
    """
    Price Optimization Model using Machine Learning
    """
    
    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.cache_timeout = 3600  # 1 hour
    
    def fit(self, historical_data: List[Dict[str, Any]]):
        """Fit the price optimization model"""
        try:
            if not historical_data:
                logger.warning("No historical data available for price optimization")
                return
            
            df = pd.DataFrame(historical_data)
            
            # Prepare features
            feature_columns = [
                'price', 'category_id', 'competitor_price', 'demand_score',
                'seasonality', 'promotion_active', 'stock_level'
            ]
            
            self.feature_columns = [col for col in feature_columns if col in df.columns]
            
            if not self.feature_columns:
                logger.warning("No relevant features found for price optimization")
                return
            
            X = df[self.feature_columns]
            y = df['demand']  # Target variable
            
            # Train model
            from sklearn.ensemble import RandomForestRegressor
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(X, y)
            
            logger.info("Price optimization model fitted successfully")
            
        except Exception as e:
            logger.error(f"Error fitting price optimization model: {e}")
    
    def predict_optimal_price(self, product_features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict optimal price for a product"""
        if self.model is None:
            return {'optimal_price': product_features.get('price', 0), 'confidence': 0.0}
        
        try:
            # Prepare features
            features = []
            for col in self.feature_columns:
                features.append(product_features.get(col, 0))
            
            # Predict demand for different prices
            price_range = np.linspace(
                product_features.get('price', 0) * 0.5,
                product_features.get('price', 0) * 1.5,
                20
            )
            
            demands = []
            for price in price_range:
                test_features = features.copy()
                price_index = self.feature_columns.index('price')
                test_features[price_index] = price
                
                demand = self.model.predict([test_features])[0]
                demands.append(demand)
            
            # Find optimal price (maximize revenue)
            revenues = price_range * np.array(demands)
            optimal_price_index = np.argmax(revenues)
            optimal_price = price_range[optimal_price_index]
            
            # Calculate confidence based on model performance
            confidence = min(0.9, max(0.1, np.std(demands) / np.mean(demands)))
            
            return {
                'optimal_price': float(optimal_price),
                'current_price': float(product_features.get('price', 0)),
                'price_change': float(optimal_price - product_features.get('price', 0)),
                'expected_demand': float(demands[optimal_price_index]),
                'expected_revenue': float(revenues[optimal_price_index]),
                'confidence': float(confidence)
            }
            
        except Exception as e:
            logger.error(f"Error predicting optimal price: {e}")
            return {'optimal_price': product_features.get('price', 0), 'confidence': 0.0}


class DemandForecastingModel:
    """
    Demand Forecasting Model using Time Series Analysis
    """
    
    def __init__(self):
        self.model = None
        self.cache_timeout = 3600  # 1 hour
    
    def fit(self, time_series_data: List[Dict[str, Any]]):
        """Fit the demand forecasting model"""
        try:
            if not time_series_data:
                logger.warning("No time series data available for demand forecasting")
                return
            
            df = pd.DataFrame(time_series_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date').sort_index()
            
            # Prepare time series
            ts = df['demand'].fillna(method='ffill').fillna(0)
            
            # Simple moving average model
            window_size = min(7, len(ts) // 2)
            if window_size < 2:
                logger.warning("Insufficient data for demand forecasting")
                return
            
            self.model = {
                'window_size': window_size,
                'last_values': ts.tail(window_size).tolist(),
                'trend': self._calculate_trend(ts),
                'seasonality': self._calculate_seasonality(ts)
            }
            
            logger.info("Demand forecasting model fitted successfully")
            
        except Exception as e:
            logger.error(f"Error fitting demand forecasting model: {e}")
    
    def forecast(self, periods: int = 30) -> List[Dict[str, Any]]:
        """Forecast demand for future periods"""
        if self.model is None:
            return []
        
        try:
            forecasts = []
            last_values = self.model['last_values'].copy()
            trend = self.model['trend']
            seasonality = self.model['seasonality']
            
            for i in range(periods):
                # Simple moving average with trend and seasonality
                forecast_value = np.mean(last_values) + trend * (i + 1)
                
                # Add seasonality (weekly pattern)
                if seasonality and len(seasonality) > 0:
                    seasonality_index = i % len(seasonality)
                    forecast_value += seasonality[seasonality_index]
                
                # Ensure non-negative demand
                forecast_value = max(0, forecast_value)
                
                forecasts.append({
                    'date': (timezone.now() + timedelta(days=i+1)).date().isoformat(),
                    'predicted_demand': float(forecast_value),
                    'confidence': float(min(0.9, max(0.1, 1.0 - i * 0.01)))
                })
                
                # Update last values for next iteration
                last_values.append(forecast_value)
                if len(last_values) > self.model['window_size']:
                    last_values.pop(0)
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error forecasting demand: {e}")
            return []
    
    def _calculate_trend(self, ts: pd.Series) -> float:
        """Calculate trend in time series"""
        if len(ts) < 2:
            return 0.0
        
        # Simple linear trend
        x = np.arange(len(ts))
        y = ts.values
        
        # Linear regression
        slope = np.polyfit(x, y, 1)[0]
        return float(slope)
    
    def _calculate_seasonality(self, ts: pd.Series) -> List[float]:
        """Calculate seasonality pattern"""
        if len(ts) < 7:
            return []
        
        # Weekly seasonality
        weekly_pattern = []
        for day in range(7):
            day_values = ts[ts.index.weekday == day]
            if len(day_values) > 0:
                weekly_pattern.append(float(day_values.mean()))
            else:
                weekly_pattern.append(0.0)
        
        # Normalize seasonality
        if weekly_pattern:
            mean_value = np.mean(weekly_pattern)
            weekly_pattern = [x - mean_value for x in weekly_pattern]
        
        return weekly_pattern


class CustomerSegmentationModel:
    """
    Customer Segmentation Model using Clustering
    """
    
    def __init__(self):
        self.model = None
        self.segments = None
        self.cache_timeout = 3600  # 1 hour
    
    def fit(self, customer_data: List[Dict[str, Any]]):
        """Fit the customer segmentation model"""
        try:
            if not customer_data:
                logger.warning("No customer data available for segmentation")
                return
            
            df = pd.DataFrame(customer_data)
            
            # Select features for clustering
            feature_columns = [
                'total_spent', 'total_orders', 'avg_order_value',
                'days_since_last_purchase', 'total_sessions', 'avg_session_duration'
            ]
            
            available_features = [col for col in feature_columns if col in df.columns]
            
            if not available_features:
                logger.warning("No relevant features found for customer segmentation")
                return
            
            X = df[available_features].fillna(0)
            
            # Normalize features
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # K-means clustering
            from sklearn.cluster import KMeans
            
            # Determine optimal number of clusters
            n_clusters = min(5, max(2, len(df) // 10))
            
            self.model = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = self.model.fit_predict(X_scaled)
            
            # Create segment definitions
            self.segments = self._create_segment_definitions(df, cluster_labels, available_features)
            
            logger.info(f"Customer segmentation model fitted with {n_clusters} segments")
            
        except Exception as e:
            logger.error(f"Error fitting customer segmentation model: {e}")
    
    def predict_segment(self, customer_features: Dict[str, Any]) -> str:
        """Predict customer segment"""
        if self.model is None or self.segments is None:
            return 'unknown'
        
        try:
            # Prepare features
            feature_values = []
            for feature in self.model.feature_names_in_:
                feature_values.append(customer_features.get(feature, 0))
            
            # Predict cluster
            cluster = self.model.predict([feature_values])[0]
            
            # Map cluster to segment name
            return self.segments.get(cluster, 'unknown')
            
        except Exception as e:
            logger.error(f"Error predicting customer segment: {e}")
            return 'unknown'
    
    def _create_segment_definitions(self, df: pd.DataFrame, cluster_labels, features: List[str]) -> Dict[int, str]:
        """Create segment definitions based on cluster characteristics"""
        segments = {}
        
        for cluster_id in range(len(set(cluster_labels))):
            cluster_data = df[cluster_labels == cluster_id]
            
            # Calculate cluster characteristics
            avg_spent = cluster_data['total_spent'].mean() if 'total_spent' in cluster_data.columns else 0
            avg_orders = cluster_data['total_orders'].mean() if 'total_orders' in cluster_data.columns else 0
            avg_value = cluster_data['avg_order_value'].mean() if 'avg_order_value' in cluster_data.columns else 0
            
            # Define segment based on characteristics
            if avg_spent > 1000 and avg_orders > 10:
                segment_name = 'high_value_loyal'
            elif avg_spent > 500 and avg_orders > 5:
                segment_name = 'medium_value_regular'
            elif avg_spent > 100:
                segment_name = 'low_value_occasional'
            else:
                segment_name = 'new_inactive'
            
            segments[cluster_id] = segment_name
        
        return segments


class FraudDetectionModel:
    """
    Fraud Detection Model using Anomaly Detection
    """
    
    def __init__(self):
        self.model = None
        self.threshold = None
        self.cache_timeout = 3600  # 1 hour
    
    def fit(self, transaction_data: List[Dict[str, Any]]):
        """Fit the fraud detection model"""
        try:
            if not transaction_data:
                logger.warning("No transaction data available for fraud detection")
                return
            
            df = pd.DataFrame(transaction_data)
            
            # Select features for fraud detection
            feature_columns = [
                'amount', 'hour_of_day', 'day_of_week', 'user_orders_count',
                'user_avg_order_value', 'ip_frequency', 'device_frequency'
            ]
            
            available_features = [col for col in feature_columns if col in df.columns]
            
            if not available_features:
                logger.warning("No relevant features found for fraud detection")
                return
            
            X = df[available_features].fillna(0)
            
            # Normalize features
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Isolation Forest for anomaly detection
            from sklearn.ensemble import IsolationForest
            
            self.model = IsolationForest(contamination=0.1, random_state=42)
            self.model.fit(X_scaled)
            
            # Calculate threshold
            scores = self.model.decision_function(X_scaled)
            self.threshold = np.percentile(scores, 10)  # Bottom 10% are considered anomalies
            
            logger.info("Fraud detection model fitted successfully")
            
        except Exception as e:
            logger.error(f"Error fitting fraud detection model: {e}")
    
    def predict_fraud(self, transaction_features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict if a transaction is fraudulent"""
        if self.model is None:
            return {'is_fraud': False, 'fraud_score': 0.0, 'confidence': 0.0}
        
        try:
            # Prepare features
            feature_values = []
            for feature in self.model.feature_names_in_:
                feature_values.append(transaction_features.get(feature, 0))
            
            # Predict anomaly score
            score = self.model.decision_function([feature_values])[0]
            is_fraud = score < self.threshold
            
            # Calculate confidence
            confidence = abs(score) / (abs(score) + 1)  # Normalize to 0-1
            
            return {
                'is_fraud': bool(is_fraud),
                'fraud_score': float(score),
                'confidence': float(confidence),
                'risk_level': 'high' if is_fraud and confidence > 0.7 else 'medium' if is_fraud else 'low'
            }
            
        except Exception as e:
            logger.error(f"Error predicting fraud: {e}")
            return {'is_fraud': False, 'fraud_score': 0.0, 'confidence': 0.0}

"""
ML Optimization Models for ASOUD Platform
Price Optimization, Demand Forecasting, and Advanced ML Features
"""

import logging
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
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
        'linspace': lambda a, b, c: [a, b],
        'arange': lambda x: [0, 1],
        'polyfit': lambda x, y, z: [0, 0],
    })()
    
    pd = type('pandas', (), {
        'DataFrame': lambda x: x,
        'Series': lambda x: x,
        'to_datetime': lambda x: x,
    })()
    
    class DummyML:
        def __init__(self, *args, **kwargs):
            pass
        def fit(self, *args, **kwargs):
            return self
        def transform(self, *args, **kwargs):
            return DummyArray()
        def predict(self, *args, **kwargs):
            return DummyArray()
        def fit_transform(self, *args, **kwargs):
            return DummyArray()
        def fit_predict(self, *args, **kwargs):
            return DummyArray()
    
    RandomForestRegressor = DummyML
    GradientBoostingRegressor = DummyML
    LinearRegression = DummyML
    Ridge = DummyML
    Lasso = DummyML
    StandardScaler = DummyML
    MinMaxScaler = DummyML
    train_test_split = lambda x, y, **kwargs: (x, x, y, y)
    cross_val_score = lambda x, y, z: [0]
    mean_squared_error = lambda x, y: 0
    mean_absolute_error = lambda x, y: 0
    r2_score = lambda x, y: 0
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F
from django.core.cache import cache
from typing import List, Dict, Any, Optional, Tuple
import json
# ML imports are handled in the try-except block above
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class PriceOptimizationEngine:
    """
    Advanced Price Optimization Engine using Machine Learning
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.cache_timeout = 3600  # 1 hour
    
    def optimize_product_price(self, product_id: int, days: int = 90) -> Dict[str, Any]:
        """Optimize price for a specific product"""
        cache_key = f"price_optimization_{product_id}_{days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Get historical data
            historical_data = self._get_historical_data(product_id, days)
            
            if len(historical_data) < 10:
                return self._empty_price_optimization()
            
            # Prepare features
            features, target = self._prepare_price_features(historical_data)
            
            if len(features) < 10:
                return self._empty_price_optimization()
            
            # Train models
            models = self._train_price_models(features, target)
            
            # Get current product data
            current_data = self._get_current_product_data(product_id)
            
            # Generate price recommendations
            recommendations = self._generate_price_recommendations(
                models, current_data, features, target
            )
            
            # Calculate price elasticity
            elasticity = self._calculate_price_elasticity(features, target)
            
            # Generate price sensitivity analysis
            sensitivity_analysis = self._generate_sensitivity_analysis(
                models, current_data, elasticity
            )
            
            optimization_result = {
                'product_id': product_id,
                'current_price': current_data.get('price', 0),
                'recommended_price': recommendations['optimal_price'],
                'price_change': recommendations['optimal_price'] - current_data.get('price', 0),
                'price_change_percent': ((recommendations['optimal_price'] - current_data.get('price', 0)) / current_data.get('price', 1)) * 100,
                'expected_demand': recommendations['expected_demand'],
                'expected_revenue': recommendations['expected_revenue'],
                'confidence': recommendations['confidence'],
                'price_elasticity': elasticity,
                'sensitivity_analysis': sensitivity_analysis,
                'model_performance': models['performance'],
                'recommendations': recommendations['recommendations'],
                'generated_at': timezone.now().isoformat()
            }
            
            # Cache the result
            cache.set(cache_key, optimization_result, self.cache_timeout)
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error optimizing price for product {product_id}: {e}")
            return self._empty_price_optimization()
    
    def batch_optimize_prices(self, product_ids: List[int], days: int = 90) -> Dict[str, Any]:
        """Optimize prices for multiple products"""
        try:
            results = {}
            successful_optimizations = 0
            failed_optimizations = 0
            
            for product_id in product_ids:
                try:
                    result = self.optimize_product_price(product_id, days)
                    if result.get('recommended_price', 0) > 0:
                        results[product_id] = result
                        successful_optimizations += 1
                    else:
                        failed_optimizations += 1
                except Exception as e:
                    logger.error(f"Error optimizing price for product {product_id}: {e}")
                    failed_optimizations += 1
            
            return {
                'total_products': len(product_ids),
                'successful_optimizations': successful_optimizations,
                'failed_optimizations': failed_optimizations,
                'success_rate': (successful_optimizations / len(product_ids)) * 100,
                'results': results,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in batch price optimization: {e}")
            return {'error': str(e)}
    
    def _get_historical_data(self, product_id: int, days: int) -> List[Dict[str, Any]]:
        """Get historical data for price optimization"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Get purchase events for this product
        events = UserBehaviorEvent.objects.filter(
            object_id=product_id,
            event_type='purchase',
            timestamp__gte=start_date
        ).values('timestamp', 'event_data__value')
        
        historical_data = []
        for event in events:
            historical_data.append({
                'timestamp': event['timestamp'],
                'price': float(event['event_data__value']) if event['event_data__value'] else 0,
                'date': event['timestamp'].date()
            })
        
        return historical_data
    
    def _get_current_product_data(self, product_id: int) -> Dict[str, Any]:
        """Get current product data"""
        try:
            from apps.product.models import Product
            product = Product.objects.get(id=product_id)
            
            return {
                'price': float(product.price),
                'category_id': product.category.id if product.category else 0,
                'name': product.name,
                'description': product.description
            }
        except Product.DoesNotExist:
            return {'price': 0, 'category_id': 0, 'name': 'Unknown', 'description': ''}
    
    def _prepare_price_features(self, historical_data: List[Dict[str, Any]]):
        """Prepare features for price optimization"""
        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = pd.to_datetime(df['date'])
        
        # Create features
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['hour'] = df['timestamp'].dt.hour
        df['month'] = df['timestamp'].dt.month
        df['quarter'] = df['timestamp'].dt.quarter
        
        # Price features
        df['price_lag_1'] = df['price'].shift(1)
        df['price_lag_7'] = df['price'].shift(7)
        df['price_ma_7'] = df['price'].rolling(window=7).mean()
        df['price_std_7'] = df['price'].rolling(window=7).std()
        
        # Demand features (simplified)
        df['demand'] = 1  # In real implementation, this would be actual demand data
        
        # Remove NaN values
        df = df.dropna()
        
        if len(df) < 5:
            return np.array([]), np.array([])
        
        # Select features
        feature_columns = [
            'day_of_week', 'hour', 'month', 'quarter',
            'price_lag_1', 'price_lag_7', 'price_ma_7', 'price_std_7'
        ]
        
        features = df[feature_columns].values
        target = df['demand'].values
        
        return features, target
    
    def _train_price_models(self, features, target) -> Dict[str, Any]:
        """Train multiple price optimization models"""
        if len(features) < 5:
            return {'performance': {}, 'models': {}}
        
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, target, test_size=0.2, random_state=42
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train models
            models = {
                'linear': LinearRegression(),
                'ridge': Ridge(alpha=1.0),
                'lasso': Lasso(alpha=0.1),
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
            }
            
            model_performance = {}
            trained_models = {}
            
            for name, model in models.items():
                try:
                    # Train model
                    if name in ['linear', 'ridge', 'lasso']:
                        model.fit(X_train_scaled, y_train)
                        y_pred = model.predict(X_test_scaled)
                    else:
                        model.fit(X_train, y_train)
                        y_pred = model.predict(X_test)
                    
                    # Calculate performance metrics
                    mse = mean_squared_error(y_test, y_pred)
                    mae = mean_absolute_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    
                    model_performance[name] = {
                        'mse': float(mse),
                        'mae': float(mae),
                        'r2': float(r2)
                    }
                    
                    trained_models[name] = model
                    
                except Exception as e:
                    logger.error(f"Error training {name} model: {e}")
                    continue
            
            # Select best model
            best_model_name = max(model_performance.keys(), key=lambda x: model_performance[x]['r2'])
            best_model = trained_models[best_model_name]
            
            return {
                'performance': model_performance,
                'models': trained_models,
                'best_model': best_model,
                'best_model_name': best_model_name,
                'scaler': scaler
            }
            
        except Exception as e:
            logger.error(f"Error training price models: {e}")
            return {'performance': {}, 'models': {}}
    
    def _generate_price_recommendations(self, models: Dict, current_data: Dict, 
                                      features, target) -> Dict[str, Any]:
        """Generate price recommendations"""
        try:
            if not models.get('best_model'):
                return self._empty_recommendations()
            
            best_model = models['best_model']
            scaler = models.get('scaler')
            
            # Test different prices
            current_price = current_data.get('price', 100)
            price_range = np.linspace(current_price * 0.5, current_price * 1.5, 20)
            
            best_price = current_price
            best_demand = 0
            best_revenue = 0
            
            for price in price_range:
                # Create feature vector for this price
                feature_vector = self._create_price_feature_vector(price, features, current_data)
                
                if scaler:
                    feature_vector_scaled = scaler.transform([feature_vector])
                    predicted_demand = best_model.predict(feature_vector_scaled)[0]
                else:
                    predicted_demand = best_model.predict([feature_vector])[0]
                
                predicted_revenue = price * predicted_demand
                
                if predicted_revenue > best_revenue:
                    best_revenue = predicted_revenue
                    best_demand = predicted_demand
                    best_price = price
            
            # Calculate confidence based on model performance
            best_model_performance = models['performance'].get(models['best_model_name'], {})
            confidence = min(0.9, max(0.1, best_model_performance.get('r2', 0.5)))
            
            # Generate recommendations
            recommendations = []
            if best_price > current_price * 1.1:
                recommendations.append("Consider increasing price for higher revenue")
            elif best_price < current_price * 0.9:
                recommendations.append("Consider decreasing price to increase demand")
            else:
                recommendations.append("Current price is near optimal")
            
            return {
                'optimal_price': float(best_price),
                'expected_demand': float(best_demand),
                'expected_revenue': float(best_revenue),
                'confidence': float(confidence),
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error generating price recommendations: {e}")
            return self._empty_recommendations()
    
    def _create_price_feature_vector(self, price: float, features, current_data: Dict):
        """Create feature vector for price prediction"""
        # Use average values from historical data
        avg_features = np.mean(features, axis=0)
        
        # Update price-related features
        avg_features[4] = price  # price_lag_1
        avg_features[5] = price  # price_lag_7
        avg_features[6] = price  # price_ma_7
        avg_features[7] = 0      # price_std_7
        
        return avg_features
    
    def _calculate_price_elasticity(self, features, target) -> float:
        """Calculate price elasticity of demand"""
        try:
            if len(features) < 5:
                return 0.0
            
            # Simple elasticity calculation
            prices = features[:, 4]  # price_lag_1
            demands = target
            
            # Calculate percentage changes
            price_changes = np.diff(prices) / prices[:-1]
            demand_changes = np.diff(demands) / demands[:-1]
            
            # Calculate elasticity
            elasticity = np.mean(demand_changes / price_changes) if np.any(price_changes != 0) else 0.0
            
            return float(elasticity)
            
        except Exception as e:
            logger.error(f"Error calculating price elasticity: {e}")
            return 0.0
    
    def _generate_sensitivity_analysis(self, models: Dict, current_data: Dict, elasticity: float) -> Dict[str, Any]:
        """Generate price sensitivity analysis"""
        try:
            current_price = current_data.get('price', 100)
            
            # Test price sensitivity
            price_changes = [-20, -10, -5, 0, 5, 10, 20]  # Percentage changes
            sensitivity_data = []
            
            for change in price_changes:
                new_price = current_price * (1 + change / 100)
                
                # Estimate demand change based on elasticity
                demand_change = elasticity * (change / 100)
                new_demand = 1 * (1 + demand_change)  # Base demand = 1
                new_revenue = new_price * new_demand
                
                sensitivity_data.append({
                    'price_change_percent': change,
                    'new_price': float(new_price),
                    'demand_change_percent': float(demand_change * 100),
                    'new_demand': float(new_demand),
                    'new_revenue': float(new_revenue),
                    'revenue_change_percent': float((new_revenue - current_price) / current_price * 100)
                })
            
            return {
                'elasticity': float(elasticity),
                'sensitivity_data': sensitivity_data,
                'optimal_price_change': max(sensitivity_data, key=lambda x: x['new_revenue'])['price_change_percent']
            }
            
        except Exception as e:
            logger.error(f"Error generating sensitivity analysis: {e}")
            return {'elasticity': 0.0, 'sensitivity_data': [], 'optimal_price_change': 0}
    
    def _empty_price_optimization(self) -> Dict[str, Any]:
        """Return empty price optimization result"""
        return {
            'product_id': 0,
            'current_price': 0,
            'recommended_price': 0,
            'price_change': 0,
            'price_change_percent': 0,
            'expected_demand': 0,
            'expected_revenue': 0,
            'confidence': 0,
            'price_elasticity': 0,
            'sensitivity_analysis': {},
            'model_performance': {},
            'recommendations': [],
            'generated_at': timezone.now().isoformat()
        }
    
    def _empty_recommendations(self) -> Dict[str, Any]:
        """Return empty recommendations"""
        return {
            'optimal_price': 0,
            'expected_demand': 0,
            'expected_revenue': 0,
            'confidence': 0,
            'recommendations': []
        }


class DemandForecastingEngine:
    """
    Advanced Demand Forecasting Engine using Machine Learning
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.cache_timeout = 3600  # 1 hour
    
    def forecast_demand(self, product_id: int, days: int = 30, forecast_days: int = 7) -> Dict[str, Any]:
        """Forecast demand for a specific product"""
        cache_key = f"demand_forecast_{product_id}_{days}_{forecast_days}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Get historical data
            historical_data = self._get_demand_data(product_id, days)
            
            if len(historical_data) < 14:  # Need at least 2 weeks of data
                return self._empty_demand_forecast()
            
            # Prepare time series data
            ts_data = self._prepare_time_series_data(historical_data)
            
            if len(ts_data) < 14:
                return self._empty_demand_forecast()
            
            # Train forecasting models
            models = self._train_forecasting_models(ts_data)
            
            # Generate forecast
            forecast = self._generate_forecast(models, ts_data, forecast_days)
            
            # Calculate forecast accuracy
            accuracy = self._calculate_forecast_accuracy(models, ts_data)
            
            # Generate demand insights
            insights = self._generate_demand_insights(ts_data, forecast)
            
            forecast_result = {
                'product_id': product_id,
                'forecast_days': forecast_days,
                'forecast': forecast,
                'accuracy': accuracy,
                'insights': insights,
                'historical_data': ts_data[-30:],  # Last 30 days
                'trend': self._calculate_trend(ts_data),
                'seasonality': self._detect_seasonality(ts_data),
                'generated_at': timezone.now().isoformat()
            }
            
            # Cache the result
            cache.set(cache_key, forecast_result, self.cache_timeout)
            
            return forecast_result
            
        except Exception as e:
            logger.error(f"Error forecasting demand for product {product_id}: {e}")
            return self._empty_demand_forecast()
    
    def batch_forecast_demand(self, product_ids: List[int], days: int = 30, forecast_days: int = 7) -> Dict[str, Any]:
        """Forecast demand for multiple products"""
        try:
            results = {}
            successful_forecasts = 0
            failed_forecasts = 0
            
            for product_id in product_ids:
                try:
                    result = self.forecast_demand(product_id, days, forecast_days)
                    if result.get('forecast'):
                        results[product_id] = result
                        successful_forecasts += 1
                    else:
                        failed_forecasts += 1
                except Exception as e:
                    logger.error(f"Error forecasting demand for product {product_id}: {e}")
                    failed_forecasts += 1
            
            return {
                'total_products': len(product_ids),
                'successful_forecasts': successful_forecasts,
                'failed_forecasts': failed_forecasts,
                'success_rate': (successful_forecasts / len(product_ids)) * 100,
                'results': results,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in batch demand forecasting: {e}")
            return {'error': str(e)}
    
    def _get_demand_data(self, product_id: int, days: int) -> List[Dict[str, Any]]:
        """Get historical demand data"""
        start_date = timezone.now() - timedelta(days=days)
        
        # Get purchase events for this product
        events = UserBehaviorEvent.objects.filter(
            object_id=product_id,
            event_type='purchase',
            timestamp__gte=start_date
        ).values('timestamp')
        
        # Aggregate by day
        daily_demand = {}
        for event in events:
            date = event['timestamp'].date()
            daily_demand[date] = daily_demand.get(date, 0) + 1
        
        # Convert to list
        demand_data = []
        for date, demand in daily_demand.items():
            demand_data.append({
                'date': date,
                'demand': demand,
                'timestamp': timezone.make_aware(datetime.combine(date, datetime.min.time()))
            })
        
        # Sort by date
        demand_data.sort(key=lambda x: x['date'])
        
        return demand_data
    
    def _prepare_time_series_data(self, demand_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare time series data for forecasting"""
        df = pd.DataFrame(demand_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()
        
        # Create additional features
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Create lag features
        df['demand_lag_1'] = df['demand'].shift(1)
        df['demand_lag_7'] = df['demand'].shift(7)
        df['demand_lag_14'] = df['demand'].shift(14)
        
        # Create moving averages
        df['demand_ma_3'] = df['demand'].rolling(window=3).mean()
        df['demand_ma_7'] = df['demand'].rolling(window=7).mean()
        df['demand_ma_14'] = df['demand'].rolling(window=14).mean()
        
        # Create trend features
        df['trend'] = np.arange(len(df))
        
        # Remove NaN values
        df = df.dropna()
        
        return df
    
    def _train_forecasting_models(self, ts_data: pd.DataFrame) -> Dict[str, Any]:
        """Train forecasting models"""
        try:
            if len(ts_data) < 14:
                return {'performance': {}, 'models': {}}
            
            # Prepare features and target
            feature_columns = [
                'day_of_week', 'month', 'quarter', 'is_weekend',
                'demand_lag_1', 'demand_lag_7', 'demand_lag_14',
                'demand_ma_3', 'demand_ma_7', 'demand_ma_14', 'trend'
            ]
            
            X = ts_data[feature_columns].values
            y = ts_data['demand'].values
            
            # Split data
            split_point = int(len(X) * 0.8)
            X_train, X_test = X[:split_point], X[split_point:]
            y_train, y_test = y[:split_point], y[split_point:]
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train models
            models = {
                'linear': LinearRegression(),
                'ridge': Ridge(alpha=1.0),
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
            }
            
            model_performance = {}
            trained_models = {}
            
            for name, model in models.items():
                try:
                    # Train model
                    if name in ['linear', 'ridge']:
                        model.fit(X_train_scaled, y_train)
                        y_pred = model.predict(X_test_scaled)
                    else:
                        model.fit(X_train, y_train)
                        y_pred = model.predict(X_test)
                    
                    # Calculate performance metrics
                    mse = mean_squared_error(y_test, y_pred)
                    mae = mean_absolute_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    
                    model_performance[name] = {
                        'mse': float(mse),
                        'mae': float(mae),
                        'r2': float(r2)
                    }
                    
                    trained_models[name] = model
                    
                except Exception as e:
                    logger.error(f"Error training {name} model: {e}")
                    continue
            
            # Select best model
            best_model_name = max(model_performance.keys(), key=lambda x: model_performance[x]['r2'])
            best_model = trained_models[best_model_name]
            
            return {
                'performance': model_performance,
                'models': trained_models,
                'best_model': best_model,
                'best_model_name': best_model_name,
                'scaler': scaler,
                'feature_columns': feature_columns
            }
            
        except Exception as e:
            logger.error(f"Error training forecasting models: {e}")
            return {'performance': {}, 'models': {}}
    
    def _generate_forecast(self, models: Dict, ts_data: pd.DataFrame, forecast_days: int) -> List[Dict[str, Any]]:
        """Generate demand forecast"""
        try:
            if not models.get('best_model'):
                return []
            
            best_model = models['best_model']
            scaler = models.get('scaler')
            feature_columns = models.get('feature_columns', [])
            
            forecast = []
            last_data = ts_data.iloc[-1].copy()
            
            for i in range(forecast_days):
                # Create feature vector for next day
                next_date = ts_data.index[-1] + timedelta(days=i+1)
                
                # Update features
                feature_vector = last_data[feature_columns].values.copy()
                feature_vector[0] = next_date.dayofweek  # day_of_week
                feature_vector[1] = next_date.month      # month
                feature_vector[2] = next_date.quarter    # quarter
                feature_vector[3] = 1 if next_date.dayofweek >= 5 else 0  # is_weekend
                feature_vector[10] = len(ts_data) + i    # trend
                
                # Predict demand
                if scaler:
                    feature_vector_scaled = scaler.transform([feature_vector])
                    predicted_demand = best_model.predict(feature_vector_scaled)[0]
                else:
                    predicted_demand = best_model.predict([feature_vector])[0]
                
                # Ensure non-negative demand
                predicted_demand = max(0, predicted_demand)
                
                forecast.append({
                    'date': next_date.date().isoformat(),
                    'predicted_demand': float(predicted_demand),
                    'confidence': 0.8 - (i * 0.1),  # Decreasing confidence over time
                    'day_of_week': next_date.dayofweek,
                    'is_weekend': next_date.dayofweek >= 5
                })
                
                # Update last_data for next iteration
                last_data['demand'] = predicted_demand
                last_data['demand_lag_1'] = last_data['demand']
                last_data['demand_lag_7'] = last_data['demand_lag_1']
                last_data['demand_lag_14'] = last_data['demand_lag_7']
                last_data['demand_ma_3'] = (last_data['demand_ma_3'] * 2 + predicted_demand) / 3
                last_data['demand_ma_7'] = (last_data['demand_ma_7'] * 6 + predicted_demand) / 7
                last_data['demand_ma_14'] = (last_data['demand_ma_14'] * 13 + predicted_demand) / 14
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return []
    
    def _calculate_forecast_accuracy(self, models: Dict, ts_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate forecast accuracy"""
        try:
            if not models.get('best_model'):
                return {'mae': 0.0, 'mse': 0.0, 'r2': 0.0}
            
            best_model_performance = models['performance'].get(models['best_model_name'], {})
            
            return {
                'mae': best_model_performance.get('mae', 0.0),
                'mse': best_model_performance.get('mse', 0.0),
                'r2': best_model_performance.get('r2', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error calculating forecast accuracy: {e}")
            return {'mae': 0.0, 'mse': 0.0, 'r2': 0.0}
    
    def _generate_demand_insights(self, ts_data: pd.DataFrame, forecast: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate demand insights"""
        insights = []
        
        try:
            # Calculate average demand
            avg_demand = ts_data['demand'].mean()
            forecast_avg = np.mean([f['predicted_demand'] for f in forecast])
            
            # Demand trend
            if forecast_avg > avg_demand * 1.1:
                insights.append({
                    'type': 'positive',
                    'title': 'Increasing Demand Trend',
                    'description': f"Forecasted demand is {((forecast_avg - avg_demand) / avg_demand * 100):.1f}% higher than historical average",
                    'priority': 'medium'
                })
            elif forecast_avg < avg_demand * 0.9:
                insights.append({
                    'type': 'negative',
                    'title': 'Decreasing Demand Trend',
                    'description': f"Forecasted demand is {((avg_demand - forecast_avg) / avg_demand * 100):.1f}% lower than historical average",
                    'priority': 'medium'
                })
            
            # Weekend vs weekday demand
            weekend_demand = ts_data[ts_data['is_weekend'] == 1]['demand'].mean()
            weekday_demand = ts_data[ts_data['is_weekend'] == 0]['demand'].mean()
            
            if weekend_demand > weekday_demand * 1.2:
                insights.append({
                    'type': 'info',
                    'title': 'Weekend Demand Pattern',
                    'description': "Demand is significantly higher on weekends",
                    'priority': 'low'
                })
            
            # Seasonal patterns
            monthly_demand = ts_data.groupby(ts_data.index.month)['demand'].mean()
            peak_month = monthly_demand.idxmax()
            low_month = monthly_demand.idxmin()
            
            if monthly_demand[peak_month] > monthly_demand[low_month] * 1.5:
                insights.append({
                    'type': 'info',
                    'title': 'Seasonal Demand Pattern',
                    'description': f"Demand peaks in month {peak_month} and is lowest in month {low_month}",
                    'priority': 'low'
                })
            
        except Exception as e:
            logger.error(f"Error generating demand insights: {e}")
        
        return insights
    
    def _calculate_trend(self, ts_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate demand trend"""
        try:
            if len(ts_data) < 7:
                return {'direction': 'stable', 'strength': 0.0}
            
            # Simple linear trend
            x = np.arange(len(ts_data))
            y = ts_data['demand'].values
            
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.1:
                direction = 'increasing'
                strength = min(1.0, slope / 10)
            elif slope < -0.1:
                direction = 'decreasing'
                strength = min(1.0, abs(slope) / 10)
            else:
                direction = 'stable'
                strength = 0.0
            
            return {
                'direction': direction,
                'strength': float(strength),
                'slope': float(slope)
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return {'direction': 'stable', 'strength': 0.0}
    
    def _detect_seasonality(self, ts_data: pd.DataFrame) -> Dict[str, Any]:
        """Detect seasonality patterns"""
        try:
            if len(ts_data) < 14:
                return {'has_seasonality': False, 'pattern': 'none'}
            
            # Check for weekly seasonality
            weekly_demand = ts_data.groupby(ts_data.index.dayofweek)['demand'].mean()
            weekly_variance = weekly_demand.var()
            
            # Check for monthly seasonality
            monthly_demand = ts_data.groupby(ts_data.index.month)['demand'].mean()
            monthly_variance = monthly_demand.var()
            
            if weekly_variance > monthly_variance * 1.5:
                return {
                    'has_seasonality': True,
                    'pattern': 'weekly',
                    'variance': float(weekly_variance)
                }
            elif monthly_variance > weekly_variance * 1.5:
                return {
                    'has_seasonality': True,
                    'pattern': 'monthly',
                    'variance': float(monthly_variance)
                }
            else:
                return {
                    'has_seasonality': False,
                    'pattern': 'none',
                    'variance': 0.0
                }
                
        except Exception as e:
            logger.error(f"Error detecting seasonality: {e}")
            return {'has_seasonality': False, 'pattern': 'none', 'variance': 0.0}
    
    def _empty_demand_forecast(self) -> Dict[str, Any]:
        """Return empty demand forecast"""
        return {
            'product_id': 0,
            'forecast_days': 0,
            'forecast': [],
            'accuracy': {'mae': 0.0, 'mse': 0.0, 'r2': 0.0},
            'insights': [],
            'historical_data': [],
            'trend': {'direction': 'stable', 'strength': 0.0},
            'seasonality': {'has_seasonality': False, 'pattern': 'none'},
            'generated_at': timezone.now().isoformat()
        }

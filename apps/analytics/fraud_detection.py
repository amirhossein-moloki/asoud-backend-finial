"""
Fraud Detection and Customer Segmentation Engine for ASOUD Platform
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Try to import sklearn components with fallback
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    # Create dummy classes for when sklearn is not available
    class IsolationForest:
        def __init__(self, **kwargs):
            pass
        def fit(self, X):
            return self
        def predict(self, X):
            return np.ones(len(X))
        def decision_function(self, X):
            return np.zeros(len(X))
    
    class KMeans:
        def __init__(self, **kwargs):
            pass
        def fit(self, X):
            return self
        def predict(self, X):
            return np.zeros(len(X))
    
    class StandardScaler:
        def __init__(self):
            pass
        def fit(self, X):
            return self
        def transform(self, X):
            return X
        def fit_transform(self, X):
            return X


class FraudDetectionEngine:
    """
    Advanced fraud detection engine using machine learning
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def detect_fraud(self, transaction_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect fraudulent transactions
        """
        try:
            if not transaction_data:
                return {
                    'fraud_count': 0,
                    'fraud_percentage': 0.0,
                    'fraud_transactions': [],
                    'risk_scores': []
                }
            
            # Convert to DataFrame
            df = pd.DataFrame(transaction_data)
            
            # Feature engineering
            features = self._extract_features(df)
            
            if not self.is_trained:
                # Train model if not already trained
                self._train_fraud_model(features)
            
            if self.model is None:
                # Fallback to rule-based detection
                return self._rule_based_fraud_detection(df)
            
            # Predict fraud
            fraud_predictions = self.model.predict(features)
            fraud_scores = self.model.decision_function(features)
            
            # Identify fraudulent transactions
            fraud_indices = np.where(fraud_predictions == -1)[0]
            fraud_transactions = df.iloc[fraud_indices].to_dict('records')
            
            return {
                'fraud_count': len(fraud_indices),
                'fraud_percentage': (len(fraud_indices) / len(df)) * 100,
                'fraud_transactions': fraud_transactions,
                'risk_scores': fraud_scores.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in fraud detection: {str(e)}")
            return self._rule_based_fraud_detection(transaction_data)
    
    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extract features for fraud detection
        """
        try:
            features = []
            
            # Amount-based features
            if 'amount' in df.columns:
                features.append(df['amount'].values)
                features.append(np.log1p(df['amount'].values))  # Log transform
            else:
                features.append(np.zeros(len(df)))
                features.append(np.zeros(len(df)))
            
            # Time-based features
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['hour'] = df['timestamp'].dt.hour
                df['day_of_week'] = df['timestamp'].dt.dayofweek
                features.append(df['hour'].values)
                features.append(df['day_of_week'].values)
            else:
                features.append(np.zeros(len(df)))
                features.append(np.zeros(len(df)))
            
            # User-based features (if available)
            if 'user_id' in df.columns:
                user_counts = df['user_id'].value_counts()
                df['user_frequency'] = df['user_id'].map(user_counts)
                features.append(df['user_frequency'].values)
            else:
                features.append(np.zeros(len(df)))
            
            # Combine features
            feature_matrix = np.column_stack(features)
            
            # Handle NaN values
            feature_matrix = np.nan_to_num(feature_matrix, nan=0.0)
            
            return feature_matrix
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            # Return dummy features
            return np.zeros((len(df), 5))
    
    def _train_fraud_model(self, historical_data: np.ndarray) -> Optional[IsolationForest]:
        """
        Train the fraud detection model
        """
        try:
            if not HAS_SKLEARN or len(historical_data) < 10:
                self.is_trained = True
                return None
            
            # Scale features
            scaled_data = self.scaler.fit_transform(historical_data)
            
            # Train Isolation Forest
            self.model = IsolationForest(
                contamination=0.1,  # Assume 10% fraud rate
                random_state=42,
                n_estimators=100
            )
            
            self.model.fit(scaled_data)
            self.is_trained = True
            
            logger.info("Fraud detection model trained successfully")
            return self.model
            
        except Exception as e:
            logger.error(f"Error training fraud model: {str(e)}")
            self.is_trained = True
            return None
    
    def _rule_based_fraud_detection(self, transaction_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback rule-based fraud detection
        """
        try:
            if isinstance(transaction_data, pd.DataFrame):
                df = transaction_data
            else:
                df = pd.DataFrame(transaction_data)
            
            fraud_transactions = []
            
            # Rule 1: High amount transactions
            if 'amount' in df.columns:
                high_amount_threshold = df['amount'].quantile(0.95)
                high_amount_fraud = df[df['amount'] > high_amount_threshold]
                fraud_transactions.extend(high_amount_fraud.to_dict('records'))
            
            # Rule 2: Multiple transactions in short time
            if 'timestamp' in df.columns and 'user_id' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df_sorted = df.sort_values(['user_id', 'timestamp'])
                
                # Find users with multiple transactions within 1 hour
                df_sorted['time_diff'] = df_sorted.groupby('user_id')['timestamp'].diff()
                rapid_transactions = df_sorted[df_sorted['time_diff'] < timedelta(hours=1)]
                fraud_transactions.extend(rapid_transactions.to_dict('records'))
            
            # Remove duplicates
            fraud_transactions = list({str(item): item for item in fraud_transactions}.values())
            
            return {
                'fraud_count': len(fraud_transactions),
                'fraud_percentage': (len(fraud_transactions) / len(df)) * 100 if len(df) > 0 else 0,
                'fraud_transactions': fraud_transactions,
                'risk_scores': [0.5] * len(fraud_transactions)
            }
            
        except Exception as e:
            logger.error(f"Error in rule-based fraud detection: {str(e)}")
            return {
                'fraud_count': 0,
                'fraud_percentage': 0.0,
                'fraud_transactions': [],
                'risk_scores': []
            }


class CustomerSegmentationEngine:
    """
    Customer segmentation engine using clustering
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def segment_customers(self, customer_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Segment customers into different groups
        """
        try:
            if not customer_data:
                return {
                    'segments': {},
                    'segment_counts': {},
                    'segment_percentages': {}
                }
            
            # Convert to DataFrame
            df = pd.DataFrame(customer_data)
            
            # Feature engineering
            features = self._extract_customer_features(df)
            
            if not self.is_trained:
                # Train model if not already trained
                self._train_segmentation_model(features)
            
            if self.model is None:
                # Fallback to rule-based segmentation
                return self._rule_based_segmentation(df)
            
            # Predict segments
            segments = self.model.predict(features)
            
            # Add segments to dataframe
            df['segment'] = segments
            
            # Calculate segment statistics
            segment_counts = df['segment'].value_counts().to_dict()
            total_customers = len(df)
            segment_percentages = {
                str(segment): (count / total_customers) * 100 
                for segment, count in segment_counts.items()
            }
            
            # Group customers by segment
            segments_dict = {}
            for segment in df['segment'].unique():
                segment_customers = df[df['segment'] == segment].to_dict('records')
                segments_dict[str(segment)] = segment_customers
            
            return {
                'segments': segments_dict,
                'segment_counts': segment_counts,
                'segment_percentages': segment_percentages
            }
            
        except Exception as e:
            logger.error(f"Error in customer segmentation: {str(e)}")
            return self._rule_based_segmentation(customer_data)
    
    def _extract_customer_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extract features for customer segmentation
        """
        try:
            features = []
            
            # Transaction frequency
            if 'transaction_count' in df.columns:
                features.append(df['transaction_count'].values)
            else:
                features.append(np.zeros(len(df)))
            
            # Total amount spent
            if 'total_amount' in df.columns:
                features.append(df['total_amount'].values)
                features.append(np.log1p(df['total_amount'].values))  # Log transform
            else:
                features.append(np.zeros(len(df)))
                features.append(np.zeros(len(df)))
            
            # Average transaction amount
            if 'avg_transaction_amount' in df.columns:
                features.append(df['avg_transaction_amount'].values)
            else:
                features.append(np.zeros(len(df)))
            
            # Days since last transaction
            if 'days_since_last_transaction' in df.columns:
                features.append(df['days_since_last_transaction'].values)
            else:
                features.append(np.zeros(len(df)))
            
            # Combine features
            feature_matrix = np.column_stack(features)
            
            # Handle NaN values
            feature_matrix = np.nan_to_num(feature_matrix, nan=0.0)
            
            return feature_matrix
            
        except Exception as e:
            logger.error(f"Error extracting customer features: {str(e)}")
            # Return dummy features
            return np.zeros((len(df), 4))
    
    def _train_segmentation_model(self, customer_data: np.ndarray) -> Optional[KMeans]:
        """
        Train the customer segmentation model
        """
        try:
            if not HAS_SKLEARN or len(customer_data) < 10:
                self.is_trained = True
                return None
            
            # Scale features
            scaled_data = self.scaler.fit_transform(customer_data)
            
            # Determine optimal number of clusters
            n_clusters = min(5, max(2, len(customer_data) // 10))
            
            # Train K-Means
            self.model = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10
            )
            
            self.model.fit(scaled_data)
            self.is_trained = True
            
            logger.info(f"Customer segmentation model trained with {n_clusters} clusters")
            return self.model
            
        except Exception as e:
            logger.error(f"Error training segmentation model: {str(e)}")
            self.is_trained = True
            return None
    
    def _rule_based_segmentation(self, customer_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback rule-based customer segmentation
        """
        try:
            if isinstance(customer_data, pd.DataFrame):
                df = customer_data
            else:
                df = pd.DataFrame(customer_data)
            
            # Simple rule-based segmentation
            segments = []
            
            for _, row in df.iterrows():
                total_amount = row.get('total_amount', 0)
                transaction_count = row.get('transaction_count', 0)
                
                if total_amount > 10000 and transaction_count > 50:
                    segments.append('VIP')
                elif total_amount > 5000 and transaction_count > 20:
                    segments.append('Premium')
                elif total_amount > 1000 and transaction_count > 10:
                    segments.append('Regular')
                else:
                    segments.append('Basic')
            
            df['segment'] = segments
            
            # Calculate segment statistics
            segment_counts = df['segment'].value_counts().to_dict()
            total_customers = len(df)
            segment_percentages = {
                segment: (count / total_customers) * 100 
                for segment, count in segment_counts.items()
            }
            
            # Group customers by segment
            segments_dict = {}
            for segment in df['segment'].unique():
                segment_customers = df[df['segment'] == segment].to_dict('records')
                segments_dict[segment] = segment_customers
            
            return {
                'segments': segments_dict,
                'segment_counts': segment_counts,
                'segment_percentages': segment_percentages
            }
            
        except Exception as e:
            logger.error(f"Error in rule-based segmentation: {str(e)}")
            return {
                'segments': {},
                'segment_counts': {},
                'segment_percentages': {}
            }


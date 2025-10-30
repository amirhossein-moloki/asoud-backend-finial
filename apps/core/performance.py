"""
Performance Optimization Utilities for ASOUD Platform
"""

import time
import logging
from functools import wraps
from django.core.cache import cache
from django.db import connection, transaction
from django.db.models import Q, Prefetch, F, Count, Sum, Avg, Max, Min
from django.db.models.functions import Coalesce
from django.conf import settings
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework.response import Response
from rest_framework import status
import redis
try:
    from celery import shared_task
except ImportError:
    # Celery not available, define a dummy decorator
    def shared_task(func):
        return func

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """
    Database query optimization utilities
    """
    
    @staticmethod
    def optimize_queryset(queryset, select_related=None, prefetch_related=None, only=None, defer=None):
        """Optimize queryset with select_related and prefetch_related"""
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        if only:
            queryset = queryset.only(*only)
        
        if defer:
            queryset = queryset.defer(*defer)
        
        return queryset
    
    @staticmethod
    def get_optimized_products():
        """Get optimized products queryset"""
        from apps.product.models import Product
        
        return Product.objects.select_related(
            'market',
            'market__owner',
            'category',
            'sub_category'
        ).prefetch_related(
            'images',
            'discounts',
            'keywords',
            'comments'
        ).only(
            'id', 'name', 'description', 'price', 'stock', 'status',
            'market__name', 'market__business_id', 'category__name'
        )
    
    @staticmethod
    def get_optimized_markets():
        """Get optimized markets queryset"""
        from apps.market.models import Market
        
        return Market.objects.select_related(
            'owner',
            'sub_category',
            'location',
            'contact'
        ).prefetch_related(
            'products',
            'viewed_by'
        ).only(
            'id', 'name', 'business_id', 'description', 'is_verified',
            'owner__first_name', 'owner__last_name', 'sub_category__name'
        )
    
    @staticmethod
    def get_optimized_orders():
        """Get optimized orders queryset"""
        from apps.cart.models import Order
        
        return Order.objects.select_related(
            'user',
            'market'
        ).prefetch_related(
            'items',
            'items__product',
            'items__affiliate'
        ).only(
            'id', 'description', 'status', 'is_paid', 'created_at',
            'user__first_name', 'user__last_name', 'market__name'
        )

class CacheManager:
    """
    Advanced caching utilities
    """
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
    
    def get_or_set(self, key, callable_func, timeout=300):
        """Get from cache or set if not exists"""
        value = cache.get(key)
        if value is None:
            value = callable_func()
            cache.set(key, value, timeout)
        return value
    
    def get_or_set_async(self, key, task_name, args=None, kwargs=None, timeout=300):
        """Get from cache or trigger async task"""
        value = cache.get(key)
        if value is None:
            # Trigger async task
            from celery import current_app
            current_app.send_task(task_name, args=args, kwargs=kwargs)
            return None
        return value
    
    def invalidate_pattern(self, pattern):
        """Invalidate cache keys matching pattern"""
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
    
    def warm_cache(self, cache_keys):
        """Warm up cache with frequently accessed data"""
        for key, data, timeout in cache_keys:
            cache.set(key, data, timeout)
    
    def get_cache_stats(self):
        """Get cache statistics"""
        info = self.redis_client.info()
        return {
            'used_memory': info.get('used_memory_human'),
            'connected_clients': info.get('connected_clients'),
            'total_commands_processed': info.get('total_commands_processed'),
            'keyspace_hits': info.get('keyspace_hits'),
            'keyspace_misses': info.get('keyspace_misses'),
        }

class QueryProfiler:
    """
    Enhanced query profiling and optimization
    """
    
    def __init__(self):
        self.queries = []
        self.start_time = None
        self.slow_query_threshold = 0.1  # 100ms
        self.max_queries_warning = 20
    
    def __enter__(self):
        self.start_time = time.time()
        self.queries = []
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        execution_time = end_time - self.start_time
        query_count = len(connection.queries)
        
        # Log performance metrics
        logger.info(f"Query execution time: {execution_time:.2f}s")
        logger.info(f"Number of queries: {query_count}")
        
        # Check for N+1 queries
        if query_count > self.max_queries_warning:
            logger.warning(f"Potential N+1 query problem: {query_count} queries executed")
        
        # Log slow queries
        slow_queries = []
        for query in connection.queries:
            query_time = float(query['time'])
            if query_time > self.slow_query_threshold:
                slow_queries.append({
                    'sql': query['sql'][:200] + '...' if len(query['sql']) > 200 else query['sql'],
                    'time': query_time,
                    'params': query.get('params', [])
                })
                logger.warning(f"Slow query: {query['sql'][:100]}... (Time: {query_time:.3f}s)")
        
        # Log query analysis
        if slow_queries:
            logger.warning(f"Found {len(slow_queries)} slow queries")
            self._analyze_slow_queries(slow_queries)
        
        # Log query efficiency
        if query_count > 0:
            avg_query_time = sum(float(q['time']) for q in connection.queries) / query_count
            logger.info(f"Average query time: {avg_query_time:.3f}s")
            
            if avg_query_time > 0.05:  # 50ms
                logger.warning("Average query time is high, consider optimization")
    
    def _analyze_slow_queries(self, slow_queries):
        """Analyze slow queries for optimization opportunities"""
        for query in slow_queries:
            sql = query['sql'].lower()
            
            # Check for missing indexes
            if 'where' in sql and 'order by' in sql:
                logger.warning("Query with WHERE and ORDER BY - check for composite indexes")
            
            if 'join' in sql and 'on' in sql:
                logger.warning("Query with JOINs - check for proper foreign key indexes")
            
            if 'group by' in sql and 'having' in sql:
                logger.warning("Query with GROUP BY and HAVING - check for aggregation indexes")
            
            if 'like' in sql and '%' in sql:
                logger.warning("Query with LIKE pattern - consider full-text search indexes")
    
    @staticmethod
    def log_query_count():
        """Log current query count"""
        query_count = len(connection.queries)
        logger.info(f"Current query count: {query_count}")
        
        if query_count > 20:
            logger.warning(f"High query count: {query_count} - potential N+1 problem")
    
    @staticmethod
    def get_query_count():
        """Get current query count"""
        return len(connection.queries)
    
    @staticmethod
    def get_slow_queries(threshold=0.1):
        """Get queries slower than threshold"""
        slow_queries = []
        for query in connection.queries:
            if float(query['time']) > threshold:
                slow_queries.append(query)
        return slow_queries
    
    @staticmethod
    def analyze_query_patterns():
        """Analyze query patterns for optimization opportunities"""
        queries = connection.queries
        patterns = {
            'select_count': 0,
            'select_related': 0,
            'prefetch_related': 0,
            'filter': 0,
            'exclude': 0,
            'order_by': 0,
            'annotate': 0,
            'aggregate': 0,
        }
        
        for query in queries:
            sql = query['sql'].lower()
            
            if 'select count(' in sql:
                patterns['select_count'] += 1
            if 'select_related' in sql:
                patterns['select_related'] += 1
            if 'prefetch_related' in sql:
                patterns['prefetch_related'] += 1
            if 'where' in sql:
                patterns['filter'] += 1
            if 'order by' in sql:
                patterns['order_by'] += 1
            if 'group by' in sql:
                patterns['annotate'] += 1
        
        logger.info("Query patterns analysis:")
        for pattern, count in patterns.items():
            logger.info(f"  {pattern}: {count}")
        
        # Recommendations
        if patterns['select_count'] > 5:
            logger.warning("High number of COUNT queries - consider caching")
        
        if patterns['select_related'] == 0 and patterns['prefetch_related'] == 0:
            logger.warning("No select_related/prefetch_related usage - potential N+1 queries")
        
        if patterns['filter'] > patterns['select_related'] * 2:
            logger.warning("Many WHERE clauses without select_related - check for missing joins")

class PaginationOptimizer:
    """
    Optimized pagination utilities
    """
    
    @staticmethod
    def get_optimized_paginator(queryset, page_size=20, page_number=1):
        """Get optimized paginator"""
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)
        
        return {
            'results': page.object_list,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page.number,
            'has_next': page.has_next(),
            'has_previous': page.has_previous(),
            'next_page': page.next_page_number() if page.has_next() else None,
            'previous_page': page.previous_page_number() if page.has_previous() else None,
        }
    
    @staticmethod
    def get_cursor_pagination(queryset, cursor=None, page_size=20):
        """Get cursor-based pagination for better performance"""
        if cursor:
            queryset = queryset.filter(id__gt=cursor)
        
        items = list(queryset[:page_size + 1])
        has_next = len(items) > page_size
        
        if has_next:
            items = items[:-1]
            next_cursor = items[-1].id
        else:
            next_cursor = None
        
        return {
            'results': items,
            'next_cursor': next_cursor,
            'has_next': has_next,
        }

class PerformanceDecorators:
    """
    Performance monitoring decorators
    """
    
    @staticmethod
    def measure_time(func):
        """Measure function execution time"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            logger.info(f"{func.__name__} executed in {end_time - start_time:.2f}s")
            return result
        return wrapper
    
    @staticmethod
    def cache_result(timeout=300):
        """Cache function result"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                result = cache.get(cache_key)
                
                if result is None:
                    result = func(*args, **kwargs)
                    cache.set(cache_key, result, timeout)
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def rate_limit(max_calls=100, time_window=60):
        """Rate limit function calls"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = f"rate_limit:{func.__name__}:{time.time() // time_window}"
                current_calls = cache.get(cache_key, 0)
                
                if current_calls >= max_calls:
                    raise Exception("Rate limit exceeded")
                
                cache.set(cache_key, current_calls + 1, time_window)
                return func(*args, **kwargs)
            return wrapper
        return decorator

class DatabaseIndexes:
    """
    Database index management
    """
    
    @staticmethod
    def create_optimized_indexes():
        """Create optimized database indexes"""
        from django.db import connection
        
        indexes = [
            # User indexes
            "CREATE INDEX IF NOT EXISTS idx_user_mobile ON users_user(mobile_number);",
            "CREATE INDEX IF NOT EXISTS idx_user_email ON users_user(email);",
            "CREATE INDEX IF NOT EXISTS idx_user_owner ON users_user(is_owner);",
            "CREATE INDEX IF NOT EXISTS idx_user_verified ON users_user(is_verified);",
            "CREATE INDEX IF NOT EXISTS idx_user_active ON users_user(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_user_created ON users_user(created_at);",
            
            # Product indexes
            "CREATE INDEX IF NOT EXISTS idx_product_market ON apps_product(market_id);",
            "CREATE INDEX IF NOT EXISTS idx_product_category ON apps_product(category_id);",
            "CREATE INDEX IF NOT EXISTS idx_product_subcategory ON apps_product(sub_category_id);",
            "CREATE INDEX IF NOT EXISTS idx_product_status ON apps_product(status);",
            "CREATE INDEX IF NOT EXISTS idx_product_price ON apps_product(price);",
            "CREATE INDEX IF NOT EXISTS idx_product_stock ON apps_product(stock);",
            "CREATE INDEX IF NOT EXISTS idx_product_created ON apps_product(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_product_name ON apps_product(name);",
            
            # Market indexes
            "CREATE INDEX IF NOT EXISTS idx_market_owner ON apps_market(owner_id);",
            "CREATE INDEX IF NOT EXISTS idx_market_business_id ON apps_market(business_id);",
            "CREATE INDEX IF NOT EXISTS idx_market_verified ON apps_market(is_verified);",
            "CREATE INDEX IF NOT EXISTS idx_market_subcategory ON apps_market(sub_category_id);",
            "CREATE INDEX IF NOT EXISTS idx_market_created ON apps_market(created_at);",
            
            # Order indexes
            "CREATE INDEX IF NOT EXISTS idx_order_user ON apps_cart_order(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_order_market ON apps_cart_order(market_id);",
            "CREATE INDEX IF NOT EXISTS idx_order_status ON apps_cart_order(status);",
            "CREATE INDEX IF NOT EXISTS idx_order_paid ON apps_cart_order(is_paid);",
            "CREATE INDEX IF NOT EXISTS idx_order_created ON apps_cart_order(created_at);",
            
            # OrderItem indexes
            "CREATE INDEX IF NOT EXISTS idx_orderitem_order ON apps_cart_orderitem(order_id);",
            "CREATE INDEX IF NOT EXISTS idx_orderitem_product ON apps_cart_orderitem(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_orderitem_affiliate ON apps_cart_orderitem(affiliate_id);",
            
            # Payment indexes
            "CREATE INDEX IF NOT EXISTS idx_payment_user ON apps_payment_payment(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_payment_status ON apps_payment_payment(status);",
            "CREATE INDEX IF NOT EXISTS idx_payment_created ON apps_payment_payment(created_at);",
            
            # Wallet indexes
            "CREATE INDEX IF NOT EXISTS idx_wallet_user ON apps_wallet_wallet(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_wallet_active ON apps_wallet_wallet(is_active);",
            
            # Transaction indexes
            "CREATE INDEX IF NOT EXISTS idx_transaction_user ON apps_wallet_transaction(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_from_wallet ON apps_wallet_transaction(from_wallet_id);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_to_wallet ON apps_wallet_transaction(to_wallet_id);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_action ON apps_wallet_transaction(action);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_created ON apps_wallet_transaction(created_at);",
            
            # Composite indexes
            "CREATE INDEX IF NOT EXISTS idx_product_market_status ON apps_product(market_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_order_user_status ON apps_cart_order(user_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_payment_user_status ON apps_payment_payment(user_id, status);",
        ]
        
        with connection.cursor() as cursor:
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    logger.info(f"Created index: {index_sql}")
                except Exception as e:
                    logger.error(f"Failed to create index: {e}")
    
    @staticmethod
    def analyze_query_performance():
        """Analyze query performance"""
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Get slow queries
            cursor.execute("""
                SELECT query, mean_time, calls, total_time
                FROM pg_stat_statements
                WHERE mean_time > 100
                ORDER BY mean_time DESC
                LIMIT 10;
            """)
            
            slow_queries = cursor.fetchall()
            
            logger.info("Slow queries analysis:")
            for query in slow_queries:
                logger.info(f"Query: {query[0][:100]}...")
                logger.info(f"Mean time: {query[1]}ms, Calls: {query[2]}, Total time: {query[3]}ms")

class AsyncTaskManager:
    """
    Async task management for performance
    """
    
    @staticmethod
    @shared_task
    def warm_cache_products():
        """Warm up product cache"""
        from apps.product.models import Product
        from apps.core.performance import CacheManager
        
        cache_manager = CacheManager()
        
        # Cache popular products
        popular_products = Product.objects.filter(
            status='published'
        ).order_by('-view_count')[:100]
        
        cache_manager.warm_cache([
            ('popular_products', list(popular_products.values()), 3600),
        ])
    
    @staticmethod
    @shared_task
    def warm_cache_markets():
        """Warm up market cache"""
        from apps.market.models import Market
        from apps.core.performance import CacheManager
        
        cache_manager = CacheManager()
        
        # Cache verified markets
        verified_markets = Market.objects.filter(
            is_verified=True
        ).order_by('-created_at')[:50]
        
        cache_manager.warm_cache([
            ('verified_markets', list(verified_markets.values()), 3600),
        ])
    
    @staticmethod
    @shared_task
    def cleanup_old_sessions():
        """Clean up old user sessions"""
        from apps.users.models import UserSession
        from django.utils import timezone
        from datetime import timedelta
        
        # Delete sessions older than 30 days
        old_sessions = UserSession.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=30)
        )
        
        deleted_count = old_sessions.count()
        old_sessions.delete()
        
        logger.info(f"Cleaned up {deleted_count} old sessions")
    
    @staticmethod
    @shared_task
    def generate_analytics():
        """Generate analytics data"""
        from apps.product.models import Product
        from apps.market.models import Market
        from apps.cart.models import Order
        
        # Product analytics
        product_stats = Product.objects.aggregate(
            total_products=Count('id'),
            published_products=Count('id', filter=Q(status='published')),
            average_price=Avg('price'),
            total_stock=Sum('stock')
        )
        
        # Market analytics
        market_stats = Market.objects.aggregate(
            total_markets=Count('id'),
            verified_markets=Count('id', filter=Q(is_verified=True)),
        )
        
        # Order analytics
        order_stats = Order.objects.aggregate(
            total_orders=Count('id'),
            paid_orders=Count('id', filter=Q(is_paid=True)),
            total_revenue=Sum('total_price', filter=Q(is_paid=True))
        )
        
        analytics_data = {
            'products': product_stats,
            'markets': market_stats,
            'orders': order_stats,
            'generated_at': timezone.now().isoformat()
        }
        
        cache.set('analytics_data', analytics_data, 3600)  # Cache for 1 hour
        logger.info("Analytics data generated and cached")

class MemoryOptimizer:
    """
    Memory optimization utilities
    """
    
    @staticmethod
    def optimize_queryset_memory(queryset, batch_size=1000):
        """Process queryset in batches to optimize memory"""
        total_count = queryset.count()
        
        for i in range(0, total_count, batch_size):
            batch = queryset[i:i + batch_size]
            yield batch
    
    @staticmethod
    def get_memory_usage():
        """Get current memory usage"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
            'percent': process.memory_percent()
        }
    
    @staticmethod
    def log_memory_usage():
        """Log current memory usage"""
        memory_usage = MemoryOptimizer.get_memory_usage()
        logger.info(f"Memory usage: RSS={memory_usage['rss']:.2f}MB, "
                   f"VMS={memory_usage['vms']:.2f}MB, "
                   f"Percent={memory_usage['percent']:.2f}%")



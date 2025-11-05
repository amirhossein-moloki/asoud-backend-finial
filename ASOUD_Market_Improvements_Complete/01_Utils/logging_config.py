"""
Logging Configuration System for Market Registration
سیستم کامل Logging برای ثبت رویدادها، خطاها، تراکنش‌ها و رویدادهای امنیتی
"""

import os
import logging
import logging.handlers
from datetime import datetime
from django.conf import settings


def setup_logging():
    """
    راه‌اندازی سیستم Logging کامل
    
    ایجاد Log Files جداگانه برای:
    - Errors (خطاها)
    - Info (اطلاعات عمومی)
    - Payment (تراکنش‌های مالی)
    - Security (رویدادهای امنیتی)
    """
    
    # ایجاد پوشه logs
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # مسیر فایل‌های Log
    error_log_file = os.path.join(log_dir, 'market_errors.log')
    info_log_file = os.path.join(log_dir, 'market_info.log')
    payment_log_file = os.path.join(log_dir, 'payment_transactions.log')
    security_log_file = os.path.join(log_dir, 'security_events.log')
    debug_log_file = os.path.join(log_dir, 'market_debug.log')
    
    # فرمت Log
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # تنظیم Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    root_logger.handlers.clear()
    
    # Console Handler برای Development
    if settings.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(console_handler)
    
    # Market Logger
    market_logger = logging.getLogger('market')
    market_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    market_logger.propagate = False
    
    # Error Handler (Rotating - 10MB, 5 backup)
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    market_logger.addHandler(error_handler)
    
    # Info Handler
    info_handler = logging.handlers.RotatingFileHandler(
        info_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(detailed_formatter)
    market_logger.addHandler(info_handler)
    
    # Debug Handler (فقط در DEBUG mode)
    if settings.DEBUG:
        debug_handler = logging.handlers.RotatingFileHandler(
            debug_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(detailed_formatter)
        market_logger.addHandler(debug_handler)
    
    # Payment Logger
    payment_logger = logging.getLogger('payment')
    payment_logger.setLevel(logging.INFO)
    payment_logger.propagate = False
    
    payment_handler = logging.handlers.RotatingFileHandler(
        payment_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,  # نگه داشتن Log‌های بیشتر برای تراکنش‌ها
        encoding='utf-8'
    )
    payment_handler.setLevel(logging.INFO)
    payment_handler.setFormatter(detailed_formatter)
    payment_logger.addHandler(payment_handler)
    
    # Security Logger
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.WARNING)
    security_logger.propagate = False
    
    security_handler = logging.handlers.RotatingFileHandler(
        security_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,  # نگه داشتن Log‌های بیشتر برای امنیت
        encoding='utf-8'
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(detailed_formatter)
    security_logger.addHandler(security_handler)
    
    return {
        'market': market_logger,
        'payment': payment_logger,
        'security': security_logger,
    }


def log_info(message: str, context: dict = None, user=None):
    """
    ثبت اطلاعات عمومی
    
    Args:
        message: پیام اطلاعاتی
        context: اطلاعات اضافی
        user: کاربر (اختیاری)
    """
    logger = logging.getLogger('market')
    context = context or {}
    info = {
        'message': message,
        'context': context,
    }
    if user:
        info['user'] = {
            'id': user.id if user and user.is_authenticated else None,
            'username': user.username if user and user.is_authenticated else 'anonymous',
        }
    logger.info(f"Market Info: {info}")


def log_error(error: Exception, context: dict = None, user=None):
    """
    ثبت خطا با جزئیات کامل
    
    Args:
        error: Exception رخ داده
        context: اطلاعات اضافی
        user: کاربر (اختیاری)
    """
    import traceback
    logger = logging.getLogger('market')
    context = context or {}
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        'context': context,
    }
    if user:
        error_info['user'] = {
            'id': user.id if user and user.is_authenticated else None,
            'username': user.username if user and user.is_authenticated else 'anonymous',
        }
    logger.error(f"Market Error: {error_info}")


def log_warning(message: str, context: dict = None, user=None):
    """
    ثبت هشدار
    
    Args:
        message: پیام هشدار
        context: اطلاعات اضافی
        user: کاربر (اختیاری)
    """
    logger = logging.getLogger('market')
    context = context or {}
    warning_info = {
        'message': message,
        'context': context,
    }
    if user:
        warning_info['user'] = {
            'id': user.id if user and user.is_authenticated else None,
            'username': user.username if user and user.is_authenticated else 'anonymous',
        }
    logger.warning(f"Market Warning: {warning_info}")


def log_user_action(user, action, model_name=None, object_id=None, details=None):
    """
    ثبت اعمال کاربر برای Audit Trail
    
    Args:
        user: کاربر
        action: عمل انجام شده (CREATE, UPDATE, DELETE, VIEW)
        model_name: نام مدل
        object_id: ID شیء
        details: جزئیات اضافی
    """
    logger = logging.getLogger('market')
    log_data = {
        'user_id': user.id if user and user.is_authenticated else None,
        'username': user.username if user and user.is_authenticated else 'anonymous',
        'action': action,
        'model': model_name,
        'object_id': object_id,
        'details': details,
        'timestamp': datetime.now().isoformat(),
    }
    logger.info(f"User Action: {log_data}")


def log_payment_transaction(transaction_data):
    """
    ثبت تراکنش‌های مالی
    
    Args:
        transaction_data: اطلاعات تراکنش (dict)
    """
    payment_logger = logging.getLogger('payment')
    log_data = {
        'transaction_id': transaction_data.get('transaction_id'),
        'user_id': transaction_data.get('user_id'),
        'amount': transaction_data.get('amount'),
        'gateway': transaction_data.get('gateway'),
        'status': transaction_data.get('status'),
        'timestamp': datetime.now().isoformat(),
        'details': transaction_data.get('details', {}),
    }
    payment_logger.info(f"Payment Transaction: {log_data}")


def log_security_event(event_type, user=None, ip_address=None, details=None):
    """
    ثبت رویدادهای امنیتی
    
    Args:
        event_type: نوع رویداد امنیتی
        user: کاربر (اختیاری)
        ip_address: آدرس IP
        details: جزئیات اضافی
    """
    security_logger = logging.getLogger('security')
    log_data = {
        'event_type': event_type,
        'user_id': user.id if user and user.is_authenticated else None,
        'username': user.username if user and user.is_authenticated else 'anonymous',
        'ip_address': ip_address,
        'timestamp': datetime.now().isoformat(),
        'details': details or {},
    }
    security_logger.warning(f"Security Event: {log_data}")


# Initialize logging when module is imported
if hasattr(settings, 'BASE_DIR'):
    setup_logging()


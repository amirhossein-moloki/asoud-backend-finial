import os
import logging
import logging.handlers
from datetime import datetime
from django.conf import settings


def setup_logging():
    """
    Setup comprehensive logging configuration for the office registration system
    """
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Define log file paths
    error_log_file = os.path.join(log_dir, 'office_registration_errors.log')
    info_log_file = os.path.join(log_dir, 'office_registration_info.log')
    debug_log_file = os.path.join(log_dir, 'office_registration_debug.log')
    payment_log_file = os.path.join(log_dir, 'payment_transactions.log')
    security_log_file = os.path.join(log_dir, 'security_events.log')
    
    # Define log format
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler for development
    if settings.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(console_handler)
    
    # Office Registration Logger
    office_logger = logging.getLogger('office_registration')
    office_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    office_logger.propagate = False
    
    # Error log handler (rotating file)
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    office_logger.addHandler(error_handler)
    
    # Info log handler (rotating file)
    info_handler = logging.handlers.RotatingFileHandler(
        info_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(detailed_formatter)
    office_logger.addHandler(info_handler)
    
    # Debug log handler (rotating file) - only in debug mode
    if settings.DEBUG:
        debug_handler = logging.handlers.RotatingFileHandler(
            debug_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(detailed_formatter)
        office_logger.addHandler(debug_handler)
    
    # Payment Logger
    payment_logger = logging.getLogger('payment')
    payment_logger.setLevel(logging.INFO)
    payment_logger.propagate = False
    
    payment_handler = logging.handlers.RotatingFileHandler(
        payment_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,  # Keep more payment logs
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
        backupCount=10,  # Keep more security logs
        encoding='utf-8'
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(detailed_formatter)
    security_logger.addHandler(security_handler)
    
    # Django loggers configuration
    django_logger = logging.getLogger('django')
    django_logger.setLevel(logging.INFO)
    
    # Database logger
    db_logger = logging.getLogger('django.db.backends')
    if settings.DEBUG:
        db_logger.setLevel(logging.DEBUG)
    else:
        db_logger.setLevel(logging.WARNING)
    
    # Request logger
    request_logger = logging.getLogger('django.request')
    request_logger.setLevel(logging.WARNING)
    
    return {
        'office_registration': office_logger,
        'payment': payment_logger,
        'security': security_logger,
    }


class DatabaseLogHandler(logging.Handler):
    """
    Custom log handler to store critical logs in database
    """
    
    def emit(self, record):
        """
        Emit a log record to database
        
        Args:
            record: LogRecord instance
        """
        try:
            # Import here to avoid circular imports
            from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
            from django.contrib.contenttypes.models import ContentType
            from django.contrib.auth import get_user_model
            
            # Only log ERROR and CRITICAL levels to database
            if record.levelno >= logging.ERROR:
                # Create log entry in database
                # This is a simplified version - you might want to create a custom model
                pass
                
        except Exception:
            # Don't let logging errors break the application
            pass


class PaymentLogFilter(logging.Filter):
    """
    Filter for payment-related logs
    """
    
    def filter(self, record):
        """
        Filter payment-related log records
        
        Args:
            record: LogRecord instance
        
        Returns:
            bool: True if record should be logged
        """
        payment_keywords = ['payment', 'transaction', 'gateway', 'subscription', 'fee']
        message = record.getMessage().lower()
        return any(keyword in message for keyword in payment_keywords)


class SecurityLogFilter(logging.Filter):
    """
    Filter for security-related logs
    """
    
    def filter(self, record):
        """
        Filter security-related log records
        
        Args:
            record: LogRecord instance
        
        Returns:
            bool: True if record should be logged
        """
        security_keywords = ['authentication', 'authorization', 'permission', 'login', 'logout', 'failed', 'denied']
        message = record.getMessage().lower()
        return any(keyword in message for keyword in security_keywords)


def log_user_action(user, action, model_name=None, object_id=None, details=None):
    """
    Log user actions for audit trail
    
    Args:
        user: User instance
        action: Action performed (CREATE, UPDATE, DELETE, VIEW)
        model_name: Name of the model affected
        object_id: ID of the object affected
        details: Additional details about the action
    """
    logger = logging.getLogger('office_registration')
    
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
    Log payment transaction details
    
    Args:
        transaction_data: Dictionary containing transaction details
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
    Log security events
    
    Args:
        event_type: Type of security event
        user: User instance if applicable
        ip_address: IP address of the request
        details: Additional details about the event
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
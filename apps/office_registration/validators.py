"""
Validators for ASOUD Office Registration System
Comprehensive validation functions for business data integrity
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_business_id(value):
    """
    Validate business ID according to requirements:
    - Minimum 5 characters
    - Maximum 20 characters
    - ASCII characters only (English letters and numbers)
    - No special characters except underscore and hyphen
    """
    if not value:
        raise ValidationError(_('Business ID is required'))
    
    if len(value) < 5:
        raise ValidationError(_('Business ID must be at least 5 characters long'))
    
    if len(value) > 20:
        raise ValidationError(_('Business ID cannot exceed 20 characters'))
    
    # Check for ASCII characters only (letters, numbers, underscore, hyphen)
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise ValidationError(_('Business ID can only contain English letters, numbers, underscore, and hyphen'))
    
    # Must start with a letter
    if not value[0].isalpha():
        raise ValidationError(_('Business ID must start with a letter'))
    
    return value


def validate_iranian_national_code(value):
    """
    Validate Iranian national code (کد ملی):
    - Must be exactly 10 digits
    - Must pass the Iranian national code checksum algorithm
    """
    if not value:
        return value  # Allow empty values for optional fields
    
    # Remove any non-digit characters
    value = re.sub(r'\D', '', str(value))
    
    if len(value) != 10:
        raise ValidationError(_('National code must be exactly 10 digits'))
    
    # Check for invalid patterns (all same digits)
    if len(set(value)) == 1:
        raise ValidationError(_('Invalid national code format'))
    
    # Iranian national code checksum validation
    check_digit = int(value[9])
    sum_digits = 0
    
    for i in range(9):
        sum_digits += int(value[i]) * (10 - i)
    
    remainder = sum_digits % 11
    
    if remainder < 2:
        expected_check = remainder
    else:
        expected_check = 11 - remainder
    
    if check_digit != expected_check:
        raise ValidationError(_('Invalid Iranian national code'))
    
    return value


def validate_iranian_mobile_number(value):
    """
    Validate Iranian mobile phone number:
    - Must start with 09
    - Must be exactly 11 digits
    - Valid Iranian mobile prefixes
    """
    if not value:
        return value
    
    # Remove any non-digit characters
    value = re.sub(r'\D', '', str(value))
    
    if len(value) != 11:
        raise ValidationError(_('Mobile number must be exactly 11 digits'))
    
    if not value.startswith('09'):
        raise ValidationError(_('Mobile number must start with 09'))
    
    # Valid Iranian mobile prefixes
    valid_prefixes = [
        '0901', '0902', '0903', '0905', '0930', '0933', '0934', '0935', 
        '0936', '0937', '0938', '0939', '0990', '0991', '0992', '0993', 
        '0994', '0995', '0996', '0997', '0998', '0999'
    ]
    
    prefix = value[:4]
    if prefix not in valid_prefixes:
        raise ValidationError(_('Invalid Iranian mobile number prefix'))
    
    return value


def validate_postal_code(value):
    """
    Validate Iranian postal code:
    - Must be exactly 10 digits
    - Cannot be all zeros or all same digits
    """
    if not value:
        return value
    
    # Remove any non-digit characters
    value = re.sub(r'\D', '', str(value))
    
    if len(value) != 10:
        raise ValidationError(_('Postal code must be exactly 10 digits'))
    
    # Check for invalid patterns
    if value == '0000000000' or len(set(value)) == 1:
        raise ValidationError(_('Invalid postal code format'))
    
    return value


def validate_working_hours(value):
    """
    Validate working hours JSON structure:
    Expected format: {
        "saturday": {"start": "08:00", "end": "17:00", "is_working": true},
        "sunday": {"start": "08:00", "end": "17:00", "is_working": true},
        ...
    }
    """
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError(_('Working hours must be a valid JSON object'))
    
    required_days = [
        'saturday', 'sunday', 'monday', 'tuesday', 
        'wednesday', 'thursday', 'friday'
    ]
    
    for day in required_days:
        if day not in value:
            raise ValidationError(_(f'Working hours must include {day}'))
        
        day_data = value[day]
        if not isinstance(day_data, dict):
            raise ValidationError(_(f'Working hours for {day} must be an object'))
        
        required_fields = ['start', 'end', 'is_working']
        for field in required_fields:
            if field not in day_data:
                raise ValidationError(_(f'Working hours for {day} must include {field}'))
        
        # Validate time format if working day
        if day_data.get('is_working', False):
            start_time = day_data.get('start')
            end_time = day_data.get('end')
            
            if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', start_time):
                raise ValidationError(_(f'Invalid start time format for {day}. Use HH:MM format'))
            
            if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', end_time):
                raise ValidationError(_(f'Invalid end time format for {day}. Use HH:MM format'))
    
    return value


def validate_instagram_id(value):
    """
    Validate Instagram ID:
    - Must be a valid Instagram username format
    - 1-30 characters
    - Only letters, numbers, periods, and underscores
    - Cannot start or end with period
    """
    if not value:
        return value
    
    if len(value) < 1 or len(value) > 30:
        raise ValidationError(_('Instagram ID must be between 1 and 30 characters'))
    
    if not re.match(r'^[a-zA-Z0-9._]+$', value):
        raise ValidationError(_('Instagram ID can only contain letters, numbers, periods, and underscores'))
    
    if value.startswith('.') or value.endswith('.'):
        raise ValidationError(_('Instagram ID cannot start or end with a period'))
    
    if '..' in value:
        raise ValidationError(_('Instagram ID cannot contain consecutive periods'))
    
    return value


def validate_telegram_id(value):
    """
    Validate Telegram ID:
    - Must be a valid Telegram username format
    - 5-32 characters
    - Only letters, numbers, and underscores
    - Must start with a letter
    """
    if not value:
        return value
    
    if len(value) < 5 or len(value) > 32:
        raise ValidationError(_('Telegram ID must be between 5 and 32 characters'))
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
        raise ValidationError(_('Telegram ID must start with a letter and contain only letters, numbers, and underscores'))
    
    return value


def validate_market_fee(value):
    """
    Validate market fee amount:
    - Must be non-negative
    - Maximum value validation
    - Decimal precision validation
    """
    if value is None:
        raise ValidationError(_('Market fee is required'))
    
    if value < 0:
        raise ValidationError(_('Market fee cannot be negative'))
    
    if value > 999999999999:
        raise ValidationError(_('Market fee cannot exceed 999 billion'))
    
    # Check decimal places (maximum 3)
    decimal_str = str(value)
    if '.' in decimal_str:
        decimal_places = len(decimal_str.split('.')[1])
        if decimal_places > 3:
            raise ValidationError(_('Market fee cannot have more than 3 decimal places'))
    
    return value
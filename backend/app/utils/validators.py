"""
=============================================================================
BESIKTNINGSAPP BACKEND - VALIDATORS
=============================================================================
Custom validation functions.
"""

import re
from typing import Optional
from uuid import UUID


def validate_uuid(value: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        value: String to validate
        
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def validate_revision(revision: int, min_value: int = 1) -> bool:
    """
    Validate revision number.
    
    Args:
        revision: Revision number to validate
        min_value: Minimum allowed value
        
    Returns:
        True if valid, False otherwise
    """
    return isinstance(revision, int) and revision >= min_value


def validate_email_format(email: str) -> bool:
    """
    Validate email format (basic check).
    
    Args:
        email: Email address
        
    Returns:
        True if valid format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone_number(phone: Optional[str]) -> bool:
    """
    Validate Swedish phone number format.
    
    Args:
        phone: Phone number (optional)
        
    Returns:
        True if valid or None, False otherwise
    """
    if not phone:
        return True
    
    # Remove common separators
    cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Swedish mobile: +46 or 07
    # Swedish landline: +46 8, 08, etc.
    pattern = r'^(\+46|0)[0-9]{7,12}$'
    return bool(re.match(pattern, cleaned))


def validate_apartment_number_format(number: str) -> bool:
    """
    Validate apartment number format.
    
    Allowed: digits, letters before/after digits
    Examples: 1201, A12, 12B, A1201
    
    Args:
        number: Apartment number
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[A-Za-z]?\d{1,5}[A-Za-z]?$'
    return bool(re.match(pattern, number))


def validate_storage_key(key: str) -> bool:
    """
    Validate storage key format.
    
    Args:
        key: Storage key
        
    Returns:
        True if valid, False otherwise
    """
    # No whitespace, no path traversal
    if not key or ' ' in key or '..' in key:
        return False
    
    # Should contain at least one /
    if '/' not in key:
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    from werkzeug.utils import secure_filename
    return secure_filename(filename)

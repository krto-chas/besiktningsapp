"""
=============================================================================
BESIKTNINGSAPP BACKEND - HELPERS
=============================================================================
Miscellaneous helper functions.
"""

from datetime import datetime, timezone
from typing import Optional
import hashlib


def utc_now() -> datetime:
    """
    Get current UTC datetime.
    
    Returns:
        UTC datetime with timezone
    """
    return datetime.now(timezone.utc)


def to_iso_string(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to ISO 8601 string.
    
    Args:
        dt: Datetime object
        
    Returns:
        ISO format string or None
    """
    if not dt:
        return None
    
    return dt.isoformat() + 'Z' if dt.tzinfo else dt.isoformat()


def calculate_file_checksum(file_path: str) -> str:
    """
    Calculate SHA256 checksum of file.
    
    Args:
        file_path: Path to file
        
    Returns:
        SHA256 checksum as hex string
    """
    sha256 = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    
    return f"sha256:{sha256.hexdigest()}"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to max length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_boolean(value: any) -> bool:
    """
    Parse boolean from various input types.
    
    Args:
        value: Value to parse (string, int, bool)
        
    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    
    if isinstance(value, int):
        return value != 0
    
    return False

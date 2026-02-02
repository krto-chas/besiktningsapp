"""
=============================================================================
BESIKTNINGSAPP BACKEND - RESPONSES
=============================================================================
Standardized API response helpers.
"""

from typing import Any, Optional, List
from flask import jsonify


def success_response(data: Any, meta: Optional[dict] = None, status_code: int = 200):
    """
    Create success response.
    
    Args:
        data: Response data
        meta: Optional metadata
        status_code: HTTP status code
        
    Returns:
        JSON response tuple
    """
    response = {"data": data}
    
    if meta:
        response["meta"] = meta
    
    return jsonify(response), status_code


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    field_errors: Optional[List[dict]] = None
):
    """
    Create error response.
    
    Args:
        code: Error code
        message: Error message
        status_code: HTTP status code
        field_errors: Optional field-level errors
        
    Returns:
        JSON response tuple
    """
    error_dict = {
        "code": code,
        "message": message
    }
    
    if field_errors:
        error_dict["field_errors"] = field_errors
    
    return jsonify({"error": error_dict}), status_code


def paginated_response(
    items: List[Any],
    total: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    status_code: int = 200
):
    """
    Create paginated response.
    
    Args:
        items: List of items
        total: Total count (optional)
        limit: Items per page
        offset: Current offset
        status_code: HTTP status code
        
    Returns:
        JSON response tuple
    """
    meta = {
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total if total else False
    }
    
    if total is not None:
        meta["total"] = total
    
    return success_response(items, meta=meta, status_code=status_code)


def created_response(data: Any, location: Optional[str] = None):
    """
    Create 201 Created response.
    
    Args:
        data: Created resource data
        location: Optional Location header value
        
    Returns:
        JSON response tuple with Location header
    """
    response = jsonify({"data": data})
    response.status_code = 201
    
    if location:
        response.headers['Location'] = location
    
    return response


def no_content_response():
    """
    Create 204 No Content response.
    
    Returns:
        Empty response tuple
    """
    return '', 204

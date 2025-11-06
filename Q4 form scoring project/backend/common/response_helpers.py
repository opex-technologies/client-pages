"""
HTTP response helper functions for Cloud Functions
Provides standardized response formatting
Created: November 5, 2025
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime


def _json_serializer(obj):
    """JSON serializer for objects not serializable by default"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def _create_response(
    status_code: int,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None
) -> tuple:
    """
    Create standardized HTTP response tuple for Cloud Functions

    Args:
        status_code: HTTP status code
        body: Response body dictionary
        headers: Optional additional headers

    Returns:
        tuple: (response_body, status_code, headers) for Cloud Functions
    """
    # Default headers
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',  # CORS - adjust for production
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }

    # Merge with custom headers
    if headers:
        default_headers.update(headers)

    # Add timestamp if not present
    if 'timestamp' not in body:
        body['timestamp'] = datetime.utcnow().isoformat() + 'Z'

    # Serialize to JSON
    response_json = json.dumps(body, default=_json_serializer, indent=2)

    return response_json, status_code, default_headers


def success_response(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> tuple:
    """
    Create success response (2xx)

    Args:
        data: Response data (can be dict, list, or primitive)
        message: Optional success message
        status_code: HTTP status code (default: 200)
        headers: Optional additional headers

    Returns:
        tuple: Cloud Functions response tuple

    Usage:
        return success_response(
            data={'user_id': '123', 'email': 'user@example.com'},
            message='User created successfully',
            status_code=201
        )
    """
    body = {
        'success': True,
        'data': data
    }

    if message:
        body['message'] = message

    return _create_response(status_code, body, headers)


def error_response(
    message: str,
    status_code: int = 500,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> tuple:
    """
    Create error response (4xx or 5xx)

    Args:
        message: Error message
        status_code: HTTP status code (default: 500)
        error_code: Optional error code for client handling
        details: Optional additional error details
        headers: Optional additional headers

    Returns:
        tuple: Cloud Functions response tuple

    Usage:
        return error_response(
            message='User not found',
            status_code=404,
            error_code='USER_NOT_FOUND'
        )
    """
    body = {
        'success': False,
        'error': {
            'message': message,
            'code': error_code or f"ERROR_{status_code}"
        }
    }

    if details:
        body['error']['details'] = details

    return _create_response(status_code, body, headers)


def bad_request_response(
    message: str = "Bad request",
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> tuple:
    """
    Create 400 Bad Request response

    Args:
        message: Error message
        error_code: Optional error code
        details: Optional error details

    Returns:
        tuple: Cloud Functions response tuple

    Usage:
        return bad_request_response(
            message='Invalid email format',
            error_code='INVALID_EMAIL'
        )
    """
    return error_response(
        message=message,
        status_code=400,
        error_code=error_code or 'BAD_REQUEST',
        details=details
    )


def unauthorized_response(
    message: str = "Unauthorized",
    error_code: Optional[str] = None
) -> tuple:
    """
    Create 401 Unauthorized response

    Args:
        message: Error message
        error_code: Optional error code

    Returns:
        tuple: Cloud Functions response tuple

    Usage:
        return unauthorized_response(
            message='Invalid or expired token',
            error_code='INVALID_TOKEN'
        )
    """
    return error_response(
        message=message,
        status_code=401,
        error_code=error_code or 'UNAUTHORIZED'
    )


def forbidden_response(
    message: str = "Forbidden",
    error_code: Optional[str] = None
) -> tuple:
    """
    Create 403 Forbidden response

    Args:
        message: Error message
        error_code: Optional error code

    Returns:
        tuple: Cloud Functions response tuple

    Usage:
        return forbidden_response(
            message='Insufficient permissions',
            error_code='INSUFFICIENT_PERMISSIONS'
        )
    """
    return error_response(
        message=message,
        status_code=403,
        error_code=error_code or 'FORBIDDEN'
    )


def not_found_response(
    message: str = "Not found",
    error_code: Optional[str] = None,
    resource: Optional[str] = None
) -> tuple:
    """
    Create 404 Not Found response

    Args:
        message: Error message
        error_code: Optional error code
        resource: Optional resource identifier

    Returns:
        tuple: Cloud Functions response tuple

    Usage:
        return not_found_response(
            message='User not found',
            error_code='USER_NOT_FOUND',
            resource='user_id:123'
        )
    """
    details = {'resource': resource} if resource else None

    return error_response(
        message=message,
        status_code=404,
        error_code=error_code or 'NOT_FOUND',
        details=details
    )


def conflict_response(
    message: str = "Conflict",
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> tuple:
    """
    Create 409 Conflict response

    Args:
        message: Error message
        error_code: Optional error code
        details: Optional error details

    Returns:
        tuple: Cloud Functions response tuple

    Usage:
        return conflict_response(
            message='Email already exists',
            error_code='EMAIL_EXISTS',
            details={'email': 'user@example.com'}
        )
    """
    return error_response(
        message=message,
        status_code=409,
        error_code=error_code or 'CONFLICT',
        details=details
    )


def validation_error_response(
    errors: List[str],
    message: str = "Validation failed"
) -> tuple:
    """
    Create validation error response

    Args:
        errors: List of validation error messages
        message: General error message

    Returns:
        tuple: Cloud Functions response tuple

    Usage:
        return validation_error_response(
            errors=[
                'Email is required',
                'Password must be at least 8 characters'
            ],
            message='Invalid registration data'
        )
    """
    return error_response(
        message=message,
        status_code=400,
        error_code='VALIDATION_ERROR',
        details={'errors': errors}
    )


def paginated_response(
    data: List[Any],
    page: int,
    page_size: int,
    total_count: int,
    message: Optional[str] = None
) -> tuple:
    """
    Create paginated response

    Args:
        data: List of items for current page
        page: Current page number
        page_size: Items per page
        total_count: Total number of items across all pages
        message: Optional message

    Returns:
        tuple: Cloud Functions response tuple

    Usage:
        return paginated_response(
            data=users,
            page=1,
            page_size=50,
            total_count=150,
            message='Users retrieved successfully'
        )
    """
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division

    response_data = {
        'items': data,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }

    return success_response(
        data=response_data,
        message=message
    )


def cors_preflight_response() -> tuple:
    """
    Create CORS preflight (OPTIONS) response

    Returns:
        tuple: Cloud Functions response tuple

    Usage:
        if request.method == 'OPTIONS':
            return cors_preflight_response()
    """
    return _create_response(
        status_code=204,
        body={},
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
    )

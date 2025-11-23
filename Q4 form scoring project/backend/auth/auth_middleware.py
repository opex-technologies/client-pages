"""
Authentication and Authorization Middleware
Decorators and utilities for protecting API endpoints
Created: November 5, 2025

Usage:
    from auth_middleware import require_auth, require_permission

    @require_auth
    def my_endpoint(request, current_user):
        # current_user is automatically injected
        return success_response(data={'user_id': current_user['user_id']})

    @require_permission('edit', company='Acme', category='SASE')
    def protected_endpoint(request, current_user):
        # Only users with 'edit' permission for Acme/SASE can access
        return success_response(data={'message': 'Access granted'})
"""

from functools import wraps
from typing import Dict, Any, Optional, Callable
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from common.config import config
    from common.logger import get_logger
    from common.response_helpers import unauthorized_response, forbidden_response
except ImportError:
    from config_standalone import config
    from logger_standalone import get_logger
    from response_helpers_standalone import unauthorized_response, forbidden_response

from jwt_utils import verify_token
from permissions_firestore import check_permission

logger = get_logger('auth.middleware')


def extract_user_from_request(request) -> tuple:
    """
    Extract and verify user from Authorization header

    Args:
        request: HTTP request object

    Returns:
        tuple: (success: bool, user_data: Optional[Dict], error_response: Optional[tuple])

    Usage:
        success, user, error = extract_user_from_request(request)
        if not success:
            return error  # Return error response
        # Use user data
    """
    try:
        # Check for Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return False, None, unauthorized_response('Missing or invalid Authorization header')

        # Extract and verify token
        access_token = auth_header[7:]  # Remove 'Bearer ' prefix
        is_valid, payload, error = verify_token(access_token, token_type='access')

        if not is_valid:
            return False, None, unauthorized_response(error or 'Invalid access token')

        # Extract user info from token
        user_data = {
            'user_id': payload.get('user_id'),
            'email': payload.get('email'),
            'token_payload': payload
        }

        return True, user_data, None

    except Exception as e:
        logger.exception('Error extracting user from request', error=str(e))
        return False, None, unauthorized_response('Authentication failed')


def require_auth(handler: Callable) -> Callable:
    """
    Decorator to require authentication for an endpoint

    The decorated function will receive an additional 'current_user' parameter
    containing user_id, email, and the full token payload.

    Usage:
        @require_auth
        def my_endpoint(request, current_user):
            user_id = current_user['user_id']
            return success_response(data={'user_id': user_id})

    Args:
        handler: Function to decorate (must accept request and current_user params)

    Returns:
        Callable: Decorated function
    """
    @wraps(handler)
    def wrapper(request):
        # Extract user from request
        success, user, error = extract_user_from_request(request)

        if not success:
            return error

        # Call handler with user data
        return handler(request, current_user=user)

    return wrapper


def require_permission(
    required_level: str,
    company: Optional[str] = None,
    category: Optional[str] = None,
    extract_company_from_request: bool = False,
    extract_category_from_request: bool = False,
    company_param: str = 'company',
    category_param: str = 'category'
) -> Callable:
    """
    Decorator to require specific permission level for an endpoint

    The decorated function will receive an additional 'current_user' parameter.

    Usage:
        # Fixed scope
        @require_permission('edit', company='Acme Corp', category='SASE')
        def edit_sase_endpoint(request, current_user):
            return success_response(data={'message': 'Can edit SASE'})

        # Dynamic scope from request
        @require_permission('edit', extract_company_from_request=True, extract_category_from_request=True)
        def edit_dynamic_endpoint(request, current_user):
            # Permission checked against company/category from request params
            return success_response(data={'message': 'Access granted'})

    Args:
        required_level: Minimum permission level ('view', 'edit', 'admin')
        company: Fixed company scope (optional)
        category: Fixed category scope (optional)
        extract_company_from_request: Get company from request params
        extract_category_from_request: Get category from request params
        company_param: Request parameter name for company (default: 'company')
        category_param: Request parameter name for category (default: 'category')

    Returns:
        Callable: Decorator function
    """
    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        def wrapper(request):
            # Extract user from request
            success, user, error = extract_user_from_request(request)

            if not success:
                return error

            user_id = user['user_id']

            # Determine scope
            check_company = company
            check_category = category

            if extract_company_from_request:
                # Try query params first, then JSON body
                check_company = request.args.get(company_param)
                if not check_company and request.method in ['POST', 'PUT', 'PATCH']:
                    data = request.get_json(silent=True)
                    if data:
                        check_company = data.get(company_param)

            if extract_category_from_request:
                # Try query params first, then JSON body
                check_category = request.args.get(category_param)
                if not check_category and request.method in ['POST', 'PUT', 'PATCH']:
                    data = request.get_json(silent=True)
                    if data:
                        check_category = data.get(category_param)

            # Check permission
            has_permission = check_permission(
                user_id=user_id,
                required_level=required_level,
                company=check_company,
                category=check_category
            )

            if not has_permission:
                logger.warning(
                    'Permission denied',
                    user_id=user_id,
                    required_level=required_level,
                    company=check_company,
                    category=check_category
                )
                return forbidden_response(
                    f"Insufficient permissions: requires '{required_level}' level" +
                    (f" for {check_company}" if check_company else "") +
                    (f"/{check_category}" if check_category else "")
                )

            # Call handler with user data
            return handler(request, current_user=user)

        return wrapper
    return decorator


def require_super_admin(handler: Callable) -> Callable:
    """
    Decorator to require super admin permission

    Super admin = admin permission with NULL company and category
    (access to everything in the system)

    Usage:
        @require_super_admin
        def admin_only_endpoint(request, current_user):
            return success_response(data={'message': 'Super admin access'})

    Args:
        handler: Function to decorate

    Returns:
        Callable: Decorated function
    """
    return require_permission('admin', company=None, category=None)(handler)


def optional_auth(handler: Callable) -> Callable:
    """
    Decorator for optional authentication

    Attempts to extract user from request, but continues even if auth fails.
    The handler receives current_user=None if not authenticated.

    Usage:
        @optional_auth
        def public_endpoint_with_optional_user_context(request, current_user):
            if current_user:
                # Customize response for authenticated user
                user_id = current_user['user_id']
            else:
                # Public access
                pass
            return success_response(data={'message': 'Hello'})

    Args:
        handler: Function to decorate

    Returns:
        Callable: Decorated function
    """
    @wraps(handler)
    def wrapper(request):
        # Try to extract user, but don't fail if not present
        success, user, _ = extract_user_from_request(request)

        # Call handler with user data (None if not authenticated)
        return handler(request, current_user=user if success else None)

    return wrapper


# Example usage in Cloud Function
def example_protected_endpoint(request):
    """
    Example of how to use middleware in a Cloud Function

    This shows the different patterns for protecting endpoints.
    """
    from common.response_helpers import success_response

    # Pattern 1: Manual auth check
    success, user, error = extract_user_from_request(request)
    if not success:
        return error

    # Pattern 2: Check specific permission manually
    if not check_permission(user['user_id'], 'edit', company='Acme Corp'):
        return forbidden_response('Insufficient permissions')

    return success_response(data={'message': 'Access granted'})


# Helper function for integrating with existing handlers
def with_auth_check(handler: Callable, required_level: Optional[str] = None,
                   company: Optional[str] = None, category: Optional[str] = None):
    """
    Wrapper function to add auth checks to existing handlers

    This is useful when you can't use decorators (e.g., in routing logic)

    Usage:
        def my_handler(request, current_user):
            return success_response(data={'user_id': current_user['user_id']})

        # In main routing function:
        if path == '/protected':
            return with_auth_check(my_handler, required_level='edit')(request)

    Args:
        handler: Handler function
        required_level: Optional permission level to require
        company: Optional company scope
        category: Optional category scope

    Returns:
        Callable: Wrapped handler
    """
    if required_level:
        return require_permission(required_level, company, category)(handler)
    else:
        return require_auth(handler)

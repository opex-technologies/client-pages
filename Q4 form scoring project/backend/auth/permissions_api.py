"""
Permissions Management API
Cloud Function endpoints for managing RBAC permissions
Created: November 5, 2025

Endpoints:
    POST /permissions/grant - Grant permission to user (admin only)
    POST /permissions/revoke - Revoke permission (admin only)
    GET /permissions/user/:user_id - Get user's permissions
    GET /permissions/list - List all permissions (admin only)
    POST /permissions/check - Check if user has permission
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))))

try:
    from common.config import config
    from common.logger import get_logger, log_api_request, log_api_response
    from common.validators import validate_required_fields, validate_uuid, sanitize_input
    from common.response_helpers import (
        success_response,
        error_response,
        bad_request_response,
        unauthorized_response,
        forbidden_response
    )
except ImportError:
    from config_standalone import config
    from logger_standalone import get_logger, log_api_request, log_api_response
    from validators_standalone import validate_required_fields, validate_uuid, sanitize_input
    from response_helpers_standalone import (
        success_response,
        error_response,
        bad_request_response,
        unauthorized_response,
        forbidden_response
    )

from jwt_utils import verify_token
from permissions_utils import (
    grant_permission,
    revoke_permission,
    check_permission,
    get_user_permissions,
    get_highest_permission_level,
    is_super_admin,
    list_all_permissions
)

logger = get_logger('auth.permissions_api')


def permissions_handler(request):
    """
    Main handler for permissions API

    Routes:
        POST /permissions/grant
        POST /permissions/revoke
        GET /permissions/user/:user_id
        GET /permissions/list
        POST /permissions/check
    """
    path = request.path
    method = request.method

    log_api_request(logger, method, path)

    try:
        # All permission endpoints require authentication
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return unauthorized_response('Missing or invalid Authorization header')

        access_token = auth_header[7:]
        is_valid, payload, error = verify_token(access_token, token_type='access')

        if not is_valid:
            return unauthorized_response(error or 'Invalid access token')

        current_user_id = payload.get('user_id')

        # Route to appropriate handler
        if path == '/permissions/grant' and method == 'POST':
            response = handle_grant_permission(request, current_user_id)

        elif path == '/permissions/revoke' and method == 'POST':
            response = handle_revoke_permission(request, current_user_id)

        elif path.startswith('/permissions/user/') and method == 'GET':
            user_id = path.split('/permissions/user/')[-1]
            response = handle_get_user_permissions(request, current_user_id, user_id)

        elif path == '/permissions/list' and method == 'GET':
            response = handle_list_permissions(request, current_user_id)

        elif path == '/permissions/check' and method == 'POST':
            response = handle_check_permission(request, current_user_id)

        else:
            response = error_response(
                message=f"Endpoint not found: {method} {path}",
                status_code=404,
                error_code='ENDPOINT_NOT_FOUND'
            )

        _, status_code, _ = response
        log_api_response(logger, method, path, status_code)

        return response

    except Exception as e:
        logger.exception('Unhandled error in permissions handler', error=str(e))
        return error_response(
            message='Internal server error',
            status_code=500,
            error_code='INTERNAL_ERROR'
        )


def handle_grant_permission(request, current_user_id: str) -> tuple:
    """
    Grant permission to a user (admin only)

    POST /permissions/grant
    Body:
        {
            "user_id": "user-123",
            "permission_level": "edit",
            "company": "Acme Corp",  // optional
            "category": "SASE",  // optional
            "expires_days": 365,  // optional
            "notes": "Granted for Q4 project"  // optional
        }

    Returns:
        {
            "success": true,
            "data": {
                "permission_id": "perm-123",
                "user_id": "user-123",
                "permission_level": "edit",
                "company": "Acme Corp",
                "category": "SASE",
                "granted_by": "admin-456",
                "granted_at": "2025-11-05T...",
                "expires_at": "2026-11-05T..."
            },
            "message": "Permission granted successfully"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('Request body is required')

        # Validate required fields
        is_valid, error = validate_required_fields(data, ['user_id', 'permission_level'])
        if not is_valid:
            return bad_request_response(error)

        # Extract fields
        user_id = sanitize_input(data['user_id'], max_length=100)
        permission_level = sanitize_input(data['permission_level'], max_length=20).lower()
        company = sanitize_input(data.get('company', ''), max_length=200) or None
        category = sanitize_input(data.get('category', ''), max_length=100) or None
        expires_days = data.get('expires_days')
        notes = sanitize_input(data.get('notes', ''), max_length=500) or None

        # Calculate expiration
        expires_at = None
        if expires_days:
            try:
                expires_at = datetime.utcnow() + timedelta(days=int(expires_days))
            except (ValueError, TypeError):
                return bad_request_response('expires_days must be a valid number')

        # Grant permission
        success, permission_id, error = grant_permission(
            user_id=user_id,
            permission_level=permission_level,
            granted_by=current_user_id,
            company=company,
            category=category,
            expires_at=expires_at,
            notes=notes
        )

        if not success:
            return forbidden_response(error or 'Failed to grant permission')

        return success_response(
            data={
                'permission_id': permission_id,
                'user_id': user_id,
                'permission_level': permission_level,
                'company': company,
                'category': category,
                'granted_by': current_user_id,
                'granted_at': datetime.utcnow().isoformat(),
                'expires_at': expires_at.isoformat() if expires_at else None
            },
            message='Permission granted successfully',
            status_code=201
        )

    except Exception as e:
        logger.exception('Error granting permission', error=str(e))
        return error_response(
            message='Failed to grant permission',
            status_code=500,
            error_code='GRANT_PERMISSION_ERROR'
        )


def handle_revoke_permission(request, current_user_id: str) -> tuple:
    """
    Revoke a permission (admin only)

    POST /permissions/revoke
    Body:
        {
            "permission_id": "perm-123",
            "notes": "User left company"  // optional
        }

    Returns:
        {
            "success": true,
            "message": "Permission revoked successfully"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('Request body is required')

        # Validate required fields
        is_valid, error = validate_required_fields(data, ['permission_id'])
        if not is_valid:
            return bad_request_response(error)

        permission_id = sanitize_input(data['permission_id'], max_length=100)
        notes = sanitize_input(data.get('notes', ''), max_length=500) or None

        # Check if current user has admin permission
        # (grant_permission function will verify scope-specific admin rights)

        # Revoke permission
        success, error = revoke_permission(
            permission_id=permission_id,
            revoked_by=current_user_id,
            notes=notes
        )

        if not success:
            if "not found" in (error or "").lower():
                return bad_request_response(error)
            return forbidden_response(error or 'Failed to revoke permission')

        return success_response(
            data=None,
            message='Permission revoked successfully'
        )

    except Exception as e:
        logger.exception('Error revoking permission', error=str(e))
        return error_response(
            message='Failed to revoke permission',
            status_code=500,
            error_code='REVOKE_PERMISSION_ERROR'
        )


def handle_get_user_permissions(request, current_user_id: str, target_user_id: str) -> tuple:
    """
    Get permissions for a user

    GET /permissions/user/:user_id

    Returns:
        {
            "success": true,
            "data": {
                "user_id": "user-123",
                "highest_level": "edit",
                "is_super_admin": false,
                "permissions": [
                    {
                        "permission_id": "perm-123",
                        "company": "Acme Corp",
                        "category": "SASE",
                        "permission_level": "edit",
                        "granted_by": "admin-456",
                        "granted_at": "2025-11-05T...",
                        "expires_at": null,
                        "is_active": true
                    }
                ]
            }
        }
    """
    try:
        # Users can view their own permissions
        # Admins can view anyone's permissions
        if current_user_id != target_user_id and not is_super_admin(current_user_id):
            return forbidden_response('You can only view your own permissions')

        # Get permissions
        permissions = get_user_permissions(target_user_id)
        highest_level = get_highest_permission_level(target_user_id)
        is_admin = is_super_admin(target_user_id)

        return success_response(
            data={
                'user_id': target_user_id,
                'highest_level': highest_level,
                'is_super_admin': is_admin,
                'permissions': permissions
            }
        )

    except Exception as e:
        logger.exception('Error getting user permissions', error=str(e))
        return error_response(
            message='Failed to get user permissions',
            status_code=500,
            error_code='GET_PERMISSIONS_ERROR'
        )


def handle_list_permissions(request, current_user_id: str) -> tuple:
    """
    List all permissions (admin only)

    GET /permissions/list?company=Acme&category=SASE&level=admin&active_only=true

    Returns:
        {
            "success": true,
            "data": {
                "permissions": [
                    {
                        "permission_id": "perm-123",
                        "user_id": "user-123",
                        "email": "user@example.com",
                        "full_name": "John Doe",
                        "company": "Acme Corp",
                        "category": "SASE",
                        "permission_level": "edit",
                        "granted_by": "admin-456",
                        "granted_at": "2025-11-05T...",
                        "expires_at": null,
                        "is_active": true
                    }
                ],
                "count": 15
            }
        }
    """
    try:
        # Only super admins can list all permissions
        if not is_super_admin(current_user_id):
            return forbidden_response('Only super admins can list all permissions')

        # Get query parameters
        company = request.args.get('company')
        category = request.args.get('category')
        level = request.args.get('level')
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        # List permissions
        permissions = list_all_permissions(
            company=company,
            category=category,
            permission_level=level,
            active_only=active_only
        )

        return success_response(
            data={
                'permissions': permissions,
                'count': len(permissions)
            }
        )

    except Exception as e:
        logger.exception('Error listing permissions', error=str(e))
        return error_response(
            message='Failed to list permissions',
            status_code=500,
            error_code='LIST_PERMISSIONS_ERROR'
        )


def handle_check_permission(request, current_user_id: str) -> tuple:
    """
    Check if user has a specific permission

    POST /permissions/check
    Body:
        {
            "user_id": "user-123",  // optional, defaults to current user
            "required_level": "edit",
            "company": "Acme Corp",  // optional
            "category": "SASE"  // optional
        }

    Returns:
        {
            "success": true,
            "data": {
                "has_permission": true,
                "user_id": "user-123",
                "required_level": "edit",
                "company": "Acme Corp",
                "category": "SASE"
            }
        }
    """
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('Request body is required')

        # Validate required fields
        is_valid, error = validate_required_fields(data, ['required_level'])
        if not is_valid:
            return bad_request_response(error)

        user_id = sanitize_input(data.get('user_id', current_user_id), max_length=100)
        required_level = sanitize_input(data['required_level'], max_length=20).lower()
        company = sanitize_input(data.get('company', ''), max_length=200) or None
        category = sanitize_input(data.get('category', ''), max_length=100) or None

        # Check permission
        has_permission = check_permission(user_id, required_level, company, category)

        return success_response(
            data={
                'has_permission': has_permission,
                'user_id': user_id,
                'required_level': required_level,
                'company': company,
                'category': category
            }
        )

    except Exception as e:
        logger.exception('Error checking permission', error=str(e))
        return error_response(
            message='Failed to check permission',
            status_code=500,
            error_code='CHECK_PERMISSION_ERROR'
        )

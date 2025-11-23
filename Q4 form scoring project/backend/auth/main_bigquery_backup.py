"""
Authentication API - Cloud Function Entry Point
Handles user registration, login, logout, and token refresh
Created: November 5, 2025

Endpoints:
    POST /auth/register - Register new user
    POST /auth/login - Login and get tokens
    POST /auth/refresh - Refresh access token
    POST /auth/logout - Logout (revoke session)
    POST /auth/verify - Verify token validity
    GET  /auth/me - Get current user info
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from common.config import config
    from common.logger import get_logger, log_api_request, log_api_response, log_authentication_event
    from common.validators import (
        validate_email,
        validate_password,
        validate_required_fields,
        sanitize_input
    )
    from common.response_helpers import (
        success_response,
        error_response,
        bad_request_response,
        unauthorized_response,
        conflict_response,
        cors_preflight_response
    )
    from common.bigquery_client import get_bigquery_client, execute_query, insert_rows
except ImportError:
    # Fallback for Cloud Functions deployment
    from config_standalone import config
    from logger_standalone import get_logger, log_api_request, log_api_response, log_authentication_event
    from validators_standalone import (
        validate_email,
        validate_password,
        validate_required_fields,
        sanitize_input
    )
    from response_helpers_standalone import (
        success_response,
        error_response,
        bad_request_response,
        unauthorized_response,
        conflict_response,
        cors_preflight_response
    )
    from bigquery_client_standalone import get_bigquery_client, execute_query, insert_rows

from password_utils import hash_password, verify_password
from jwt_utils import (
    generate_access_token,
    generate_refresh_token,
    verify_token,
    revoke_token,
    revoke_all_user_sessions
)

logger = get_logger('auth.api')


def auth_handler(request):
    """
    Main Cloud Function handler for authentication API

    Routes requests to appropriate handlers based on path and method
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return cors_preflight_response()

    # Log request
    path = request.path
    method = request.method
    log_api_request(logger, method, path)

    try:
        # Route to appropriate handler
        if path == '/auth/register' and method == 'POST':
            response = handle_register(request)

        elif path == '/auth/login' and method == 'POST':
            response = handle_login(request)

        elif path == '/auth/refresh' and method == 'POST':
            response = handle_refresh(request)

        elif path == '/auth/logout' and method == 'POST':
            response = handle_logout(request)

        elif path == '/auth/verify' and method == 'POST':
            response = handle_verify(request)

        elif path == '/auth/me' and method == 'GET':
            response = handle_get_user(request)

        else:
            response = error_response(
                message=f"Endpoint not found: {method} {path}",
                status_code=404,
                error_code='ENDPOINT_NOT_FOUND'
            )

        # Log response
        _, status_code, _ = response
        log_api_response(logger, method, path, status_code)

        return response

    except Exception as e:
        logger.exception('Unhandled error in auth handler', error=str(e))
        return error_response(
            message='Internal server error',
            status_code=500,
            error_code='INTERNAL_ERROR'
        )


def handle_register(request) -> tuple:
    """
    Handle user registration

    POST /auth/register
    Body:
        {
            "email": "user@example.com",
            "password": "MyP@ssw0rd123",
            "full_name": "John Doe"
        }

    Returns:
        {
            "success": true,
            "data": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "created_at": "2025-11-05T12:00:00Z"
            },
            "message": "User registered successfully"
        }
    """
    try:
        # Parse request body
        data = request.get_json()
        if not data:
            return bad_request_response('Request body is required')

        # Validate required fields
        is_valid, error = validate_required_fields(data, ['email', 'password', 'full_name'])
        if not is_valid:
            return bad_request_response(error)

        # Extract and sanitize inputs
        email = sanitize_input(data['email'].lower().strip(), max_length=255)
        password = data['password']  # Don't sanitize passwords
        full_name = sanitize_input(data['full_name'], max_length=100)

        # Validate email format
        is_valid, error = validate_email(email)
        if not is_valid:
            return bad_request_response(error)

        # Validate password strength
        is_valid, error = validate_password(password)
        if not is_valid:
            return bad_request_response(error)

        # Check if email already exists
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'users')
        check_query = f"""
        SELECT user_id
        FROM `{table_ref}`
        WHERE email = @email
        LIMIT 1
        """

        from google.cloud import bigquery
        existing_users = execute_query(
            check_query,
            params=[bigquery.ScalarQueryParameter("email", "STRING", email)]
        )

        if existing_users:
            log_authentication_event(logger, 'registration_failed_duplicate', email=email)
            return conflict_response(
                message='Email already registered',
                error_code='EMAIL_EXISTS'
            )

        # Hash password
        password_hash = hash_password(password)

        # Create user record
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()

        user_data = {
            'user_id': user_id,
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'mfa_secret': None,
            'failed_login_attempts': 0,
            'account_locked_until': None,
            'created_at': now.isoformat(),
            'last_login': None,
            'password_changed_at': now.isoformat(),
            'status': 'active',
            'created_by': user_id,  # Self-created
            'updated_at': None,
            'updated_by': None
        }

        # Insert user into database
        insert_rows(table_ref, [user_data])

        # Log successful registration
        log_authentication_event(logger, 'user_registered', user_id=user_id, email=email)

        # Return user data (without password hash)
        return success_response(
            data={
                'user_id': user_id,
                'email': email,
                'full_name': full_name,
                'created_at': user_data['created_at']
            },
            message='User registered successfully',
            status_code=201
        )

    except Exception as e:
        logger.exception('Registration error', error=str(e))
        return error_response(
            message='Registration failed',
            status_code=500,
            error_code='REGISTRATION_ERROR'
        )


def handle_login(request) -> tuple:
    """
    Handle user login

    POST /auth/login
    Body:
        {
            "email": "user@example.com",
            "password": "MyP@ssw0rd123"
        }

    Returns:
        {
            "success": true,
            "data": {
                "access_token": "eyJhbGc...",
                "refresh_token": "eyJhbGc...",
                "token_type": "Bearer",
                "expires_in": 86400,
                "user": {
                    "user_id": "123...",
                    "email": "user@example.com",
                    "full_name": "John Doe"
                }
            },
            "message": "Login successful"
        }
    """
    try:
        # Parse request body
        data = request.get_json()
        if not data:
            return bad_request_response('Request body is required')

        # Validate required fields
        is_valid, error = validate_required_fields(data, ['email', 'password'])
        if not is_valid:
            return bad_request_response(error)

        email = sanitize_input(data['email'].lower().strip(), max_length=255)
        password = data['password']

        # Get user from database
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'users')
        query = f"""
        SELECT
            user_id,
            email,
            password_hash,
            full_name,
            status,
            failed_login_attempts,
            account_locked_until
        FROM `{table_ref}`
        WHERE email = @email
        LIMIT 1
        """

        from google.cloud import bigquery
        users = execute_query(
            query,
            params=[bigquery.ScalarQueryParameter("email", "STRING", email)]
        )

        if not users:
            log_authentication_event(logger, 'login_failed_user_not_found', email=email)
            return unauthorized_response('Invalid email or password')

        user = users[0]

        # Check account status
        if user['status'] != 'active':
            log_authentication_event(logger, 'login_failed_inactive', user_id=user['user_id'])
            return unauthorized_response('Account is inactive')

        # Check if account is locked
        if user.get('account_locked_until'):
            locked_until = user['account_locked_until']
            if isinstance(locked_until, str):
                locked_until = datetime.fromisoformat(locked_until.replace('Z', '+00:00'))

            if locked_until > datetime.utcnow():
                log_authentication_event(logger, 'login_failed_locked', user_id=user['user_id'])
                return unauthorized_response('Account is temporarily locked. Please try again later.')

        # Verify password
        is_valid = verify_password(password, user['password_hash'])

        if not is_valid:
            # Increment failed login attempts
            failed_attempts = (user.get('failed_login_attempts') or 0) + 1

            # Lock account if too many failed attempts
            lock_until = None
            if failed_attempts >= config.MAX_LOGIN_ATTEMPTS:
                lock_until = (datetime.utcnow() + timedelta(minutes=config.ACCOUNT_LOCKOUT_MINUTES)).isoformat()

            # Update failed attempts
            update_query = f"""
            UPDATE `{table_ref}`
            SET
                failed_login_attempts = @failed_attempts,
                account_locked_until = @lock_until
            WHERE user_id = @user_id
            """

            client = get_bigquery_client()
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("failed_attempts", "INT64", failed_attempts),
                    bigquery.ScalarQueryParameter("lock_until", "TIMESTAMP", lock_until),
                    bigquery.ScalarQueryParameter("user_id", "STRING", user['user_id'])
                ]
            )
            client.query(update_query, job_config=job_config).result()

            log_authentication_event(
                logger,
                'login_failed_invalid_password',
                user_id=user['user_id'],
                failed_attempts=failed_attempts
            )

            return unauthorized_response('Invalid email or password')

        # Reset failed login attempts on successful login
        now = datetime.utcnow()
        update_query = f"""
        UPDATE `{table_ref}`
        SET
            failed_login_attempts = 0,
            account_locked_until = NULL,
            last_login = @last_login
        WHERE user_id = @user_id
        """

        client = get_bigquery_client()
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("last_login", "TIMESTAMP", now.isoformat()),
                bigquery.ScalarQueryParameter("user_id", "STRING", user['user_id'])
            ]
        )
        client.query(update_query, job_config=job_config).result()

        # Generate tokens
        access_token = generate_access_token(user['user_id'], user['email'])
        refresh_token, session_id = generate_refresh_token(user['user_id'], user['email'])

        log_authentication_event(logger, 'login_successful', user_id=user['user_id'], session_id=session_id)

        # Return tokens and user info
        return success_response(
            data={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': config.JWT_EXPIRATION_HOURS * 3600,  # seconds
                'user': {
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'full_name': user['full_name']
                }
            },
            message='Login successful'
        )

    except Exception as e:
        logger.exception('Login error', error=str(e))
        return error_response(
            message='Login failed',
            status_code=500,
            error_code='LOGIN_ERROR'
        )


def handle_refresh(request) -> tuple:
    """
    Handle token refresh

    POST /auth/refresh
    Body:
        {
            "refresh_token": "eyJhbGc..."
        }

    Returns:
        {
            "success": true,
            "data": {
                "access_token": "eyJhbGc...",
                "token_type": "Bearer",
                "expires_in": 86400
            }
        }
    """
    try:
        data = request.get_json()
        if not data or 'refresh_token' not in data:
            return bad_request_response('Refresh token is required')

        refresh_token = data['refresh_token']

        # Verify refresh token
        is_valid, payload, error = verify_token(refresh_token, token_type='refresh')

        if not is_valid:
            log_authentication_event(logger, 'token_refresh_failed', error=error)
            return unauthorized_response(error or 'Invalid refresh token')

        # Generate new access token
        access_token = generate_access_token(
            payload['user_id'],
            payload['email']
        )

        log_authentication_event(logger, 'token_refreshed', user_id=payload['user_id'])

        return success_response(
            data={
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': config.JWT_EXPIRATION_HOURS * 3600
            }
        )

    except Exception as e:
        logger.exception('Token refresh error', error=str(e))
        return error_response(
            message='Token refresh failed',
            status_code=500,
            error_code='REFRESH_ERROR'
        )


def handle_logout(request) -> tuple:
    """
    Handle user logout (revoke refresh token)

    POST /auth/logout
    Headers:
        Authorization: Bearer <access_token>
    Body:
        {
            "refresh_token": "eyJhbGc..."
        }

    Returns:
        {
            "success": true,
            "message": "Logged out successfully"
        }
    """
    try:
        data = request.get_json()
        if not data or 'refresh_token' not in data:
            return bad_request_response('Refresh token is required')

        refresh_token = data['refresh_token']

        # Verify refresh token (don't need to check if active, just get session_id)
        is_valid, payload, error = verify_token(refresh_token, token_type='refresh')

        if is_valid and payload:
            session_id = payload.get('sid')
            user_id = payload.get('user_id')

            if session_id:
                # Revoke session
                success = revoke_token(session_id, revoked_by=user_id)

                if success:
                    log_authentication_event(logger, 'logout_successful', user_id=user_id, session_id=session_id)
                    return success_response(
                        data=None,
                        message='Logged out successfully'
                    )

        log_authentication_event(logger, 'logout_failed', error='Invalid token')

        return success_response(
            data=None,
            message='Logged out'
        )

    except Exception as e:
        logger.exception('Logout error', error=str(e))
        return error_response(
            message='Logout failed',
            status_code=500,
            error_code='LOGOUT_ERROR'
        )


def handle_verify(request) -> tuple:
    """
    Verify access token validity

    POST /auth/verify
    Body:
        {
            "access_token": "eyJhbGc..."
        }

    Returns:
        {
            "success": true,
            "data": {
                "valid": true,
                "user_id": "123...",
                "email": "user@example.com",
                "expires_at": "2025-11-06T12:00:00Z"
            }
        }
    """
    try:
        data = request.get_json()
        if not data or 'access_token' not in data:
            return bad_request_response('Access token is required')

        access_token = data['access_token']

        # Verify token
        is_valid, payload, error = verify_token(access_token, token_type='access')

        if is_valid:
            from datetime import datetime
            exp_timestamp = payload.get('exp')
            expires_at = datetime.fromtimestamp(exp_timestamp).isoformat() + 'Z' if exp_timestamp else None

            return success_response(
                data={
                    'valid': True,
                    'user_id': payload.get('user_id'),
                    'email': payload.get('email'),
                    'expires_at': expires_at
                }
            )
        else:
            return success_response(
                data={
                    'valid': False,
                    'error': error
                }
            )

    except Exception as e:
        logger.exception('Token verification error', error=str(e))
        return error_response(
            message='Verification failed',
            status_code=500,
            error_code='VERIFY_ERROR'
        )


def handle_get_user(request) -> tuple:
    """
    Get current user information from access token

    GET /auth/me
    Headers:
        Authorization: Bearer <access_token>

    Returns:
        {
            "success": true,
            "data": {
                "user_id": "123...",
                "email": "user@example.com",
                "full_name": "John Doe",
                "status": "active",
                "created_at": "2025-11-05T12:00:00Z"
            }
        }
    """
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return unauthorized_response('Missing or invalid Authorization header')

        access_token = auth_header[7:]  # Remove 'Bearer ' prefix

        # Verify token
        is_valid, payload, error = verify_token(access_token, token_type='access')

        if not is_valid:
            return unauthorized_response(error or 'Invalid access token')

        user_id = payload.get('user_id')

        # Get user from database
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'users')
        query = f"""
        SELECT
            user_id,
            email,
            full_name,
            status,
            created_at,
            last_login
        FROM `{table_ref}`
        WHERE user_id = @user_id
        LIMIT 1
        """

        from google.cloud import bigquery
        users = execute_query(
            query,
            params=[bigquery.ScalarQueryParameter("user_id", "STRING", user_id)]
        )

        if not users:
            return unauthorized_response('User not found')

        user = users[0]

        return success_response(
            data={
                'user_id': user['user_id'],
                'email': user['email'],
                'full_name': user['full_name'],
                'status': user['status'],
                'created_at': user['created_at'],
                'last_login': user['last_login']
            }
        )

    except Exception as e:
        logger.exception('Get user error', error=str(e))
        return error_response(
            message='Failed to get user',
            status_code=500,
            error_code='GET_USER_ERROR'
        )

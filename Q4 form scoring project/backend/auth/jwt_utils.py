"""
JWT token generation and validation utilities
Handles access tokens (24hr) and refresh tokens (30 days)
Created: November 5, 2025
"""

import jwt
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from common.config import config
    from common.logger import get_logger
except ImportError:
    from config_standalone import config
    from logger_standalone import get_logger

logger = get_logger('auth.jwt')


def generate_access_token(user_id: str, email: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a JWT access token (24-hour expiration)

    Access tokens are short-lived and used for API authentication.
    They contain user identity claims and expire after 24 hours.

    Args:
        user_id: User's unique identifier (UUID)
        email: User's email address
        additional_claims: Optional additional claims to include in token

    Returns:
        str: JWT token string

    Token Claims:
        - user_id: User identifier
        - email: User email
        - type: 'access'
        - iat: Issued at timestamp
        - exp: Expiration timestamp (24 hours from now)
        - jti: JWT ID (unique token identifier)
        - [additional_claims]: Any extra claims provided

    Usage:
        token = generate_access_token(
            user_id='123e4567-e89b-12d3-a456-426614174000',
            email='user@example.com',
            additional_claims={'role': 'admin'}
        )

    Example Token:
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    now = datetime.utcnow()
    expiration = now + timedelta(hours=config.JWT_EXPIRATION_HOURS)
    token_id = str(uuid.uuid4())

    # Build payload
    payload = {
        'user_id': user_id,
        'email': email,
        'type': 'access',
        'iat': now,
        'exp': expiration,
        'jti': token_id
    }

    # Add additional claims if provided
    if additional_claims:
        payload.update(additional_claims)

    try:
        # Generate token
        token = jwt.encode(
            payload,
            config.JWT_SECRET_KEY,
            algorithm=config.JWT_ALGORITHM
        )

        logger.info(
            'Access token generated',
            user_id=user_id,
            email=email,
            expires_at=expiration.isoformat()
        )

        return token

    except Exception as e:
        logger.error('Failed to generate access token', user_id=user_id, error=str(e))
        raise


def generate_refresh_token(user_id: str, email: str) -> Tuple[str, str]:
    """
    Generate a JWT refresh token (30-day expiration) and store in database

    Refresh tokens are long-lived and used to obtain new access tokens.
    They are stored in the database with a hash for revocation support.

    Args:
        user_id: User's unique identifier
        email: User's email address

    Returns:
        Tuple[str, str]: (refresh_token, session_id)

    Session Storage:
        - Stores SHA-256 hash of token in auth.sessions table
        - Allows token revocation (logout)
        - Tracks user sessions

    Usage:
        refresh_token, session_id = generate_refresh_token(
            user_id='123e4567-e89b-12d3-a456-426614174000',
            email='user@example.com'
        )
        # Return refresh_token to client
        # Store session_id if needed for tracking
    """
    now = datetime.utcnow()
    expiration = now + timedelta(days=config.JWT_REFRESH_EXPIRATION_DAYS)
    token_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    # Build payload
    payload = {
        'user_id': user_id,
        'email': email,
        'type': 'refresh',
        'iat': now,
        'exp': expiration,
        'jti': token_id,
        'sid': session_id  # Session ID
    }

    try:
        # Generate token
        token = jwt.encode(
            payload,
            config.JWT_SECRET_KEY,
            algorithm=config.JWT_ALGORITHM
        )

        # Create SHA-256 hash of token for storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Store session in database
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'token_hash': token_hash,
            'created_at': now.isoformat(),
            'expires_at': expiration.isoformat(),
            'is_active': True,
            'revoked_at': None,
            'revoked_by': None,
            'user_agent': None,  # Can be populated from request headers
            'ip_address': None   # Can be populated from request
        }

        # Insert session into Firestore
        from firestore_client import create_session
        create_session(session_id, user_id, token_hash, expiration)

        logger.info(
            'Refresh token generated and session stored',
            user_id=user_id,
            session_id=session_id,
            expires_at=expiration.isoformat()
        )

        return token, session_id

    except Exception as e:
        logger.error('Failed to generate refresh token', user_id=user_id, error=str(e))
        raise


def verify_token(token: str, token_type: str = 'access') -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Verify and decode a JWT token

    Checks:
    - Token signature is valid
    - Token has not expired
    - Token type matches expected type
    - For refresh tokens: session is active in database

    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')

    Returns:
        Tuple[bool, Optional[Dict], Optional[str]]: (is_valid, payload, error_message)

    Usage:
        is_valid, payload, error = verify_token(token, 'access')
        if is_valid:
            user_id = payload['user_id']
            # Grant access
        else:
            return unauthorized_response(error)

    Error Messages:
        - "Token has expired"
        - "Invalid token signature"
        - "Invalid token type"
        - "Session has been revoked"
        - "Malformed token"
    """
    if not token:
        return False, None, "Token is required"

    try:
        # Decode and verify token
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )

        # Check token type
        if payload.get('type') != token_type:
            logger.warning(
                'Token type mismatch',
                expected=token_type,
                actual=payload.get('type')
            )
            return False, None, f"Invalid token type (expected {token_type})"

        # For refresh tokens, verify session is active
        if token_type == 'refresh':
            session_id = payload.get('sid')
            if not session_id:
                return False, None, "Invalid refresh token (missing session ID)"

            # Check if session is active
            is_active = _check_session_active(session_id, token)
            if not is_active:
                return False, None, "Session has been revoked"

        logger.debug('Token verified successfully', user_id=payload.get('user_id'), type=token_type)

        return True, payload, None

    except jwt.ExpiredSignatureError:
        logger.debug('Token verification failed - expired')
        return False, None, "Token has expired"

    except jwt.InvalidSignatureError:
        logger.warning('Token verification failed - invalid signature')
        return False, None, "Invalid token signature"

    except jwt.DecodeError:
        logger.warning('Token verification failed - malformed token')
        return False, None, "Malformed token"

    except Exception as e:
        logger.error('Token verification error', error=str(e))
        return False, None, "Token verification failed"


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token WITHOUT verification (for debugging/inspection)

    WARNING: Does not verify signature or expiration!
    Use verify_token() for authentication.

    Args:
        token: JWT token string

    Returns:
        Optional[Dict]: Token payload, or None if invalid

    Usage:
        payload = decode_token(token)
        if payload:
            print(f"Token expires at: {payload['exp']}")
    """
    try:
        # Decode without verification
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload

    except Exception as e:
        logger.error('Failed to decode token', error=str(e))
        return None


def revoke_token(session_id: str, revoked_by: Optional[str] = None) -> bool:
    """
    Revoke a refresh token session (logout)

    Marks the session as inactive in the database.
    The refresh token can no longer be used to obtain new access tokens.

    Args:
        session_id: Session identifier from refresh token
        revoked_by: Optional user_id of who revoked the token (for audit)

    Returns:
        bool: True if revoked successfully, False otherwise

    Usage:
        # User logout
        success = revoke_token(session_id, revoked_by=user_id)
        if success:
            return success_response({'message': 'Logged out successfully'})
    """
    try:
        from firestore_client import revoke_session
        revoke_session(session_id)
        logger.info('Session revoked', session_id=session_id, revoked_by=revoked_by)
        return True

    except Exception as e:
        logger.error('Failed to revoke session', session_id=session_id, error=str(e))
        return False


def revoke_all_user_sessions(user_id: str) -> int:
    """
    Revoke all active sessions for a user (logout from all devices)

    Args:
        user_id: User identifier

    Returns:
        int: Number of sessions revoked

    Usage:
        # User changed password, logout from all devices
        count = revoke_all_user_sessions(user_id)
        logger.info(f'Revoked {count} sessions for security')
    """
    try:
        from firestore_client import revoke_all_user_sessions_firestore
        rows_affected = revoke_all_user_sessions_firestore(user_id)

        logger.info('All user sessions revoked', user_id=user_id, count=rows_affected)

        return rows_affected

    except Exception as e:
        logger.error('Failed to revoke all user sessions', user_id=user_id, error=str(e))
        return 0


def cleanup_expired_sessions() -> int:
    """
    Remove expired sessions from database (cleanup job)

    Should be run periodically (e.g., daily cron job)

    Returns:
        int: Number of sessions deleted

    Usage:
        # Run as Cloud Scheduler job
        deleted = cleanup_expired_sessions()
        logger.info(f'Cleaned up {deleted} expired sessions')
    """
    try:
        client = get_bigquery_client()
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'sessions')

        query = f"""
        DELETE FROM `{table_ref}`
        WHERE expires_at < CURRENT_TIMESTAMP()
        """

        query_job = client.query(query)
        query_job.result()

        rows_affected = query_job.num_dml_affected_rows

        logger.info('Expired sessions cleaned up', count=rows_affected)

        return rows_affected

    except Exception as e:
        logger.error('Failed to cleanup expired sessions', error=str(e))
        return 0


def _check_session_active(session_id: str, token: str) -> bool:
    """
    Internal helper to check if a session is active

    Verifies:
    - Session exists
    - Session is not revoked (is_active = TRUE)
    - Token hash matches stored hash
    - Session has not expired

    Args:
        session_id: Session identifier
        token: Refresh token string

    Returns:
        bool: True if session is active and valid
    """
    try:
        # Calculate token hash
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Query session from database
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'sessions')
        query = f"""
        SELECT
            is_active,
            expires_at,
            token_hash
        FROM `{table_ref}`
        WHERE session_id = @session_id
        LIMIT 1
        """

        from google.cloud import bigquery
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
            ]
        )

        results = execute_query(query, params=job_config.query_parameters)

        if not results:
            logger.warning('Session not found', session_id=session_id)
            return False

        session = results[0]

        # Check if active
        if not session.get('is_active'):
            logger.debug('Session is revoked', session_id=session_id)
            return False

        # Check token hash matches (prevents token reuse after refresh)
        if session.get('token_hash') != token_hash:
            logger.warning('Token hash mismatch', session_id=session_id)
            return False

        # Check if expired (extra check beyond JWT expiration)
        expires_at = session.get('expires_at')
        if expires_at and isinstance(expires_at, str):
            from datetime import datetime
            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if expires_dt < datetime.utcnow():
                logger.debug('Session expired', session_id=session_id)
                return False

        return True

    except Exception as e:
        logger.error('Error checking session active', session_id=session_id, error=str(e))
        return False

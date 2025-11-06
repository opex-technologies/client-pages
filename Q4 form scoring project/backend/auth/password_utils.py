"""
Password hashing and verification utilities
Uses bcrypt with cost factor 12 for secure password storage
Created: November 5, 2025
"""

import bcrypt
from typing import Tuple
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

logger = get_logger('auth.password')


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with configured cost factor

    Uses bcrypt with cost factor 12 (4,096 iterations), which provides:
    - ~250ms hashing time (acceptable UX)
    - ~4 hashes/second for attackers (makes brute-force impractical)
    - Industry standard for 2025

    Args:
        password: Plain text password to hash

    Returns:
        str: Bcrypt hashed password (60 characters)

    Raises:
        ValueError: If password is empty or invalid

    Usage:
        password_hash = hash_password('MyP@ssw0rd123')
        # Store password_hash in database

    Example Output:
        '$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    """
    if not password:
        logger.warning('Attempted to hash empty password')
        raise ValueError('Password cannot be empty')

    if not isinstance(password, str):
        logger.warning('Attempted to hash non-string password', password_type=type(password).__name__)
        raise ValueError('Password must be a string')

    try:
        # Generate salt with configured rounds (cost factor)
        salt = bcrypt.gensalt(rounds=config.BCRYPT_ROUNDS)

        # Convert password to bytes
        password_bytes = password.encode('utf-8')

        # Hash password
        hashed = bcrypt.hashpw(password_bytes, salt)

        # Convert back to string for storage
        hashed_str = hashed.decode('utf-8')

        logger.debug('Password hashed successfully', cost_factor=config.BCRYPT_ROUNDS)

        return hashed_str

    except Exception as e:
        logger.error('Password hashing failed', error=str(e))
        raise


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a bcrypt hash

    Uses constant-time comparison to prevent timing attacks

    Args:
        password: Plain text password to verify
        password_hash: Bcrypt hash from database

    Returns:
        bool: True if password matches hash, False otherwise

    Usage:
        is_valid = verify_password('MyP@ssw0rd123', stored_hash)
        if is_valid:
            # Grant access
        else:
            # Deny access

    Security Notes:
        - Takes ~250ms (same as hashing) regardless of match
        - Prevents timing attacks
        - Returns False for any errors (fails securely)
    """
    if not password or not password_hash:
        logger.warning('Password verification attempted with empty values')
        return False

    if not isinstance(password, str) or not isinstance(password_hash, str):
        logger.warning('Password verification attempted with invalid types')
        return False

    try:
        # Convert to bytes
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')

        # Verify password (constant-time comparison)
        is_valid = bcrypt.checkpw(password_bytes, hash_bytes)

        if is_valid:
            logger.debug('Password verification successful')
        else:
            logger.debug('Password verification failed - password mismatch')

        return is_valid

    except Exception as e:
        # Fail securely - don't reveal error details to caller
        logger.error('Password verification error', error=str(e))
        return False


def check_password_strength(password: str) -> Tuple[bool, list]:
    """
    Check if password meets security requirements

    Requirements (from config):
    - Minimum length (default: 8 characters)
    - At least one uppercase letter (if configured)
    - At least one lowercase letter (if configured)
    - At least one digit (if configured)
    - At least one special character (if configured)

    Args:
        password: Password to check

    Returns:
        Tuple[bool, list]: (is_strong, list_of_issues)

    Usage:
        is_strong, issues = check_password_strength('weak')
        if not is_strong:
            return error_response(f"Password too weak: {', '.join(issues)}")
    """
    from common.validators import validate_password

    is_valid, error_message = validate_password(password)

    if is_valid:
        return True, []
    else:
        # Convert single error message to list
        return False, [error_message]


def hash_password_batch(passwords: list) -> list:
    """
    Hash multiple passwords in batch (for data migration)

    Args:
        passwords: List of plain text passwords

    Returns:
        list: List of hashed passwords in same order

    Usage:
        hashes = hash_password_batch(['pass1', 'pass2', 'pass3'])

    Note:
        - Use for initial data import only
        - Each hash takes ~250ms, so 100 passwords = ~25 seconds
        - Consider running in background for large batches
    """
    logger.info('Batch password hashing started', count=len(passwords))

    hashed = []
    for i, password in enumerate(passwords):
        try:
            hashed.append(hash_password(password))

            if (i + 1) % 10 == 0:
                logger.debug('Batch hashing progress', completed=i + 1, total=len(passwords))

        except Exception as e:
            logger.error('Failed to hash password in batch', index=i, error=str(e))
            hashed.append(None)

    logger.info('Batch password hashing completed', total=len(passwords), successful=len([h for h in hashed if h]))

    return hashed


def needs_rehash(password_hash: str) -> bool:
    """
    Check if a password hash needs to be rehashed with current cost factor

    Use this to gradually upgrade password hashes when cost factor increases

    Args:
        password_hash: Existing bcrypt hash from database

    Returns:
        bool: True if hash should be regenerated with new cost factor

    Usage:
        if needs_rehash(user.password_hash):
            # User logged in successfully, rehash with new cost factor
            new_hash = hash_password(password)
            update_user_password_hash(user.user_id, new_hash)
    """
    try:
        # Extract cost factor from hash
        # Bcrypt hash format: $2b$12$... where 12 is the cost factor
        hash_parts = password_hash.split('$')
        if len(hash_parts) < 3:
            return True  # Invalid hash format, needs rehash

        current_cost = int(hash_parts[2])
        target_cost = config.BCRYPT_ROUNDS

        # Needs rehash if current cost is lower than configured cost
        needs_update = current_cost < target_cost

        if needs_update:
            logger.info('Password hash needs rehash', current_cost=current_cost, target_cost=target_cost)

        return needs_update

    except Exception as e:
        logger.error('Error checking if hash needs rehash', error=str(e))
        return True  # Assume needs rehash on error

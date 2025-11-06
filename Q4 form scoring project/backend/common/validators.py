"""
Input validation utilities for backend services
Provides common validation functions for user inputs
Created: November 5, 2025
"""

import re
import uuid
from typing import Dict, List, Any, Optional, Tuple
from .config import config


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email address format

    Args:
        email: Email address to validate

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)

    Usage:
        is_valid, error = validate_email('user@example.com')
        if not is_valid:
            return error_response(error)
    """
    if not email:
        return False, "Email is required"

    if not isinstance(email, str):
        return False, "Email must be a string"

    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, email):
        return False, "Invalid email format"

    if len(email) > 255:
        return False, "Email too long (max 255 characters)"

    return True, None


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength based on config rules

    Args:
        password: Password to validate

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)

    Usage:
        is_valid, error = validate_password('MyP@ssw0rd')
        if not is_valid:
            return error_response(error)
    """
    if not password:
        return False, "Password is required"

    if not isinstance(password, str):
        return False, "Password must be a string"

    # Check minimum length
    if len(password) < config.MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters"

    # Check maximum length
    if len(password) > 128:
        return False, "Password too long (max 128 characters)"

    # Check uppercase requirement
    if config.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    # Check lowercase requirement
    if config.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    # Check digit requirement
    if config.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    # Check special character requirement
    if config.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"

    return True, None


def validate_uuid(value: str, field_name: str = "ID") -> Tuple[bool, Optional[str]]:
    """
    Validate UUID format

    Args:
        value: UUID string to validate
        field_name: Name of the field (for error messages)

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)

    Usage:
        is_valid, error = validate_uuid(user_id, 'user_id')
        if not is_valid:
            return error_response(error)
    """
    if not value:
        return False, f"{field_name} is required"

    if not isinstance(value, str):
        return False, f"{field_name} must be a string"

    try:
        uuid.UUID(value)
        return True, None
    except ValueError:
        return False, f"Invalid {field_name} format (must be UUID)"


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate that required fields are present in data

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)

    Usage:
        is_valid, error = validate_required_fields(
            request_data,
            ['email', 'password', 'full_name']
        )
        if not is_valid:
            return error_response(error)
    """
    if not isinstance(data, dict):
        return False, "Invalid data format (must be object)"

    missing_fields = [field for field in required_fields if field not in data or not data[field]]

    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    return True, None


def sanitize_input(value: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length (default: 1000)

    Returns:
        str: Sanitized string

    Usage:
        clean_name = sanitize_input(request_data['name'], max_length=100)
    """
    if not value:
        return ""

    if not isinstance(value, str):
        value = str(value)

    # Truncate to max length
    value = value[:max_length]

    # Remove null bytes
    value = value.replace('\x00', '')

    # Strip whitespace
    value = value.strip()

    return value


def validate_permission_level(level: str) -> Tuple[bool, Optional[str]]:
    """
    Validate permission level value

    Args:
        level: Permission level to validate

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)

    Usage:
        is_valid, error = validate_permission_level('admin')
        if not is_valid:
            return error_response(error)
    """
    valid_levels = ['view', 'edit', 'admin']

    if not level:
        return False, "Permission level is required"

    if level not in valid_levels:
        return False, f"Invalid permission level. Must be one of: {', '.join(valid_levels)}"

    return True, None


def validate_opportunity_type(opp_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate opportunity type value

    Args:
        opp_type: Opportunity type to validate

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    valid_types = [
        'All',
        'Managed Service Provider',
        'Cloud',
        'CCaaS',
        'UCaaS',
        'Network',
        'Security',
        'Data Center',
        'Expense Management'
    ]

    if not opp_type:
        return False, "Opportunity type is required"

    if opp_type not in valid_types:
        return False, f"Invalid opportunity type. Must be one of: {', '.join(valid_types)}"

    return True, None


def validate_input_type(input_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate question input type

    Args:
        input_type: Input type to validate

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    valid_types = ['text', 'textarea', 'number', 'radio', 'checkbox', 'select', 'date', 'email', 'phone']

    if not input_type:
        return False, "Input type is required"

    if input_type not in valid_types:
        return False, f"Invalid input type. Must be one of: {', '.join(valid_types)}"

    return True, None


def validate_weight(weight: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate question weight value

    Args:
        weight: Weight to validate (can be "Info" or numeric)

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not weight:
        return False, "Weight is required"

    # Allow "Info" weight
    if isinstance(weight, str) and weight == "Info":
        return True, None

    # Validate numeric weight
    try:
        weight_num = float(weight) if isinstance(weight, str) else weight
        if weight_num < 0 or weight_num > 100:
            return False, "Weight must be between 0 and 100"
        return True, None
    except (ValueError, TypeError):
        return False, "Weight must be 'Info' or a number between 0 and 100"


def validate_json_structure(data: Any, expected_type: type) -> Tuple[bool, Optional[str]]:
    """
    Validate JSON data structure type

    Args:
        data: Data to validate
        expected_type: Expected Python type (dict, list, etc.)

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)

    Usage:
        is_valid, error = validate_json_structure(request_data, dict)
        if not is_valid:
            return error_response(error)
    """
    if not isinstance(data, expected_type):
        return False, f"Invalid data type. Expected {expected_type.__name__}"

    return True, None


def validate_pagination(page: Any, page_size: Any) -> Tuple[bool, Optional[str], int, int]:
    """
    Validate and sanitize pagination parameters

    Args:
        page: Page number
        page_size: Items per page

    Returns:
        Tuple[bool, Optional[str], int, int]: (is_valid, error_message, sanitized_page, sanitized_page_size)

    Usage:
        is_valid, error, page, page_size = validate_pagination(
            request.args.get('page'),
            request.args.get('page_size')
        )
        if not is_valid:
            return error_response(error)
    """
    # Default values
    default_page = 1
    default_page_size = config.DEFAULT_PAGE_SIZE

    # Parse page
    try:
        page_num = int(page) if page else default_page
        if page_num < 1:
            return False, "Page number must be at least 1", 0, 0
    except (ValueError, TypeError):
        return False, "Invalid page number", 0, 0

    # Parse page_size
    try:
        size = int(page_size) if page_size else default_page_size
        if size < 1:
            return False, "Page size must be at least 1", 0, 0
        if size > config.MAX_PAGE_SIZE:
            return False, f"Page size cannot exceed {config.MAX_PAGE_SIZE}", 0, 0
    except (ValueError, TypeError):
        return False, "Invalid page size", 0, 0

    return True, None, page_num, size

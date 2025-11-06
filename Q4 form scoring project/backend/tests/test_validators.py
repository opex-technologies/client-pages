"""
Unit tests for validators module
Created: November 5, 2025
"""

import pytest
from common.validators import (
    validate_email,
    validate_password,
    validate_uuid,
    validate_required_fields,
    sanitize_input,
    validate_permission_level,
    validate_weight,
    validate_pagination
)


class TestEmailValidation:
    """Tests for email validation"""

    def test_valid_email(self):
        """Test valid email addresses"""
        valid_emails = [
            'user@example.com',
            'test.user@example.com',
            'user+tag@example.co.uk',
            'user123@sub.example.com'
        ]

        for email in valid_emails:
            is_valid, error = validate_email(email)
            assert is_valid is True
            assert error is None

    def test_invalid_email_format(self):
        """Test invalid email formats"""
        invalid_emails = [
            'not-an-email',
            '@example.com',
            'user@',
            'user @example.com',
            'user@example',
            ''
        ]

        for email in invalid_emails:
            is_valid, error = validate_email(email)
            assert is_valid is False
            assert error is not None

    def test_email_too_long(self):
        """Test email exceeds max length"""
        long_email = 'a' * 250 + '@example.com'
        is_valid, error = validate_email(long_email)
        assert is_valid is False
        assert 'too long' in error.lower()

    def test_email_none(self):
        """Test None email"""
        is_valid, error = validate_email(None)
        assert is_valid is False
        assert 'required' in error.lower()


class TestPasswordValidation:
    """Tests for password validation"""

    def test_valid_password(self):
        """Test valid passwords"""
        is_valid, error = validate_password('MyP@ssw0rd')
        assert is_valid is True
        assert error is None

    def test_password_too_short(self):
        """Test password below minimum length"""
        is_valid, error = validate_password('Short1!')
        assert is_valid is False
        assert 'at least' in error.lower()

    def test_password_missing_uppercase(self):
        """Test password missing uppercase letter"""
        is_valid, error = validate_password('myp@ssw0rd')
        assert is_valid is False
        assert 'uppercase' in error.lower()

    def test_password_missing_lowercase(self):
        """Test password missing lowercase letter"""
        is_valid, error = validate_password('MYP@SSW0RD')
        assert is_valid is False
        assert 'lowercase' in error.lower()

    def test_password_missing_digit(self):
        """Test password missing digit"""
        is_valid, error = validate_password('MyP@ssword')
        assert is_valid is False
        assert 'digit' in error.lower()

    def test_password_missing_special(self):
        """Test password missing special character"""
        is_valid, error = validate_password('MyPassw0rd')
        assert is_valid is False
        assert 'special' in error.lower()

    def test_password_too_long(self):
        """Test password exceeds max length"""
        long_password = 'A' * 130 + 'a1!'
        is_valid, error = validate_password(long_password)
        assert is_valid is False
        assert 'too long' in error.lower()


class TestUuidValidation:
    """Tests for UUID validation"""

    def test_valid_uuid(self):
        """Test valid UUID"""
        import uuid
        valid_uuid = str(uuid.uuid4())
        is_valid, error = validate_uuid(valid_uuid, 'test_id')
        assert is_valid is True
        assert error is None

    def test_invalid_uuid(self):
        """Test invalid UUID format"""
        is_valid, error = validate_uuid('not-a-uuid', 'test_id')
        assert is_valid is False
        assert 'invalid' in error.lower()

    def test_uuid_none(self):
        """Test None UUID"""
        is_valid, error = validate_uuid(None, 'test_id')
        assert is_valid is False
        assert 'required' in error.lower()


class TestRequiredFields:
    """Tests for required fields validation"""

    def test_all_required_fields_present(self):
        """Test when all required fields are present"""
        data = {
            'email': 'user@example.com',
            'password': 'MyP@ssw0rd',
            'full_name': 'Test User'
        }
        is_valid, error = validate_required_fields(data, ['email', 'password', 'full_name'])
        assert is_valid is True
        assert error is None

    def test_missing_required_field(self):
        """Test when required field is missing"""
        data = {
            'email': 'user@example.com',
            'password': 'MyP@ssw0rd'
        }
        is_valid, error = validate_required_fields(data, ['email', 'password', 'full_name'])
        assert is_valid is False
        assert 'full_name' in error

    def test_empty_required_field(self):
        """Test when required field is empty string"""
        data = {
            'email': 'user@example.com',
            'password': '',
            'full_name': 'Test User'
        }
        is_valid, error = validate_required_fields(data, ['email', 'password', 'full_name'])
        assert is_valid is False
        assert 'password' in error


class TestSanitizeInput:
    """Tests for input sanitization"""

    def test_sanitize_normal_input(self):
        """Test sanitizing normal input"""
        result = sanitize_input('  Test Input  ')
        assert result == 'Test Input'

    def test_sanitize_null_bytes(self):
        """Test removal of null bytes"""
        result = sanitize_input('Test\x00Input')
        assert result == 'TestInput'

    def test_sanitize_max_length(self):
        """Test truncation to max length"""
        long_input = 'a' * 2000
        result = sanitize_input(long_input, max_length=100)
        assert len(result) == 100

    def test_sanitize_empty_input(self):
        """Test empty input"""
        result = sanitize_input('')
        assert result == ''


class TestPermissionLevel:
    """Tests for permission level validation"""

    def test_valid_permission_levels(self):
        """Test valid permission levels"""
        valid_levels = ['view', 'edit', 'admin']

        for level in valid_levels:
            is_valid, error = validate_permission_level(level)
            assert is_valid is True
            assert error is None

    def test_invalid_permission_level(self):
        """Test invalid permission level"""
        is_valid, error = validate_permission_level('superuser')
        assert is_valid is False
        assert 'invalid' in error.lower()


class TestWeightValidation:
    """Tests for weight validation"""

    def test_valid_numeric_weight(self):
        """Test valid numeric weights"""
        valid_weights = [0, 10, 50, 100, '50', '75.5']

        for weight in valid_weights:
            is_valid, error = validate_weight(weight)
            assert is_valid is True
            assert error is None

    def test_valid_info_weight(self):
        """Test 'Info' weight"""
        is_valid, error = validate_weight('Info')
        assert is_valid is True
        assert error is None

    def test_invalid_weight_range(self):
        """Test weight out of range"""
        invalid_weights = [-1, 101, 150]

        for weight in invalid_weights:
            is_valid, error = validate_weight(weight)
            assert is_valid is False
            assert 'between 0 and 100' in error

    def test_invalid_weight_format(self):
        """Test invalid weight format"""
        is_valid, error = validate_weight('not-a-number')
        assert is_valid is False
        assert 'must be' in error.lower()


class TestPaginationValidation:
    """Tests for pagination validation"""

    def test_valid_pagination(self):
        """Test valid pagination parameters"""
        is_valid, error, page, page_size = validate_pagination('2', '50')
        assert is_valid is True
        assert error is None
        assert page == 2
        assert page_size == 50

    def test_pagination_defaults(self):
        """Test pagination with default values"""
        is_valid, error, page, page_size = validate_pagination(None, None)
        assert is_valid is True
        assert error is None
        assert page == 1
        assert page_size == 50  # DEFAULT_PAGE_SIZE

    def test_invalid_page_number(self):
        """Test invalid page number"""
        is_valid, error, _, _ = validate_pagination('0', '50')
        assert is_valid is False
        assert 'at least 1' in error

    def test_invalid_page_size(self):
        """Test invalid page size"""
        is_valid, error, _, _ = validate_pagination('1', '0')
        assert is_valid is False
        assert 'at least 1' in error

    def test_page_size_exceeds_max(self):
        """Test page size exceeds maximum"""
        is_valid, error, _, _ = validate_pagination('1', '200')
        assert is_valid is False
        assert 'cannot exceed' in error

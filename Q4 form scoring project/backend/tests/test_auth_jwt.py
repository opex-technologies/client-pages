"""
Unit tests for JWT token utilities
Tests token generation, validation, and session management
Created: November 5, 2025
"""

import pytest
import jwt
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add auth directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../auth')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jwt_utils import (
    generate_access_token,
    generate_refresh_token,
    verify_token,
    decode_token,
    revoke_token,
    revoke_all_user_sessions,
    cleanup_expired_sessions
)
from common.config import config


class TestAccessTokenGeneration:
    """Tests for access token generation"""

    def test_generate_access_token_basic(self):
        """Test basic access token generation"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        token = generate_access_token(user_id, email)

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode token (without verification for testing)
        payload = decode_token(token)

        assert payload['user_id'] == user_id
        assert payload['email'] == email
        assert payload['type'] == 'access'
        assert 'iat' in payload
        assert 'exp' in payload
        assert 'jti' in payload

    def test_generate_access_token_with_additional_claims(self):
        """Test access token with additional claims"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'
        additional_claims = {'role': 'admin', 'permissions': ['read', 'write']}

        token = generate_access_token(user_id, email, additional_claims)
        payload = decode_token(token)

        assert payload['role'] == 'admin'
        assert payload['permissions'] == ['read', 'write']

    def test_access_token_expiration_time(self):
        """Test that access token has correct expiration time (24 hours)"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        token = generate_access_token(user_id, email)
        payload = decode_token(token)

        # Calculate expected expiration (24 hours from now)
        now = datetime.utcnow()
        expected_exp = now + timedelta(hours=config.JWT_EXPIRATION_HOURS)

        # Allow 5 second variance for test execution time
        actual_exp = datetime.fromtimestamp(payload['exp'])
        time_diff = abs((actual_exp - expected_exp).total_seconds())

        assert time_diff < 5  # Within 5 seconds


class TestRefreshTokenGeneration:
    """Tests for refresh token generation"""

    @patch('jwt_utils.insert_rows')
    def test_generate_refresh_token_basic(self, mock_insert):
        """Test basic refresh token generation"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        token, session_id = generate_refresh_token(user_id, email)

        # Token should be generated
        assert isinstance(token, str)
        assert len(token) > 0

        # Session ID should be returned
        assert isinstance(session_id, str)
        assert len(session_id) > 0

        # Decode token
        payload = decode_token(token)

        assert payload['user_id'] == user_id
        assert payload['email'] == email
        assert payload['type'] == 'refresh'
        assert payload['sid'] == session_id

        # Session should be inserted into database
        mock_insert.assert_called_once()

    @patch('jwt_utils.insert_rows')
    def test_refresh_token_expiration_time(self, mock_insert):
        """Test that refresh token has correct expiration time (30 days)"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        token, session_id = generate_refresh_token(user_id, email)
        payload = decode_token(token)

        # Calculate expected expiration (30 days from now)
        now = datetime.utcnow()
        expected_exp = now + timedelta(days=config.JWT_REFRESH_EXPIRATION_DAYS)

        # Allow 5 second variance
        actual_exp = datetime.fromtimestamp(payload['exp'])
        time_diff = abs((actual_exp - expected_exp).total_seconds())

        assert time_diff < 5


class TestTokenVerification:
    """Tests for token verification"""

    def test_verify_valid_access_token(self):
        """Test verification of valid access token"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        token = generate_access_token(user_id, email)

        is_valid, payload, error = verify_token(token, 'access')

        assert is_valid is True
        assert payload is not None
        assert error is None
        assert payload['user_id'] == user_id

    def test_verify_expired_token(self):
        """Test verification of expired token"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        # Create token that's already expired
        payload = {
            'user_id': user_id,
            'email': email,
            'type': 'access',
            'iat': datetime.utcnow() - timedelta(hours=25),
            'exp': datetime.utcnow() - timedelta(hours=1),
            'jti': 'test-jti'
        }

        token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

        is_valid, payload, error = verify_token(token, 'access')

        assert is_valid is False
        assert payload is None
        assert 'expired' in error.lower()

    def test_verify_invalid_signature(self):
        """Test verification of token with invalid signature"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        # Create token with wrong secret
        payload = {
            'user_id': user_id,
            'email': email,
            'type': 'access',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=24),
            'jti': 'test-jti'
        }

        token = jwt.encode(payload, 'wrong-secret-key', algorithm='HS256')

        is_valid, payload, error = verify_token(token, 'access')

        assert is_valid is False
        assert 'signature' in error.lower()

    def test_verify_wrong_token_type(self):
        """Test verification with wrong token type"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        token = generate_access_token(user_id, email)

        # Try to verify as refresh token
        is_valid, payload, error = verify_token(token, 'refresh')

        assert is_valid is False
        assert 'type' in error.lower()

    def test_verify_malformed_token(self):
        """Test verification of malformed token"""
        is_valid, payload, error = verify_token('not-a-valid-jwt-token', 'access')

        assert is_valid is False
        assert 'malformed' in error.lower()

    def test_verify_empty_token(self):
        """Test verification of empty token"""
        is_valid, payload, error = verify_token('', 'access')

        assert is_valid is False
        assert 'required' in error.lower()


class TestTokenDecoding:
    """Tests for token decoding (without verification)"""

    def test_decode_valid_token(self):
        """Test decoding valid token"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        token = generate_access_token(user_id, email)
        payload = decode_token(token)

        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['email'] == email

    def test_decode_expired_token(self):
        """Test that decode works on expired token (no verification)"""
        payload_data = {
            'user_id': 'test-user',
            'email': 'user@example.com',
            'type': 'access',
            'iat': datetime.utcnow() - timedelta(hours=25),
            'exp': datetime.utcnow() - timedelta(hours=1),
            'jti': 'test-jti'
        }

        token = jwt.encode(payload_data, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        payload = decode_token(token)

        # Should decode successfully (no verification)
        assert payload is not None
        assert payload['user_id'] == 'test-user'

    def test_decode_malformed_token(self):
        """Test decoding malformed token"""
        payload = decode_token('not-a-valid-token')

        assert payload is None


@pytest.mark.integration
class TestSessionManagement:
    """Integration tests for session management"""

    @patch('jwt_utils.get_bigquery_client')
    def test_revoke_token_success(self, mock_client):
        """Test successful token revocation"""
        # Mock BigQuery client
        mock_job = MagicMock()
        mock_job.result = MagicMock()
        mock_job.num_dml_affected_rows = 1

        mock_client.return_value.query.return_value = mock_job

        session_id = '123e4567-e89b-12d3-a456-426614174000'
        revoked_by = 'user-123'

        success = revoke_token(session_id, revoked_by)

        assert success is True
        mock_client.return_value.query.assert_called_once()

    @patch('jwt_utils.get_bigquery_client')
    def test_revoke_token_not_found(self, mock_client):
        """Test revoking non-existent token"""
        # Mock no rows affected
        mock_job = MagicMock()
        mock_job.result = MagicMock()
        mock_job.num_dml_affected_rows = 0

        mock_client.return_value.query.return_value = mock_job

        session_id = 'non-existent'
        success = revoke_token(session_id)

        assert success is False

    @patch('jwt_utils.get_bigquery_client')
    def test_revoke_all_user_sessions(self, mock_client):
        """Test revoking all sessions for a user"""
        # Mock 3 sessions revoked
        mock_job = MagicMock()
        mock_job.result = MagicMock()
        mock_job.num_dml_affected_rows = 3

        mock_client.return_value.query.return_value = mock_job

        user_id = '123e4567-e89b-12d3-a456-426614174000'
        count = revoke_all_user_sessions(user_id)

        assert count == 3

    @patch('jwt_utils.get_bigquery_client')
    def test_cleanup_expired_sessions(self, mock_client):
        """Test cleanup of expired sessions"""
        # Mock 10 expired sessions deleted
        mock_job = MagicMock()
        mock_job.result = MagicMock()
        mock_job.num_dml_affected_rows = 10

        mock_client.return_value.query.return_value = mock_job

        count = cleanup_expired_sessions()

        assert count == 10


class TestTokenSecurity:
    """Security tests for JWT tokens"""

    def test_token_unique_per_generation(self):
        """Test that each token generation is unique"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        tokens = [generate_access_token(user_id, email) for _ in range(10)]

        # All tokens should be unique
        assert len(set(tokens)) == 10

    def test_token_contains_no_sensitive_data(self):
        """Test that token doesn't contain password or sensitive data"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        token = generate_access_token(user_id, email)
        payload = decode_token(token)

        # Payload should not contain password_hash or other sensitive data
        assert 'password' not in payload
        assert 'password_hash' not in payload
        assert 'secret' not in payload

    def test_cannot_modify_token_claims(self):
        """Test that modifying token claims invalidates signature"""
        user_id = '123e4567-e89b-12d3-a456-426614174000'
        email = 'user@example.com'

        token = generate_access_token(user_id, email)

        # Try to decode and re-encode with modified claims
        payload = decode_token(token)
        payload['user_id'] = 'different-user-id'

        modified_token = jwt.encode(payload, 'wrong-secret', algorithm='HS256')

        # Modified token should fail verification
        is_valid, _, error = verify_token(modified_token, 'access')

        assert is_valid is False

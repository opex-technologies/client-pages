"""
Unit tests for password hashing utilities
Tests bcrypt cost factor 12 implementation
Created: November 5, 2025
"""

import pytest
import sys
import os

# Add auth directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../auth')))

from password_utils import (
    hash_password,
    verify_password,
    check_password_strength,
    hash_password_batch,
    needs_rehash
)


class TestPasswordHashing:
    """Tests for password hashing with bcrypt cost factor 12"""

    def test_hash_password_basic(self):
        """Test basic password hashing"""
        password = 'MyP@ssw0rd123'
        hashed = hash_password(password)

        # Check hash format (bcrypt produces 60-character strings)
        assert isinstance(hashed, str)
        assert len(hashed) == 60
        assert hashed.startswith('$2b$12$')  # bcrypt with cost factor 12

    def test_hash_password_unique_salts(self):
        """Test that same password produces different hashes (unique salts)"""
        password = 'MyP@ssw0rd123'
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Same password should produce different hashes due to random salts
        assert hash1 != hash2

    def test_hash_password_empty(self):
        """Test hashing empty password raises error"""
        with pytest.raises(ValueError, match='cannot be empty'):
            hash_password('')

    def test_hash_password_none(self):
        """Test hashing None password raises error"""
        with pytest.raises(ValueError, match='cannot be empty'):
            hash_password(None)

    def test_hash_password_non_string(self):
        """Test hashing non-string password raises error"""
        with pytest.raises(ValueError, match='must be a string'):
            hash_password(12345)


class TestPasswordVerification:
    """Tests for password verification"""

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = 'MyP@ssw0rd123'
        hashed = hash_password(password)

        # Verify correct password
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = 'MyP@ssw0rd123'
        hashed = hash_password(password)

        # Verify incorrect password
        assert verify_password('WrongPassword', hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive"""
        password = 'MyP@ssw0rd123'
        hashed = hash_password(password)

        # Different case should not match
        assert verify_password('myp@ssw0rd123', hashed) is False

    def test_verify_password_empty(self):
        """Test verification with empty password"""
        hashed = hash_password('ValidPassword123!')

        assert verify_password('', hashed) is False

    def test_verify_password_empty_hash(self):
        """Test verification with empty hash"""
        assert verify_password('MyP@ssw0rd123', '') is False

    def test_verify_password_invalid_hash(self):
        """Test verification with invalid hash format"""
        # Should fail securely (return False, not raise exception)
        assert verify_password('MyP@ssw0rd123', 'invalid-hash') is False


class TestPasswordStrength:
    """Tests for password strength validation"""

    def test_strong_password(self):
        """Test strong password passes validation"""
        is_strong, issues = check_password_strength('MyP@ssw0rd123')

        assert is_strong is True
        assert len(issues) == 0

    def test_weak_password_too_short(self):
        """Test weak password (too short)"""
        is_strong, issues = check_password_strength('Pass1!')

        assert is_strong is False
        assert len(issues) > 0
        assert any('at least' in issue.lower() for issue in issues)

    def test_weak_password_no_uppercase(self):
        """Test weak password (no uppercase)"""
        is_strong, issues = check_password_strength('myp@ssw0rd123')

        assert is_strong is False
        assert any('uppercase' in issue.lower() for issue in issues)

    def test_weak_password_no_lowercase(self):
        """Test weak password (no lowercase)"""
        is_strong, issues = check_password_strength('MYP@SSW0RD123')

        assert is_strong is False
        assert any('lowercase' in issue.lower() for issue in issues)

    def test_weak_password_no_digit(self):
        """Test weak password (no digit)"""
        is_strong, issues = check_password_strength('MyP@ssword')

        assert is_strong is False
        assert any('digit' in issue.lower() for issue in issues)

    def test_weak_password_no_special(self):
        """Test weak password (no special character)"""
        is_strong, issues = check_password_strength('MyPassword123')

        assert is_strong is False
        assert any('special' in issue.lower() for issue in issues)


class TestPasswordBatchHashing:
    """Tests for batch password hashing"""

    def test_hash_password_batch(self):
        """Test batch password hashing"""
        passwords = ['Pass1!Aa', 'Pass2!Bb', 'Pass3!Cc']
        hashes = hash_password_batch(passwords)

        assert len(hashes) == 3
        assert all(isinstance(h, str) for h in hashes)
        assert all(h.startswith('$2b$12$') for h in hashes)

        # Verify all passwords work
        for password, hash_val in zip(passwords, hashes):
            assert verify_password(password, hash_val) is True

    def test_hash_password_batch_empty(self):
        """Test batch hashing with empty list"""
        hashes = hash_password_batch([])

        assert len(hashes) == 0


class TestPasswordRehash:
    """Tests for password rehash detection"""

    def test_needs_rehash_current_cost(self):
        """Test that current cost factor doesn't need rehash"""
        password = 'MyP@ssw0rd123'
        hashed = hash_password(password)  # Uses cost factor 12

        # Should not need rehash
        assert needs_rehash(hashed) is False

    def test_needs_rehash_lower_cost(self):
        """Test that lower cost factor needs rehash"""
        import bcrypt

        # Create hash with cost factor 10 (lower than configured 12)
        password = 'MyP@ssw0rd123'
        salt = bcrypt.gensalt(rounds=10)
        hashed = bcrypt.hashpw(password.encode(), salt).decode()

        # Should need rehash
        assert needs_rehash(hashed) is True

    def test_needs_rehash_invalid_hash(self):
        """Test invalid hash format"""
        # Should return True (needs rehash) for safety
        assert needs_rehash('invalid-hash-format') is True


class TestPasswordSecurity:
    """Security tests for password hashing"""

    def test_constant_time_verification(self):
        """Test that verification takes similar time regardless of match

        Note: This is a simplified test. Bcrypt handles constant-time internally.
        """
        password = 'MyP@ssw0rd123'
        hashed = hash_password(password)

        import time

        # Time correct password
        start = time.time()
        verify_password(password, hashed)
        time_correct = time.time() - start

        # Time incorrect password
        start = time.time()
        verify_password('WrongPassword', hashed)
        time_incorrect = time.time() - start

        # Both should take ~250ms (within reasonable variance)
        # Allow 50% variance for testing environment differences
        assert abs(time_correct - time_incorrect) < 0.5

    def test_salt_randomness(self):
        """Test that salts are random (different hashes for same password)"""
        password = 'MyP@ssw0rd123'
        hashes = [hash_password(password) for _ in range(10)]

        # All hashes should be unique
        assert len(set(hashes)) == 10

    def test_hash_contains_no_password_data(self):
        """Test that hash doesn't contain original password"""
        password = 'MyP@ssw0rd123'
        hashed = hash_password(password)

        # Hash should not contain password substring
        assert password not in hashed
        assert password.lower() not in hashed.lower()


class TestPasswordEdgeCases:
    """Edge case tests for password handling"""

    def test_very_long_password(self):
        """Test hashing very long password"""
        # Bcrypt has max 72-byte limit
        long_password = 'A' * 100 + 'b1!'

        # Should succeed
        hashed = hash_password(long_password)
        assert verify_password(long_password, hashed) is True

    def test_unicode_password(self):
        """Test password with Unicode characters"""
        password = 'MyP@ss™ørd123'

        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_password_with_spaces(self):
        """Test password with spaces"""
        password = 'My P@ssw0rd 123'

        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_password_all_special_chars(self):
        """Test password with all special characters"""
        password = '!@#$%^&*()_+-=[]{}|;:,.<>?'

        # Should fail strength check (no letters or digits)
        is_strong, _ = check_password_strength(password)
        assert is_strong is False

        # But hashing should still work
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

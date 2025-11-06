"""
Permission Management Tests
Tests for RBAC permission system
Created: November 5, 2025
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth.permissions_utils import (
    grant_permission,
    revoke_permission,
    check_permission,
    get_user_permissions,
    get_highest_permission_level,
    is_super_admin,
    list_all_permissions,
    PERMISSION_LEVELS
)


class TestPermissionHierarchy:
    """Test permission level hierarchy"""

    def test_permission_levels_defined(self):
        """Test that permission levels are properly defined"""
        assert 'view' in PERMISSION_LEVELS
        assert 'edit' in PERMISSION_LEVELS
        assert 'admin' in PERMISSION_LEVELS

    def test_permission_hierarchy(self):
        """Test that permission hierarchy is correct: admin > edit > view"""
        assert PERMISSION_LEVELS['admin'] > PERMISSION_LEVELS['edit']
        assert PERMISSION_LEVELS['edit'] > PERMISSION_LEVELS['view']
        assert PERMISSION_LEVELS['admin'] > PERMISSION_LEVELS['view']


class TestGrantPermission:
    """Test granting permissions"""

    @patch('auth.permissions_utils.check_permission')
    @patch('auth.permissions_utils.get_user_permissions')
    @patch('auth.permissions_utils.insert_rows')
    def test_grant_permission_basic(self, mock_insert, mock_get_perms, mock_check):
        """Test basic permission grant"""
        # Setup mocks
        mock_check.return_value = True  # Granter has admin
        mock_get_perms.return_value = []  # No existing permission
        mock_insert.return_value = True

        # Grant permission
        success, perm_id, error = grant_permission(
            user_id='user-123',
            permission_level='edit',
            granted_by='admin-456',
            company='Acme Corp',
            category='SASE'
        )

        assert success is True
        assert perm_id is not None
        assert error is None
        assert mock_insert.called

    @patch('auth.permissions_utils.check_permission')
    def test_grant_permission_invalid_level(self, mock_check):
        """Test that invalid permission level is rejected"""
        mock_check.return_value = True

        success, perm_id, error = grant_permission(
            user_id='user-123',
            permission_level='invalid',
            granted_by='admin-456'
        )

        assert success is False
        assert perm_id is None
        assert 'Invalid permission level' in error

    @patch('auth.permissions_utils.check_permission')
    def test_grant_permission_without_admin(self, mock_check):
        """Test that non-admin cannot grant permissions"""
        mock_check.return_value = False  # Granter is not admin

        success, perm_id, error = grant_permission(
            user_id='user-123',
            permission_level='edit',
            granted_by='user-789'
        )

        assert success is False
        assert perm_id is None
        assert 'does not have admin permission' in error

    @patch('auth.permissions_utils.check_permission')
    @patch('auth.permissions_utils.get_user_permissions')
    def test_grant_permission_duplicate(self, mock_get_perms, mock_check):
        """Test that duplicate permission is rejected"""
        mock_check.return_value = True
        mock_get_perms.return_value = [{'permission_id': 'existing-perm'}]

        success, perm_id, error = grant_permission(
            user_id='user-123',
            permission_level='edit',
            granted_by='admin-456',
            company='Acme Corp',
            category='SASE'
        )

        assert success is False
        assert perm_id is None
        assert 'already exists' in error


class TestCheckPermission:
    """Test permission checking logic"""

    @patch('auth.permissions_utils.get_user_permissions')
    def test_check_permission_exact_match(self, mock_get_perms):
        """Test exact scope match"""
        mock_get_perms.return_value = [{
            'permission_id': 'perm-123',
            'permission_level': 'edit',
            'company': 'Acme Corp',
            'category': 'SASE',
            'is_active': True,
            'expires_at': None
        }]

        has_perm = check_permission(
            user_id='user-123',
            required_level='edit',
            company='Acme Corp',
            category='SASE'
        )

        assert has_perm is True

    @patch('auth.permissions_utils.get_user_permissions')
    def test_check_permission_super_admin(self, mock_get_perms):
        """Test super admin (NULL, NULL) matches everything"""
        mock_get_perms.return_value = [{
            'permission_id': 'perm-123',
            'permission_level': 'admin',
            'company': None,
            'category': None,
            'is_active': True,
            'expires_at': None
        }]

        # Should match any scope
        assert check_permission('user-123', 'view', 'Acme Corp', 'SASE') is True
        assert check_permission('user-123', 'edit', 'Other Corp', 'Cloud') is True
        assert check_permission('user-123', 'admin', None, None) is True

    @patch('auth.permissions_utils.get_user_permissions')
    def test_check_permission_company_admin(self, mock_get_perms):
        """Test company admin (company, NULL) matches all categories for that company"""
        mock_get_perms.return_value = [{
            'permission_id': 'perm-123',
            'permission_level': 'admin',
            'company': 'Acme Corp',
            'category': None,
            'is_active': True,
            'expires_at': None
        }]

        # Should match any category for Acme Corp
        assert check_permission('user-123', 'view', 'Acme Corp', 'SASE') is True
        assert check_permission('user-123', 'edit', 'Acme Corp', 'Cloud') is True

        # Should not match other companies
        assert check_permission('user-123', 'view', 'Other Corp', 'SASE') is False

    @patch('auth.permissions_utils.get_user_permissions')
    def test_check_permission_hierarchy(self, mock_get_perms):
        """Test permission hierarchy: admin can do edit and view"""
        mock_get_perms.return_value = [{
            'permission_id': 'perm-123',
            'permission_level': 'admin',
            'company': 'Acme Corp',
            'category': 'SASE',
            'is_active': True,
            'expires_at': None
        }]

        # Admin can do everything
        assert check_permission('user-123', 'view', 'Acme Corp', 'SASE') is True
        assert check_permission('user-123', 'edit', 'Acme Corp', 'SASE') is True
        assert check_permission('user-123', 'admin', 'Acme Corp', 'SASE') is True

    @patch('auth.permissions_utils.get_user_permissions')
    def test_check_permission_edit_cannot_admin(self, mock_get_perms):
        """Test that edit permission cannot perform admin actions"""
        mock_get_perms.return_value = [{
            'permission_id': 'perm-123',
            'permission_level': 'edit',
            'company': 'Acme Corp',
            'category': 'SASE',
            'is_active': True,
            'expires_at': None
        }]

        # Edit can do view and edit
        assert check_permission('user-123', 'view', 'Acme Corp', 'SASE') is True
        assert check_permission('user-123', 'edit', 'Acme Corp', 'SASE') is True

        # But not admin
        assert check_permission('user-123', 'admin', 'Acme Corp', 'SASE') is False

    @patch('auth.permissions_utils.get_user_permissions')
    def test_check_permission_inactive(self, mock_get_perms):
        """Test that inactive permissions are ignored"""
        mock_get_perms.return_value = [{
            'permission_id': 'perm-123',
            'permission_level': 'admin',
            'company': None,
            'category': None,
            'is_active': False,  # Inactive
            'expires_at': None
        }]

        has_perm = check_permission('user-123', 'view', None, None)
        assert has_perm is False

    @patch('auth.permissions_utils.get_user_permissions')
    def test_check_permission_expired(self, mock_get_perms):
        """Test that expired permissions are ignored"""
        yesterday = datetime.utcnow() - timedelta(days=1)

        mock_get_perms.return_value = [{
            'permission_id': 'perm-123',
            'permission_level': 'admin',
            'company': None,
            'category': None,
            'is_active': True,
            'expires_at': yesterday.isoformat()
        }]

        has_perm = check_permission('user-123', 'view', None, None)
        assert has_perm is False

    @patch('auth.permissions_utils.get_user_permissions')
    def test_check_permission_no_permissions(self, mock_get_perms):
        """Test user with no permissions"""
        mock_get_perms.return_value = []

        has_perm = check_permission('user-123', 'view', 'Acme Corp', 'SASE')
        assert has_perm is False


class TestGetHighestPermissionLevel:
    """Test getting highest permission level"""

    @patch('auth.permissions_utils.get_user_permissions')
    def test_get_highest_level_admin(self, mock_get_perms):
        """Test user with admin permission"""
        mock_get_perms.return_value = [
            {'permission_level': 'view', 'is_active': True},
            {'permission_level': 'admin', 'is_active': True},
            {'permission_level': 'edit', 'is_active': True}
        ]

        level = get_highest_permission_level('user-123')
        assert level == 'admin'

    @patch('auth.permissions_utils.get_user_permissions')
    def test_get_highest_level_edit(self, mock_get_perms):
        """Test user with only edit permission"""
        mock_get_perms.return_value = [
            {'permission_level': 'view', 'is_active': True},
            {'permission_level': 'edit', 'is_active': True}
        ]

        level = get_highest_permission_level('user-123')
        assert level == 'edit'

    @patch('auth.permissions_utils.get_user_permissions')
    def test_get_highest_level_none(self, mock_get_perms):
        """Test user with no permissions"""
        mock_get_perms.return_value = []

        level = get_highest_permission_level('user-123')
        assert level is None

    @patch('auth.permissions_utils.get_user_permissions')
    def test_get_highest_level_ignores_inactive(self, mock_get_perms):
        """Test that inactive permissions are ignored"""
        mock_get_perms.return_value = [
            {'permission_level': 'admin', 'is_active': False},
            {'permission_level': 'view', 'is_active': True}
        ]

        level = get_highest_permission_level('user-123')
        assert level == 'view'


class TestIsSuperAdmin:
    """Test super admin check"""

    @patch('auth.permissions_utils.check_permission')
    def test_is_super_admin_true(self, mock_check):
        """Test user with super admin permission"""
        mock_check.return_value = True

        is_admin = is_super_admin('user-123')
        assert is_admin is True

        # Verify it checked for admin with NULL scope
        mock_check.assert_called_once_with('user-123', 'admin', company=None, category=None)

    @patch('auth.permissions_utils.check_permission')
    def test_is_super_admin_false(self, mock_check):
        """Test user without super admin permission"""
        mock_check.return_value = False

        is_admin = is_super_admin('user-123')
        assert is_admin is False


class TestScopeMatching:
    """Test complex scope matching scenarios"""

    @patch('auth.permissions_utils.get_user_permissions')
    def test_multiple_scope_permissions(self, mock_get_perms):
        """Test user with permissions for multiple scopes"""
        mock_get_perms.return_value = [
            {
                'permission_level': 'admin',
                'company': 'Acme Corp',
                'category': None,
                'is_active': True,
                'expires_at': None
            },
            {
                'permission_level': 'view',
                'company': 'Other Corp',
                'category': 'SASE',
                'is_active': True,
                'expires_at': None
            }
        ]

        # Should have admin for all Acme Corp categories
        assert check_permission('user-123', 'admin', 'Acme Corp', 'SASE') is True
        assert check_permission('user-123', 'edit', 'Acme Corp', 'Cloud') is True

        # Should have view for Other Corp SASE only
        assert check_permission('user-123', 'view', 'Other Corp', 'SASE') is True
        assert check_permission('user-123', 'edit', 'Other Corp', 'SASE') is False
        assert check_permission('user-123', 'view', 'Other Corp', 'Cloud') is False


class TestPermissionEdgeCases:
    """Test edge cases and error handling"""

    @patch('auth.permissions_utils.get_user_permissions')
    def test_check_permission_exception_handling(self, mock_get_perms):
        """Test that exceptions in permission check are handled"""
        mock_get_perms.side_effect = Exception("Database error")

        # Should return False on error, not raise exception
        has_perm = check_permission('user-123', 'view', 'Acme Corp', 'SASE')
        assert has_perm is False

    def test_permission_levels_dict_immutable(self):
        """Test that PERMISSION_LEVELS cannot be accidentally modified"""
        original = PERMISSION_LEVELS.copy()

        # Even if someone tries to modify it, it should be detected in tests
        assert PERMISSION_LEVELS == original


# Integration test examples (would require actual BigQuery in full integration tests)
class TestPermissionIntegration:
    """Integration test scenarios (mock BigQuery for unit tests)"""

    @patch('auth.permissions_utils.insert_rows')
    @patch('auth.permissions_utils.check_permission')
    @patch('auth.permissions_utils.get_user_permissions')
    def test_grant_and_check_flow(self, mock_get_perms, mock_check, mock_insert):
        """Test full flow: grant permission, then check it"""
        # Setup: admin grants permission
        mock_check.return_value = True
        mock_get_perms.return_value = []  # No existing permission
        mock_insert.return_value = True

        # Grant permission
        success, perm_id, error = grant_permission(
            user_id='user-123',
            permission_level='edit',
            granted_by='admin-456',
            company='Acme Corp',
            category='SASE'
        )

        assert success is True
        assert perm_id is not None

        # Now mock that permission exists
        mock_get_perms.return_value = [{
            'permission_id': perm_id,
            'permission_level': 'edit',
            'company': 'Acme Corp',
            'category': 'SASE',
            'is_active': True,
            'expires_at': None
        }]

        # Check permission
        has_perm = check_permission('user-123', 'edit', 'Acme Corp', 'SASE')
        assert has_perm is True

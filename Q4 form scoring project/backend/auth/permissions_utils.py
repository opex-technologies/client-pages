"""
Permission Management Utilities
Implements Role-Based Access Control (RBAC) for the Form Builder System
Created: November 5, 2025

Permission Model:
- Levels: admin > edit > view (hierarchical)
- Scopes: company + category (NULL = all)
- Temporal: expires_at, is_active
- Audit trail: granted_by, granted_at, revoked_by, revoked_at
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from common.config import config
    from common.logger import get_logger
    from common.bigquery_client import get_bigquery_client, execute_query, insert_rows
except ImportError:
    from config_standalone import config
    from logger_standalone import get_logger
    from bigquery_client_standalone import get_bigquery_client, execute_query, insert_rows

from google.cloud import bigquery

logger = get_logger('auth.permissions')

# Permission level hierarchy (higher number = more permissions)
PERMISSION_LEVELS = {
    'view': 1,
    'edit': 2,
    'admin': 3
}


def grant_permission(
    user_id: str,
    permission_level: str,
    granted_by: str,
    company: Optional[str] = None,
    category: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    notes: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Grant a permission to a user

    Args:
        user_id: User to grant permission to
        permission_level: 'view', 'edit', or 'admin'
        granted_by: User ID of admin granting the permission
        company: Specific company scope (NULL = all companies)
        category: Specific category scope (NULL = all categories)
        expires_at: Optional expiration datetime
        notes: Optional admin notes

    Returns:
        Tuple[bool, Optional[str], Optional[str]]: (success, permission_id, error_message)

    Usage:
        success, perm_id, error = grant_permission(
            user_id='user-123',
            permission_level='edit',
            granted_by='admin-456',
            company='Acme Corp',
            category='SASE'
        )
    """
    try:
        # Validate permission level
        if permission_level not in PERMISSION_LEVELS:
            return False, None, f"Invalid permission level: {permission_level}"

        # Verify granting user has admin permission
        granter_has_admin = check_permission(granted_by, 'admin', company, category)
        if not granter_has_admin:
            return False, None, "Granting user does not have admin permission for this scope"

        # Check if permission already exists
        existing = get_user_permissions(user_id, company, category, permission_level)
        if existing:
            return False, None, "Permission already exists for this scope"

        # Create permission record
        permission_id = str(uuid.uuid4())
        now = datetime.utcnow()

        permission_data = {
            'permission_id': permission_id,
            'user_id': user_id,
            'company': company,
            'category': category,
            'permission_level': permission_level,
            'granted_by': granted_by,
            'granted_at': now.isoformat(),
            'expires_at': expires_at.isoformat() if expires_at else None,
            'is_active': True,
            'revoked_by': None,
            'revoked_at': None,
            'notes': notes
        }

        # Insert into BigQuery
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'permission_groups')
        insert_rows(table_ref, [permission_data])

        logger.info(
            'Permission granted',
            permission_id=permission_id,
            user_id=user_id,
            level=permission_level,
            company=company,
            category=category,
            granted_by=granted_by
        )

        return True, permission_id, None

    except Exception as e:
        logger.exception('Failed to grant permission', error=str(e))
        return False, None, str(e)


def revoke_permission(
    permission_id: str,
    revoked_by: str,
    notes: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Revoke a permission

    Args:
        permission_id: ID of permission to revoke
        revoked_by: User ID of admin revoking the permission
        notes: Optional notes about why permission was revoked

    Returns:
        Tuple[bool, Optional[str]]: (success, error_message)

    Usage:
        success, error = revoke_permission(
            permission_id='perm-123',
            revoked_by='admin-456',
            notes='User left company'
        )
    """
    try:
        # Note: BigQuery UPDATE operations may fail on recently inserted rows
        # due to streaming buffer limitation. This is acceptable for permissions
        # as they are typically set during setup, not in real-time.

        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'permission_groups')
        now = datetime.utcnow()

        update_query = f"""
        UPDATE `{table_ref}`
        SET
            is_active = FALSE,
            revoked_by = @revoked_by,
            revoked_at = @revoked_at,
            notes = COALESCE(@notes, notes)
        WHERE permission_id = @permission_id
        """

        client = get_bigquery_client()
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("revoked_by", "STRING", revoked_by),
                bigquery.ScalarQueryParameter("revoked_at", "TIMESTAMP", now.isoformat()),
                bigquery.ScalarQueryParameter("notes", "STRING", notes),
                bigquery.ScalarQueryParameter("permission_id", "STRING", permission_id)
            ]
        )

        query_job = client.query(update_query, job_config=job_config)
        result = query_job.result()

        rows_affected = query_job.num_dml_affected_rows

        if rows_affected == 0:
            return False, "Permission not found or already revoked"

        logger.info(
            'Permission revoked',
            permission_id=permission_id,
            revoked_by=revoked_by
        )

        return True, None

    except Exception as e:
        logger.exception('Failed to revoke permission', error=str(e))
        return False, str(e)


def check_permission(
    user_id: str,
    required_level: str,
    company: Optional[str] = None,
    category: Optional[str] = None
) -> bool:
    """
    Check if user has required permission level for given scope

    Permission hierarchy: admin > edit > view
    - If user has 'admin', they can do everything
    - If user has 'edit', they can view and edit
    - If user has 'view', they can only view

    Scope matching:
    - company=NULL, category=NULL: Super admin (access to all)
    - company='X', category=NULL: Access to all categories for company X
    - company='X', category='Y': Access only to category Y for company X

    Args:
        user_id: User to check
        required_level: Minimum permission level required ('view', 'edit', 'admin')
        company: Company scope to check (None = any company)
        category: Category scope to check (None = any category)

    Returns:
        bool: True if user has permission, False otherwise

    Usage:
        # Check if user can edit SASE data for Acme Corp
        if check_permission('user-123', 'edit', 'Acme Corp', 'SASE'):
            # Allow edit operation
            pass
    """
    try:
        permissions = get_user_permissions(user_id)

        if not permissions:
            return False

        required_level_value = PERMISSION_LEVELS.get(required_level, 0)

        for perm in permissions:
            # Check if permission is active and not expired
            if not perm.get('is_active', False):
                continue

            if perm.get('expires_at'):
                expires_at = perm['expires_at']
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if expires_at < datetime.utcnow():
                    continue

            # Check permission level
            perm_level = perm.get('permission_level', 'view')
            perm_level_value = PERMISSION_LEVELS.get(perm_level, 0)

            if perm_level_value < required_level_value:
                continue

            # Check scope matching
            perm_company = perm.get('company')
            perm_category = perm.get('category')

            # Super admin (NULL, NULL) matches everything
            if perm_company is None and perm_category is None:
                return True

            # Company admin (company, NULL) matches all categories for that company
            if perm_company is not None and perm_category is None:
                if company is None or perm_company == company:
                    return True

            # Specific permission (company, category)
            if perm_company is not None and perm_category is not None:
                if (company is None or perm_company == company) and \
                   (category is None or perm_category == category):
                    return True

        return False

    except Exception as e:
        logger.exception('Error checking permission', error=str(e), user_id=user_id)
        return False


def get_user_permissions(
    user_id: str,
    company: Optional[str] = None,
    category: Optional[str] = None,
    permission_level: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get all permissions for a user

    Args:
        user_id: User to get permissions for
        company: Optional filter by company
        category: Optional filter by category
        permission_level: Optional filter by permission level

    Returns:
        List[Dict[str, Any]]: List of permission records

    Usage:
        # Get all permissions
        perms = get_user_permissions('user-123')

        # Get admin permissions for Acme Corp
        perms = get_user_permissions('user-123', company='Acme Corp', permission_level='admin')
    """
    try:
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'permission_groups')

        where_clauses = ["user_id = @user_id"]
        params = [bigquery.ScalarQueryParameter("user_id", "STRING", user_id)]

        if company is not None:
            where_clauses.append("(company = @company OR company IS NULL)")
            params.append(bigquery.ScalarQueryParameter("company", "STRING", company))

        if category is not None:
            where_clauses.append("(category = @category OR category IS NULL)")
            params.append(bigquery.ScalarQueryParameter("category", "STRING", category))

        if permission_level is not None:
            where_clauses.append("permission_level = @permission_level")
            params.append(bigquery.ScalarQueryParameter("permission_level", "STRING", permission_level))

        where_clause = " AND ".join(where_clauses)

        query = f"""
        SELECT
            permission_id,
            user_id,
            company,
            category,
            permission_level,
            granted_by,
            granted_at,
            expires_at,
            is_active,
            revoked_by,
            revoked_at,
            notes
        FROM `{table_ref}`
        WHERE {where_clause}
        ORDER BY granted_at DESC
        """

        results = execute_query(query, params=params)
        return results

    except Exception as e:
        logger.exception('Failed to get user permissions', error=str(e), user_id=user_id)
        return []


def get_highest_permission_level(user_id: str) -> Optional[str]:
    """
    Get user's highest permission level across all scopes

    Args:
        user_id: User to check

    Returns:
        Optional[str]: Highest permission level ('admin', 'edit', 'view') or None

    Usage:
        level = get_highest_permission_level('user-123')
        if level == 'admin':
            # User is admin somewhere
            pass
    """
    try:
        permissions = get_user_permissions(user_id)

        if not permissions:
            return None

        highest_value = 0
        highest_level = None

        for perm in permissions:
            if not perm.get('is_active', False):
                continue

            level = perm.get('permission_level', 'view')
            level_value = PERMISSION_LEVELS.get(level, 0)

            if level_value > highest_value:
                highest_value = level_value
                highest_level = level

        return highest_level

    except Exception as e:
        logger.exception('Error getting highest permission', error=str(e), user_id=user_id)
        return None


def is_super_admin(user_id: str) -> bool:
    """
    Check if user is a super admin (admin permission with NULL company and category)

    Args:
        user_id: User to check

    Returns:
        bool: True if user is super admin

    Usage:
        if is_super_admin('user-123'):
            # Allow access to everything
            pass
    """
    return check_permission(user_id, 'admin', company=None, category=None)


def list_all_permissions(
    company: Optional[str] = None,
    category: Optional[str] = None,
    permission_level: Optional[str] = None,
    active_only: bool = True
) -> List[Dict[str, Any]]:
    """
    List all permissions in the system (admin function)

    Args:
        company: Optional filter by company
        category: Optional filter by category
        permission_level: Optional filter by level
        active_only: Only return active permissions

    Returns:
        List[Dict[str, Any]]: List of all permissions

    Usage:
        # List all active admin permissions
        admins = list_all_permissions(permission_level='admin', active_only=True)
    """
    try:
        table_ref = config.get_dataset_table(config.AUTH_DATASET, 'permission_groups')

        where_clauses = []
        params = []

        if active_only:
            where_clauses.append("is_active = TRUE")

        if company is not None:
            where_clauses.append("company = @company")
            params.append(bigquery.ScalarQueryParameter("company", "STRING", company))

        if category is not None:
            where_clauses.append("category = @category")
            params.append(bigquery.ScalarQueryParameter("category", "STRING", category))

        if permission_level is not None:
            where_clauses.append("permission_level = @permission_level")
            params.append(bigquery.ScalarQueryParameter("permission_level", "STRING", permission_level))

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"""
        SELECT
            p.permission_id,
            p.user_id,
            u.email,
            u.full_name,
            p.company,
            p.category,
            p.permission_level,
            p.granted_by,
            p.granted_at,
            p.expires_at,
            p.is_active,
            p.revoked_by,
            p.revoked_at,
            p.notes
        FROM `{table_ref}` p
        LEFT JOIN `{config.get_dataset_table(config.AUTH_DATASET, 'users')}` u
            ON p.user_id = u.user_id
        WHERE {where_clause}
        ORDER BY p.granted_at DESC
        """

        results = execute_query(query, params=params if params else None)
        return results

    except Exception as e:
        logger.exception('Failed to list permissions', error=str(e))
        return []

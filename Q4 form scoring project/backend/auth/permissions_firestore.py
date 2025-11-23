"""
Firestore-based Permissions Utilities
Handles permission checking and management in Firestore
Created: November 16, 2025
"""

from google.cloud import firestore
from typing import List, Dict, Any, Optional
from datetime import datetime
import os


def get_firestore_client():
    """Get Firestore client instance"""
    project_id = os.environ.get('GCP_PROJECT', 'opex-data-lake-k23k4y98m')
    return firestore.Client(project=project_id)


def check_permission(user_id: str, required_level: str, company: str = None, category: str = None) -> bool:
    """
    Check if user has required permission level

    Args:
        user_id: User ID to check
        required_level: Required permission level ('view', 'edit', 'admin')
        company: Optional company scope
        category: Optional category scope

    Returns:
        bool: True if user has permission, False otherwise
    """
    db = get_firestore_client()

    # Query active permissions for user
    query = db.collection('permissions').where('user_id', '==', user_id).where('is_active', '==', True)
    permissions = list(query.stream())

    if not permissions:
        return False

    # Permission hierarchy: admin > edit > view
    level_hierarchy = {'view': 1, 'edit': 2, 'admin': 3}
    required_level_value = level_hierarchy.get(required_level, 0)

    for perm_doc in permissions:
        perm = perm_doc.to_dict()

        # Check if permission level is sufficient
        perm_level = perm.get('permission_level', '')
        perm_level_value = level_hierarchy.get(perm_level, 0)

        if perm_level_value < required_level_value:
            continue

        # Check scope
        perm_company = perm.get('company_id')
        perm_category = perm.get('category')

        # NULL scope = all access
        if perm_company is None and perm_category is None:
            return True

        # Check company match
        if company and perm_company and perm_company != company:
            continue

        # Check category match
        if category and perm_category and perm_category != category:
            continue

        return True

    return False


def get_user_permissions(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all active permissions for a user

    Args:
        user_id: User ID

    Returns:
        List of permission dictionaries
    """
    db = get_firestore_client()

    query = db.collection('permissions').where('user_id', '==', user_id).where('is_active', '==', True)
    permissions = []

    for doc in query.stream():
        perm = doc.to_dict()
        perm['permission_id'] = doc.id
        permissions.append(perm)

    return permissions


def is_super_admin(user_id: str) -> bool:
    """
    Check if user is a super admin (admin permission with NULL scope)

    Args:
        user_id: User ID

    Returns:
        bool: True if user is super admin
    """
    db = get_firestore_client()

    query = db.collection('permissions') \
        .where('user_id', '==', user_id) \
        .where('is_active', '==', True) \
        .where('permission_level', '==', 'admin')

    for doc in query.stream():
        perm = doc.to_dict()
        # Super admin has NULL company_id and category
        if perm.get('company_id') is None and perm.get('category') is None:
            return True

    return False


def get_highest_permission_level(user_id: str) -> Optional[str]:
    """
    Get user's highest permission level across all scopes

    Args:
        user_id: User ID

    Returns:
        Optional[str]: Highest permission level ('admin', 'edit', 'view') or None
    """
    permissions = get_user_permissions(user_id)

    if not permissions:
        return None

    level_hierarchy = {'view': 1, 'edit': 2, 'admin': 3}
    highest_value = 0
    highest_level = None

    for perm in permissions:
        level = perm.get('permission_level', 'view')
        level_value = level_hierarchy.get(level, 0)

        if level_value > highest_value:
            highest_value = level_value
            highest_level = level

    return highest_level

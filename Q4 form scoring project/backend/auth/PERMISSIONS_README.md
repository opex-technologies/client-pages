# Role-Based Access Control (RBAC) System

**Created**: November 5, 2025
**Status**: ✅ Implemented
**Version**: 1.0.0

## Overview

The Form Builder & Response Scoring System implements a flexible Role-Based Access Control (RBAC) system with hierarchical permissions and scope-based access control.

## Table of Contents

1. [Permission Model](#permission-model)
2. [Quick Start](#quick-start)
3. [Permission Levels](#permission-levels)
4. [Scope System](#scope-system)
5. [API Endpoints](#api-endpoints)
6. [Using Middleware](#using-middleware)
7. [Code Examples](#code-examples)
8. [Security Best Practices](#security-best-practices)

---

## Permission Model

### Core Concepts

**Permission Levels** (Hierarchical):
- `admin` - Full access (can grant/revoke permissions, manage data)
- `edit` - Can create, read, update, delete data
- `view` - Read-only access

**Scope Dimensions**:
- **Company** - Specific company or NULL for all companies
- **Category** - Specific category or NULL for all categories

**Temporal Controls**:
- `expires_at` - Optional expiration timestamp
- `is_active` - Enable/disable without deletion
- `granted_at` - When permission was granted
- `revoked_at` - When permission was revoked

**Audit Trail**:
- `granted_by` - Admin who granted the permission
- `revoked_by` - Admin who revoked the permission
- `notes` - Admin notes about the permission

---

## Quick Start

### Grant Permission

```python
from permissions_utils import grant_permission

# Grant edit permission for Acme Corp SASE category
success, perm_id, error = grant_permission(
    user_id='user-123',
    permission_level='edit',
    granted_by='admin-456',
    company='Acme Corp',
    category='SASE',
    notes='Q4 project access'
)

if success:
    print(f"Permission granted: {perm_id}")
else:
    print(f"Failed: {error}")
```

### Check Permission

```python
from permissions_utils import check_permission

# Check if user can edit SASE data for Acme Corp
can_edit = check_permission(
    user_id='user-123',
    required_level='edit',
    company='Acme Corp',
    category='SASE'
)

if can_edit:
    # Allow operation
    pass
else:
    # Deny access
    pass
```

### Protect Endpoint

```python
from auth_middleware import require_permission

@require_permission('edit', company='Acme Corp', category='SASE')
def edit_sase_data(request, current_user):
    # Only users with edit permission for Acme/SASE can access
    return success_response(data={'message': 'Access granted'})
```

---

## Permission Levels

### Hierarchy

```
admin > edit > view
```

Users with higher permission can perform all actions of lower permissions.

### Level Details

#### `view` (Level 1)
- Read-only access
- Can view data within scope
- Cannot modify anything

**Use Cases**:
- Reporting users
- Auditors
- External consultants (read-only)

#### `edit` (Level 2)
- Can create, read, update, delete data
- Cannot grant permissions to others
- Cannot access admin functions

**Use Cases**:
- Regular team members
- Project contributors
- Data entry personnel

#### `admin` (Level 3)
- Full access to data
- Can grant and revoke permissions
- Can access all admin functions

**Use Cases**:
- Team leads
- Managers
- System administrators

---

## Scope System

### Scope Patterns

#### 1. Super Admin (NULL, NULL)

```python
# Grant super admin permission
grant_permission(
    user_id='admin-user',
    permission_level='admin',
    granted_by='existing-admin',
    company=None,  # All companies
    category=None  # All categories
)
```

**Access**: Everything in the system
**Use Case**: System administrators

#### 2. Company Admin (Company, NULL)

```python
# Grant company-wide admin
grant_permission(
    user_id='company-admin',
    permission_level='admin',
    granted_by='super-admin',
    company='Acme Corp',
    category=None  # All categories for Acme
)
```

**Access**: All categories for specified company
**Use Case**: Company account managers

#### 3. Category-Specific (Company, Category)

```python
# Grant category-specific permission
grant_permission(
    user_id='specialist-user',
    permission_level='edit',
    granted_by='company-admin',
    company='Acme Corp',
    category='SASE'
)
```

**Access**: Only specified category for specified company
**Use Case**: Specialists, consultants with limited scope

### Scope Matching Rules

When checking permissions, the system matches scopes using these rules:

1. **Super Admin Permission** (`NULL`, `NULL`) matches ANY requested scope
2. **Company Admin Permission** (`company`, `NULL`) matches:
   - Exact company match, ANY category
   - NULL company request (any company)
3. **Category-Specific Permission** (`company`, `category`) matches:
   - Exact company AND category match
   - NULL company/category requests

#### Examples

User has: `admin` permission for `(Acme Corp, NULL)`

```python
# These all return True:
check_permission('user', 'edit', 'Acme Corp', 'SASE')  # ✓ Company match
check_permission('user', 'view', 'Acme Corp', 'Cloud') # ✓ Company match
check_permission('user', 'admin', 'Acme Corp', None)   # ✓ Company match

# This returns False:
check_permission('user', 'edit', 'Other Corp', 'SASE') # ✗ Company mismatch
```

---

## API Endpoints

All endpoints require authentication via `Authorization: Bearer <token>` header.

### POST /permissions/grant

Grant permission to a user (requires admin permission).

**Request**:
```json
{
  "user_id": "user-123",
  "permission_level": "edit",
  "company": "Acme Corp",
  "category": "SASE",
  "expires_days": 365,
  "notes": "Q4 project access"
}
```

**Response** (201):
```json
{
  "success": true,
  "data": {
    "permission_id": "perm-abc-123",
    "user_id": "user-123",
    "permission_level": "edit",
    "company": "Acme Corp",
    "category": "SASE",
    "granted_by": "admin-456",
    "granted_at": "2025-11-05T12:00:00Z",
    "expires_at": "2026-11-05T12:00:00Z"
  },
  "message": "Permission granted successfully"
}
```

### POST /permissions/revoke

Revoke a permission (requires admin permission).

**Request**:
```json
{
  "permission_id": "perm-abc-123",
  "notes": "User left company"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Permission revoked successfully"
}
```

### GET /permissions/user/:user_id

Get all permissions for a user.

**Response** (200):
```json
{
  "success": true,
  "data": {
    "user_id": "user-123",
    "highest_level": "edit",
    "is_super_admin": false,
    "permissions": [
      {
        "permission_id": "perm-abc-123",
        "company": "Acme Corp",
        "category": "SASE",
        "permission_level": "edit",
        "granted_by": "admin-456",
        "granted_at": "2025-11-05T12:00:00Z",
        "expires_at": null,
        "is_active": true
      }
    ]
  }
}
```

### GET /permissions/list

List all permissions (requires super admin).

**Query Parameters**:
- `company` (optional) - Filter by company
- `category` (optional) - Filter by category
- `level` (optional) - Filter by permission level
- `active_only` (optional, default: true) - Only show active permissions

**Response** (200):
```json
{
  "success": true,
  "data": {
    "permissions": [...],
    "count": 42
  }
}
```

### POST /permissions/check

Check if user has a specific permission.

**Request**:
```json
{
  "user_id": "user-123",
  "required_level": "edit",
  "company": "Acme Corp",
  "category": "SASE"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "has_permission": true,
    "user_id": "user-123",
    "required_level": "edit",
    "company": "Acme Corp",
    "category": "SASE"
  }
}
```

---

## Using Middleware

### Basic Authentication

```python
from auth_middleware import require_auth

@require_auth
def my_endpoint(request, current_user):
    user_id = current_user['user_id']
    email = current_user['email']
    return success_response(data={'user_id': user_id})
```

### Permission-Based Protection

```python
from auth_middleware import require_permission

# Fixed scope
@require_permission('edit', company='Acme Corp', category='SASE')
def edit_sase_data(request, current_user):
    return success_response(data={'message': 'Can edit SASE data'})

# Dynamic scope from request
@require_permission('edit',
                   extract_company_from_request=True,
                   extract_category_from_request=True)
def edit_dynamic_data(request, current_user):
    # Permission checked against company/category from request params
    return success_response(data={'message': 'Access granted'})
```

### Super Admin Only

```python
from auth_middleware import require_super_admin

@require_super_admin
def admin_panel(request, current_user):
    return success_response(data={'message': 'Super admin access'})
```

### Optional Authentication

```python
from auth_middleware import optional_auth

@optional_auth
def public_with_user_context(request, current_user):
    if current_user:
        # Authenticated - customize response
        return success_response(data={'user_id': current_user['user_id']})
    else:
        # Anonymous - default response
        return success_response(data={'message': 'Hello, guest'})
```

---

## Code Examples

### Complete Workflow Example

```python
# 1. Initial Setup: Create super admin
grant_permission(
    user_id='founder-123',
    permission_level='admin',
    granted_by='system',  # Initial grant
    company=None,
    category=None
)

# 2. Super admin creates company admin
grant_permission(
    user_id='company-admin-456',
    permission_level='admin',
    granted_by='founder-123',
    company='Acme Corp',
    category=None
)

# 3. Company admin creates team member
grant_permission(
    user_id='team-member-789',
    permission_level='edit',
    granted_by='company-admin-456',
    company='Acme Corp',
    category='SASE',
    expires_days=365
)

# 4. Check team member's access
can_edit_sase = check_permission(
    'team-member-789',
    'edit',
    'Acme Corp',
    'SASE'
)  # Returns True

can_edit_cloud = check_permission(
    'team-member-789',
    'edit',
    'Acme Corp',
    'Cloud'
)  # Returns False (no permission for Cloud category)
```

### Temporary Access Example

```python
from datetime import datetime, timedelta

# Grant 90-day contractor access
expires_at = datetime.utcnow() + timedelta(days=90)

success, perm_id, error = grant_permission(
    user_id='contractor-999',
    permission_level='view',
    granted_by='admin-456',
    company='Acme Corp',
    category='SASE',
    expires_at=expires_at,
    notes='90-day contractor engagement'
)

# Permission automatically expires after 90 days
```

### Permission Audit Example

```python
# List all admin permissions
admins = list_all_permissions(
    permission_level='admin',
    active_only=True
)

# List permissions for specific company
acme_perms = list_all_permissions(
    company='Acme Corp',
    active_only=True
)

# Review and revoke if needed
for perm in acme_perms:
    if needs_review(perm):
        revoke_permission(
            permission_id=perm['permission_id'],
            revoked_by='admin-456',
            notes='Quarterly access review'
        )
```

---

## Security Best Practices

### 1. Principle of Least Privilege

Grant the minimum permission level needed:

```python
# ✓ Good: Grant only what's needed
grant_permission('user', 'view', 'admin', 'Acme', 'SASE')

# ✗ Bad: Over-permissioning
grant_permission('user', 'admin', 'admin', None, None)
```

### 2. Use Temporal Controls

Set expiration dates for temporary access:

```python
# ✓ Good: Time-limited contractor access
grant_permission('contractor', 'view', 'admin', 'Acme', 'SASE',
                expires_days=90)

# ✗ Bad: Permanent contractor access
grant_permission('contractor', 'view', 'admin', 'Acme', 'SASE')
```

### 3. Audit Trail

Always include notes for accountability:

```python
# ✓ Good: Document why permission was granted
grant_permission('user', 'edit', 'admin', 'Acme', 'SASE',
                notes='Q4 SASE modernization project')

# ✗ Bad: No documentation
grant_permission('user', 'edit', 'admin', 'Acme', 'SASE')
```

### 4. Regular Reviews

Implement periodic permission reviews:

```python
# Review all permissions quarterly
def quarterly_permission_review():
    all_perms = list_all_permissions(active_only=True)

    for perm in all_perms:
        # Check if permission is still needed
        if should_revoke(perm):
            revoke_permission(
                perm['permission_id'],
                'admin-system',
                notes='Quarterly review - no longer needed'
            )
```

### 5. Scope Restrictions

Use company/category scopes to limit access:

```python
# ✓ Good: Limit to specific scope
grant_permission('specialist', 'edit', 'admin', 'Acme', 'SASE')

# ✗ Bad: Overly broad scope
grant_permission('specialist', 'edit', 'admin', None, None)
```

### 6. Verify Granter Permissions

Always ensure granter has sufficient permissions:

```python
# The grant_permission function automatically checks this:
# - Granter must have 'admin' permission for the scope
# - Granter cannot grant permissions broader than their own
```

---

## Common Patterns

### Multi-Company User

User working with multiple companies:

```python
# Grant separate permissions for each company
grant_permission('consultant', 'view', 'admin', 'Company A', 'SASE')
grant_permission('consultant', 'view', 'admin', 'Company B', 'Cloud')

# User can view SASE for Company A and Cloud for Company B
```

### Team Lead Pattern

Team lead with admin for their team's category:

```python
# Team lead for SASE team at Acme
grant_permission('team-lead', 'admin', 'super-admin', 'Acme', 'SASE')

# Team lead can then grant permissions to team members
grant_permission('team-member', 'edit', 'team-lead', 'Acme', 'SASE')
```

### Read-Only Reporting User

Analyst with view-only access across all categories:

```python
# Company-wide view permission
grant_permission('analyst', 'view', 'admin', 'Acme', None)

# Analyst can view all data for Acme Corp, but cannot modify
```

---

## Troubleshooting

### Permission Not Working

1. **Check if permission is active**:
   ```python
   perms = get_user_permissions('user-123')
   for perm in perms:
       print(f"Active: {perm['is_active']}, Expires: {perm['expires_at']}")
   ```

2. **Check permission level**:
   ```python
   level = get_highest_permission_level('user-123')
   print(f"Highest level: {level}")
   ```

3. **Check scope matching**:
   ```python
   # Debug: Try with NULL scope
   has_any = check_permission('user-123', 'view', None, None)
   print(f"Has any permission: {has_any}")
   ```

### Cannot Grant Permission

**Error**: "Granting user does not have admin permission"

**Solution**: Verify granter has admin permission for the scope:
```python
granter_is_admin = check_permission('granter-id', 'admin', 'Acme', 'SASE')
```

### Permission Already Exists

**Error**: "Permission already exists for this scope"

**Solution**: Revoke existing permission first or check existing permissions:
```python
existing = get_user_permissions('user-123', 'Acme', 'SASE', 'edit')
if existing:
    print("User already has this permission")
```

---

## Testing

Run permission tests:

```bash
cd backend
pytest tests/test_permissions.py -v
```

Test coverage includes:
- Permission hierarchy
- Scope matching
- Expiration handling
- Super admin checks
- Edge cases

---

**Documentation Version**: 1.0.0
**Last Updated**: November 5, 2025
**Maintainer**: Dayta Analytics - Form Builder Team

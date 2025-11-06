# Admin User Setup Guide

**Created**: November 5, 2025
**Status**: Production Ready
**Version**: 1.0.0

## Overview

This guide explains how to create the initial super admin user for the Form Builder & Response Scoring System.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Method 1: Using create_admin.py Script](#method-1-using-create_adminpy-script)
3. [Method 2: Using BigQuery Console](#method-2-using-bigquery-console)
4. [Method 3: Using bq CLI](#method-3-using-bq-cli)
5. [Verifying Admin Creation](#verifying-admin-creation)
6. [Granting Additional Permissions](#granting-additional-permissions)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Access to GCP project `opex-data-lake-k23k4y98m`
- BigQuery write permissions
- Python 3.10+ (for script method)
- Required Python packages: `google-cloud-bigquery`, `bcrypt`, `pyjwt`, `python-dotenv`

---

## Method 1: Using create_admin.py Script

### Interactive Mode

```bash
cd backend/auth
python3 create_admin.py
```

Follow the prompts:
- **Email**: admin@opextech.com
- **Full Name**: System Administrator
- **Password**: (Strong password with uppercase, lowercase, digit, special char, 8+ chars)

### Command Line Mode

```bash
python3 create_admin.py \
  --email "admin@opextech.com" \
  --name "System Administrator" \
  --password "SecureP@ssw0rd123"
```

### Expected Output

```
Creating admin user: admin@opextech.com
✓ Admin user created: admin@opextech.com (ID: abc-123-def-456)
✓ Super admin permission granted (ID: perm-789-xyz)

⚠️  IMPORTANT: Wait 90 minutes before attempting to login due to BigQuery limitation
```

---

## Method 2: Using BigQuery Console

### Step 1: Hash the Password

You'll need to hash the password using bcrypt. Use this Python one-liner:

```bash
python3 -c "import bcrypt; pw=b'YOUR_PASSWORD_HERE'; print(bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12)).decode())"
```

**Example**:
```bash
python3 -c "import bcrypt; pw=b'Admin@Opex2025'; print(bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12)).decode())"
# Output: $2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
```

### Step 2: Insert User into BigQuery

Go to [BigQuery Console](https://console.cloud.google.com/bigquery) and run:

```sql
-- Replace with your values
DECLARE user_id STRING DEFAULT GENERATE_UUID();
DECLARE email STRING DEFAULT 'admin@opextech.com';
DECLARE password_hash STRING DEFAULT '$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';  -- From Step 1
DECLARE full_name STRING DEFAULT 'System Administrator';
DECLARE now TIMESTAMP DEFAULT CURRENT_TIMESTAMP();

-- Insert user
INSERT INTO `opex-data-lake-k23k4y98m.auth.users` (
  user_id,
  email,
  password_hash,
  full_name,
  mfa_secret,
  failed_login_attempts,
  account_locked_until,
  created_at,
  last_login,
  password_changed_at,
  status,
  created_by,
  updated_at,
  updated_by
) VALUES (
  user_id,
  email,
  password_hash,
  full_name,
  NULL,  -- mfa_secret
  0,     -- failed_login_attempts
  NULL,  -- account_locked_until
  now,   -- created_at
  NULL,  -- last_login
  now,   -- password_changed_at
  'active',  -- status
  user_id,   -- created_by (self)
  NULL,  -- updated_at
  NULL   -- updated_by
);

-- Output the user_id for next step
SELECT user_id, email, full_name
FROM `opex-data-lake-k23k4y98m.auth.users`
WHERE email = email
ORDER BY created_at DESC
LIMIT 1;
```

### Step 3: Grant Super Admin Permission

Using the `user_id` from Step 2:

```sql
-- Replace USER_ID_FROM_STEP_2 with actual UUID
DECLARE target_user_id STRING DEFAULT 'USER_ID_FROM_STEP_2';
DECLARE perm_id STRING DEFAULT GENERATE_UUID();
DECLARE now TIMESTAMP DEFAULT CURRENT_TIMESTAMP();

INSERT INTO `opex-data-lake-k23k4y98m.auth.permission_groups` (
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
) VALUES (
  perm_id,
  target_user_id,
  NULL,    -- company (NULL = all companies)
  NULL,    -- category (NULL = all categories)
  'admin', -- permission_level
  'system',  -- granted_by
  now,     -- granted_at
  NULL,    -- expires_at (never)
  TRUE,    -- is_active
  NULL,    -- revoked_by
  NULL,    -- revoked_at
  'Initial super admin - system bootstrap'  -- notes
);

-- Verify
SELECT *
FROM `opex-data-lake-k23k4y98m.auth.permission_groups`
WHERE user_id = target_user_id;
```

---

## Method 3: Using bq CLI

### Step 1: Create JSON Files

Create `user.json`:

```json
{
  "user_id": "GENERATE_A_UUID",
  "email": "admin@opextech.com",
  "password_hash": "$2b$12$YOUR_BCRYPT_HASH_HERE",
  "full_name": "System Administrator",
  "mfa_secret": null,
  "failed_login_attempts": 0,
  "account_locked_until": null,
  "created_at": "2025-11-05T12:00:00Z",
  "last_login": null,
  "password_changed_at": "2025-11-05T12:00:00Z",
  "status": "active",
  "created_by": "SAME_AS_USER_ID",
  "updated_at": null,
  "updated_by": null
}
```

Create `permission.json` (use user_id from user.json):

```json
{
  "permission_id": "GENERATE_A_UUID",
  "user_id": "SAME_AS_USER_JSON",
  "company": null,
  "category": null,
  "permission_level": "admin",
  "granted_by": "system",
  "granted_at": "2025-11-05T12:00:00Z",
  "expires_at": null,
  "is_active": true,
  "revoked_by": null,
  "revoked_at": null,
  "notes": "Initial super admin"
}
```

### Step 2: Insert via bq CLI

```bash
# Insert user
bq insert \
  opex-data-lake-k23k4y98m:auth.users \
  user.json

# Insert permission
bq insert \
  opex-data-lake-k23k4y98m:auth.permission_groups \
  permission.json
```

---

## Verifying Admin Creation

### Check User Exists

```sql
SELECT
  user_id,
  email,
  full_name,
  status,
  created_at
FROM `opex-data-lake-k23k4y98m.auth.users`
WHERE email = 'admin@opextech.com';
```

### Check Permission Granted

```sql
SELECT
  p.permission_id,
  p.user_id,
  u.email,
  p.company,
  p.category,
  p.permission_level,
  p.is_active,
  p.granted_at
FROM `opex-data-lake-k23k4y98m.auth.permission_groups` p
JOIN `opex-data-lake-k23k4y98m.auth.users` u ON p.user_id = u.user_id
WHERE u.email = 'admin@opextech.com'
  AND p.is_active = TRUE;
```

Expected output should show:
- **permission_level**: `admin`
- **company**: `NULL`
- **category**: `NULL`
- **is_active**: `TRUE`

---

## Granting Additional Permissions

Once you have one super admin, you can grant permissions to other users.

### Using the CLI Tool

```bash
# Grant super admin to another user
python3 grant_permission_cli.py \
  --user-id "user-abc-123" \
  --level admin

# Grant company admin
python3 grant_permission_cli.py \
  --user-id "user-def-456" \
  --level admin \
  --company "Acme Corp"

# Grant category-specific edit permission
python3 grant_permission_cli.py \
  --user-id "user-ghi-789" \
  --level edit \
  --company "Acme Corp" \
  --category "SASE" \
  --expires-days 365 \
  --notes "Q4 project access"
```

### Using the API

Once the system is running, you can use the permissions API:

```bash
# Get admin's access token first
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@opextech.com",
    "password": "YOUR_PASSWORD"
  }'

# Use the access token to grant permissions
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/permissions/grant \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "user_id": "user-to-grant",
    "permission_level": "edit",
    "company": "Acme Corp",
    "category": "SASE",
    "expires_days": 365,
    "notes": "Q4 project team member"
  }'
```

---

## Troubleshooting

### Issue: "Cannot login immediately after creation"

**Cause**: BigQuery streaming buffer limitation (90-minute delay for UPDATE operations)

**Solution**:
- Wait 90 minutes after user creation before attempting login
- OR migrate authentication to Firestore (see `BIGQUERY_LIMITATIONS.md`)

### Issue: "Password hash doesn't work"

**Verify**: Hash was generated with bcrypt rounds=12

```bash
# Check hash format
python3 -c "import bcrypt; hash=b'$2b$12$...'print('Valid' if hash.startswith(b'$2b$12$') else 'Invalid')"
```

**Solution**: Regenerate hash with correct parameters:

```python
import bcrypt
password = b'YOUR_PASSWORD'
hash = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
print(hash.decode())
```

### Issue: "User created but no permissions"

**Verify**: Check permission_groups table

```sql
SELECT COUNT(*) as perm_count
FROM `opex-data-lake-k23k4y98m.auth.permission_groups`
WHERE user_id = 'YOUR_USER_ID'
  AND is_active = TRUE;
```

**Solution**: Run Step 3 of BigQuery Console method to grant super admin permission

### Issue: "Permission denied when trying to grant"

**Verify**: Current user has admin permission

```sql
SELECT
  user_id,
  permission_level,
  company,
  category
FROM `opex-data-lake-k23k4y98m.auth.permission_groups`
WHERE user_id = 'YOUR_USER_ID'
  AND is_active = TRUE;
```

**Solution**:
- Ensure you have `admin` level permission
- Ensure scope is NULL/NULL for super admin, or matches the scope you're granting

### Issue: "ModuleNotFoundError: No module named 'bcrypt'"

**Solution**: Install dependencies

```bash
cd backend/auth
pip3 install -r requirements.txt

# Or install specific packages
pip3 install google-cloud-bigquery bcrypt pyjwt python-dotenv
```

---

## Security Best Practices

### 1. Strong Password Requirements

Ensure admin password meets requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

**Good**: `Admin@Opex2025`, `SecureP@ssw0rd!`, `MyStr0ng#Pass`
**Bad**: `admin`, `password123`, `Admin2025`

### 2. Change Default Password

After first login, immediately change the password via the API:

```bash
curl -X PUT https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "Admin@Opex2025",
    "new_password": "NewSecureP@ss2025"
  }'
```

### 3. Limit Super Admins

- Create only 1-2 super admin accounts
- Most users should have company or category-specific permissions
- Use principle of least privilege

### 4. Regular Audit

Regularly review admin permissions:

```sql
SELECT
  u.email,
  u.full_name,
  p.permission_level,
  p.company,
  p.category,
  p.granted_at,
  p.granted_by
FROM `opex-data-lake-k23k4y98m.auth.permission_groups` p
JOIN `opex-data-lake-k23k4y98m.auth.users` u ON p.user_id = u.user_id
WHERE p.permission_level = 'admin'
  AND p.is_active = TRUE
ORDER BY p.granted_at DESC;
```

### 5. Document Grants

Always include notes when granting permissions:

```bash
python3 grant_permission_cli.py \
  --user-id "user-123" \
  --level admin \
  --notes "CTO - full system access granted by CEO 2025-11-05"
```

---

## Quick Reference

### Create Super Admin (Fastest Method)

```sql
-- In BigQuery Console
DECLARE user_id STRING DEFAULT GENERATE_UUID();

-- Insert user (replace password_hash with actual hash)
INSERT INTO `opex-data-lake-k23k4y98m.auth.users` VALUES (
  user_id, 'admin@opextech.com', '$2b$12$HASH_HERE',
  'Admin', NULL, 0, NULL, CURRENT_TIMESTAMP(), NULL,
  CURRENT_TIMESTAMP(), 'active', user_id, NULL, NULL
);

-- Grant super admin
INSERT INTO `opex-data-lake-k23k4y98m.auth.permission_groups` VALUES (
  GENERATE_UUID(), user_id, NULL, NULL, 'admin', 'system',
  CURRENT_TIMESTAMP(), NULL, TRUE, NULL, NULL, 'Initial admin'
);
```

### Verify Admin

```sql
SELECT u.email, p.permission_level, p.company, p.category
FROM `opex-data-lake-k23k4y98m.auth.permission_groups` p
JOIN `opex-data-lake-k23k4y98m.auth.users` u ON p.user_id = u.user_id
WHERE u.email = 'admin@opextech.com'
  AND p.is_active = TRUE;
```

Should return:
- **permission_level**: `admin`
- **company**: `NULL`
- **category**: `NULL`

---

**Last Updated**: November 5, 2025
**Maintainer**: Dayta Analytics - Form Builder Team
**Support**: See `PERMISSIONS_README.md` for permission system details

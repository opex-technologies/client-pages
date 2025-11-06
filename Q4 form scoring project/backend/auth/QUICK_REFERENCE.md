# Authentication & Permissions - Quick Reference

**Version**: 1.0.0
**Last Updated**: November 5, 2025

---

## 🚀 Quick Start

### Register User
```bash
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ss123",
    "full_name": "John Doe"
  }'
```

### Login
```bash
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ss123"
  }'
```

### Use Token
```bash
curl -X GET https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 📋 API Endpoints

### Authentication Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Login and get tokens |
| POST | `/auth/refresh` | No | Refresh access token |
| POST | `/auth/logout` | Yes | Logout (revoke session) |
| POST | `/auth/verify` | No | Verify token validity |
| GET | `/auth/me` | Yes | Get current user info |

### Permission Endpoints

| Method | Endpoint | Auth Required | Permission | Description |
|--------|----------|---------------|------------|-------------|
| POST | `/permissions/grant` | Yes | Admin | Grant permission |
| POST | `/permissions/revoke` | Yes | Admin | Revoke permission |
| GET | `/permissions/user/:id` | Yes | Self/Admin | Get user permissions |
| GET | `/permissions/list` | Yes | Super Admin | List all permissions |
| POST | `/permissions/check` | Yes | Any | Check permission |

---

## 🔐 Permission Levels

| Level | Code | Can Do |
|-------|------|--------|
| **Admin** | `admin` | Everything + grant/revoke permissions |
| **Edit** | `edit` | Create, read, update, delete data |
| **View** | `view` | Read-only access |

**Hierarchy**: `admin > edit > view`

---

## 🎯 Permission Scopes

| Scope | Company | Category | Access |
|-------|---------|----------|--------|
| **Super Admin** | `NULL` | `NULL` | Everything in system |
| **Company Admin** | `"Acme Corp"` | `NULL` | All categories for Acme |
| **Category-Specific** | `"Acme Corp"` | `"SASE"` | Only SASE for Acme |

---

## 💻 Code Examples

### Python: Check Permission

```python
from auth_middleware import require_permission

@require_permission('edit', company='Acme Corp', category='SASE')
def edit_sase_data(request, current_user):
    return success_response(data={'message': 'Access granted'})
```

### Python: Require Authentication

```python
from auth_middleware import require_auth

@require_auth
def protected_endpoint(request, current_user):
    user_id = current_user['user_id']
    return success_response(data={'user_id': user_id})
```

### Python: Grant Permission

```python
from permissions_utils import grant_permission

success, perm_id, error = grant_permission(
    user_id='user-123',
    permission_level='edit',
    granted_by='admin-456',
    company='Acme Corp',
    category='SASE'
)
```

### Python: Check Permission Manually

```python
from permissions_utils import check_permission

can_edit = check_permission(
    user_id='user-123',
    required_level='edit',
    company='Acme Corp',
    category='SASE'
)
```

---

## 🛠️ CLI Tools

### Create Admin User

```bash
python3 create_admin.py \
  --email "admin@opextech.com" \
  --name "Admin User" \
  --password "SecureP@ss123"
```

### Grant Permission

```bash
# Super admin
python3 grant_permission_cli.py --user-id USER_ID --level admin

# Company admin
python3 grant_permission_cli.py --user-id USER_ID --level admin --company "Acme"

# Category-specific
python3 grant_permission_cli.py --user-id USER_ID --level edit \
  --company "Acme" --category "SASE"
```

---

## 🗄️ BigQuery Queries

### Get User by Email

```sql
SELECT * FROM `opex-data-lake-k23k4y98m.auth.users`
WHERE email = 'user@example.com';
```

### Get User Permissions

```sql
SELECT
  p.*,
  u.email,
  u.full_name
FROM `opex-data-lake-k23k4y98m.auth.permission_groups` p
JOIN `opex-data-lake-k23k4y98m.auth.users` u ON p.user_id = u.user_id
WHERE u.email = 'user@example.com'
  AND p.is_active = TRUE;
```

### List All Admins

```sql
SELECT
  u.email,
  u.full_name,
  p.company,
  p.category,
  p.granted_at
FROM `opex-data-lake-k23k4y98m.auth.permission_groups` p
JOIN `opex-data-lake-k23k4y98m.auth.users` u ON p.user_id = u.user_id
WHERE p.permission_level = 'admin'
  AND p.is_active = TRUE
ORDER BY p.granted_at DESC;
```

### Get Active Sessions

```sql
SELECT
  s.*,
  u.email
FROM `opex-data-lake-k23k4y98m.auth.sessions` s
JOIN `opex-data-lake-k23k4y98m.auth.users` u ON s.user_id = u.user_id
WHERE s.is_active = TRUE
  AND s.expires_at > CURRENT_TIMESTAMP()
ORDER BY s.created_at DESC;
```

---

## 🔑 Token Management

### Token Lifespans

- **Access Token**: 24 hours
- **Refresh Token**: 30 days

### Refresh Token Flow

```bash
# 1. Login to get tokens
curl -X POST .../auth/login \
  -d '{"email":"user@example.com","password":"pass"}' \
  | jq '.data.refresh_token' > refresh_token.txt

# 2. When access token expires, refresh it
curl -X POST .../auth/refresh \
  -d "{\"refresh_token\":\"$(cat refresh_token.txt)\"}" \
  | jq '.data.access_token' > access_token.txt

# 3. Use new access token
curl -X GET .../auth/me \
  -H "Authorization: Bearer $(cat access_token.txt)"
```

---

## ⚠️ Known Issues

### BigQuery Streaming Buffer Limitation

**Issue**: Login fails for newly registered users (within 90 minutes)

**Why**: BigQuery cannot UPDATE rows in streaming buffer

**Workaround**: Wait 90 minutes after registration

**Solution**: Migrate auth data to Firestore (see `BIGQUERY_LIMITATIONS.md`)

---

## 📁 File Structure

```
backend/auth/
├── main.py                          # Auth API endpoints
├── permissions_api.py               # Permission API endpoints
├── jwt_utils.py                     # JWT token management
├── password_utils.py                # Password hashing (bcrypt)
├── permissions_utils.py             # Permission logic
├── auth_middleware.py               # Decorators & middleware
├── create_admin.py                  # Create admin user script
├── grant_permission_cli.py          # Grant permission script
├── PERMISSIONS_README.md            # Full permission docs
├── ADMIN_SETUP.md                   # Admin setup guide
├── BIGQUERY_LIMITATIONS.md          # Known issues
└── QUICK_REFERENCE.md               # This file
```

---

## 📚 Documentation Links

- **Full Permission Docs**: `PERMISSIONS_README.md`
- **Admin Setup**: `ADMIN_SETUP.md`
- **BigQuery Issues**: `BIGQUERY_LIMITATIONS.md`
- **Deployment**: `../../DEPLOYMENT.md`
- **Project Status**: `../../PROJECT_STATUS.md`

---

## 🔍 Common Tasks

### Task: Register User

```bash
curl -X POST .../auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ss123",
    "full_name": "User Name"
  }'
```

### Task: Grant Edit Permission

```bash
# Get admin token first
ADMIN_TOKEN=$(curl -X POST .../auth/login \
  -d '{"email":"admin@opextech.com","password":"AdminPass"}' \
  | jq -r '.data.access_token')

# Grant permission
curl -X POST .../permissions/grant \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "target-user-id",
    "permission_level": "edit",
    "company": "Acme Corp",
    "category": "SASE"
  }'
```

### Task: Check User's Permissions

```bash
curl -X GET .../permissions/user/USER_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Task: Revoke Permission

```bash
curl -X POST .../permissions/revoke \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "permission_id": "perm-123",
    "notes": "User left company"
  }'
```

---

## 🐛 Troubleshooting

### Problem: "Invalid or expired token"

**Check**:
```bash
curl -X POST .../auth/verify \
  -d '{"access_token":"YOUR_TOKEN"}'
```

**Solution**: Refresh token or login again

### Problem: "Permission denied"

**Check**:
```sql
SELECT * FROM `opex-data-lake-k23k4y98m.auth.permission_groups`
WHERE user_id = 'YOUR_USER_ID' AND is_active = TRUE;
```

**Solution**: Grant required permission

### Problem: "User not found"

**Check**:
```sql
SELECT * FROM `opex-data-lake-k23k4y98m.auth.users`
WHERE email = 'user@example.com';
```

**Solution**: User may not exist, register first

---

## 📞 Support

- **Documentation**: See README files in `/backend/auth/`
- **Issues**: Check `BIGQUERY_LIMITATIONS.md`
- **Status**: `PROJECT_STATUS.md`

---

**Quick Reference v1.0.0** | Opex Technologies | Dayta Analytics

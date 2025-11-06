# Authentication API

JWT-based authentication system for Form Builder & Response Scoring System.

## Features

- **User Registration** with email validation and password strength requirements
- **Password Hashing** using bcrypt with cost factor 12 (~250ms per hash)
- **JWT Tokens** with access (24hr) and refresh (30 day) token strategy
- **Session Management** with database-backed revocation support
- **Account Security** with failed login tracking and automatic lockout
- **Token Refresh** to extend sessions without re-authentication

## Security

### Password Hashing
- **Algorithm**: bcrypt with cost factor 12 (4,096 iterations)
- **Performance**: ~250ms per hash/verify (acceptable UX)
- **Attack Resistance**: ~4 hashes/second makes brute-force impractical
- **Future-Proof**: Cost factor can be increased as computers get faster

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### JWT Tokens
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Access Token**: 24-hour expiration, used for API authentication
- **Refresh Token**: 30-day expiration, used to obtain new access tokens
- **Session Tracking**: Refresh tokens stored with SHA-256 hash in database
- **Revocation**: Sessions can be revoked (logout, password change)

### Account Protection
- Failed login attempts tracked per user
- Account locked for 30 minutes after 5 failed attempts
- All sessions revoked on password change
- Constant-time password verification (prevents timing attacks)

## API Endpoints

### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "MyP@ssw0rd123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2025-11-05T12:00:00Z"
  },
  "message": "User registered successfully"
}
```

**Errors:**
- `400` - Validation error (weak password, invalid email, missing fields)
- `409` - Email already registered

---

### POST /auth/login
Login and receive access + refresh tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "MyP@ssw0rd123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "full_name": "John Doe"
    }
  },
  "message": "Login successful"
}
```

**Errors:**
- `401` - Invalid credentials, account inactive, or account locked
- `400` - Missing email or password

**Notes:**
- Failed login attempts increment counter
- Account locked for 30 minutes after 5 failed attempts
- Counter resets on successful login

---

### POST /auth/refresh
Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 86400
  }
}
```

**Errors:**
- `401` - Invalid or expired refresh token, or session revoked

---

### POST /auth/logout
Logout and revoke refresh token session.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### POST /auth/verify
Verify access token validity.

**Request:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "expires_at": "2025-11-06T12:00:00Z"
  }
}
```

---

### GET /auth/me
Get current user information.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "status": "active",
    "created_at": "2025-11-05T12:00:00Z",
    "last_login": "2025-11-05T14:30:00Z"
  }
}
```

**Errors:**
- `401` - Missing, invalid, or expired access token

---

## Usage Examples

### Registration Flow
```javascript
// Register new user
const response = await fetch('https://auth-api.example.com/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'MyP@ssw0rd123',
    full_name: 'John Doe'
  })
});

const data = await response.json();
console.log('User registered:', data.data.user_id);
```

### Login Flow
```javascript
// Login
const loginResponse = await fetch('https://auth-api.example.com/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'MyP@ssw0rd123'
  })
});

const { access_token, refresh_token } = (await loginResponse.json()).data;

// Store tokens securely (e.g., httpOnly cookies or secure storage)
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);
```

### Authenticated API Call
```javascript
// Make authenticated request
const response = await fetch('https://api.example.com/forms', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});

// Handle 401 by refreshing token
if (response.status === 401) {
  // Refresh access token
  const refreshResponse = await fetch('https://auth-api.example.com/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      refresh_token: localStorage.getItem('refresh_token')
    })
  });

  const { access_token } = (await refreshResponse.json()).data;
  localStorage.setItem('access_token', access_token);

  // Retry original request
  // ...
}
```

### Logout Flow
```javascript
// Logout
await fetch('https://auth-api.example.com/auth/logout', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    refresh_token: localStorage.getItem('refresh_token')
  })
});

// Clear tokens
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
```

## Deployment

### Deploy to Google Cloud Functions

```bash
cd backend/auth/

# Deploy authentication API
gcloud functions deploy auth-api \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-central1 \
  --entry-point auth_handler \
  --set-env-vars PROJECT_ID=opex-data-lake-k23k4y98m,JWT_SECRET_KEY=$JWT_SECRET_KEY

# Get function URL
gcloud functions describe auth-api --region us-central1 --format='value(httpsTrigger.url)'
```

### Environment Variables

Set these in Cloud Functions configuration:

```bash
PROJECT_ID=opex-data-lake-k23k4y98m
JWT_SECRET_KEY=your-secure-random-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=30
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30
```

## Local Development

```bash
cd backend/auth/

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PROJECT_ID=opex-data-lake-k23k4y98m
export JWT_SECRET_KEY=test-secret-key

# Run locally with Functions Framework
functions-framework --target=auth_handler --port=8080

# Test endpoints
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","full_name":"Test User"}'
```

## Testing

```bash
cd backend/

# Run authentication tests
pytest tests/test_auth_password.py -v
pytest tests/test_auth_jwt.py -v

# Run with coverage
pytest tests/test_auth*.py --cov=auth --cov-report=html
```

## Database Schema

### auth.users
Stores user accounts and authentication data.

### auth.sessions
Stores active refresh token sessions with SHA-256 hashes.

### auth.permission_groups
Stores user permissions (RBAC).

See `/database/schemas/` for complete schema definitions.

## Security Best Practices

### Token Storage (Client-Side)
- **Best**: httpOnly cookies (prevents XSS)
- **Good**: Secure storage API (mobile apps)
- **Acceptable**: localStorage with Content Security Policy
- **Never**: Plain cookies or global variables

### Token Transmission
- Always use HTTPS in production
- Include tokens in `Authorization: Bearer <token>` header
- Never pass tokens in URL query parameters

### Token Lifecycle
- Access tokens expire after 24 hours (cannot be revoked)
- Refresh tokens expire after 30 days (can be revoked)
- Always revoke all sessions on password change
- Implement auto-logout on token expiration

### Production Checklist
- [ ] Generate strong JWT_SECRET_KEY (at least 32 random bytes)
- [ ] Enable HTTPS only
- [ ] Set appropriate CORS origins (not *)
- [ ] Implement rate limiting on login endpoint
- [ ] Monitor failed login attempts
- [ ] Set up alerts for unusual activity
- [ ] Regularly cleanup expired sessions (Cloud Scheduler)

## Monitoring

### Key Metrics
- Failed login attempts per user
- Account lockouts per day
- Token refresh rate
- Session duration average
- Active sessions count

### Logging
All authentication events are logged with structured JSON:
- User registration
- Login success/failure
- Token refresh
- Logout
- Account lockout

View logs in Google Cloud Logging:
```bash
gcloud functions logs read auth-api --region=us-central1 --limit=50
```

## Troubleshooting

### "Token has expired"
- Access tokens expire after 24 hours
- Use refresh token to get new access token
- Implement automatic token refresh in client

### "Account is temporarily locked"
- Account locked after 5 failed login attempts
- Lockout duration: 30 minutes
- User can request password reset to unlock immediately

### "Invalid token signature"
- JWT_SECRET_KEY mismatch between environments
- Ensure same secret used for generation and verification
- Tokens cannot be validated if secret changes

### "Session has been revoked"
- Refresh token session was revoked (logout, password change)
- User needs to login again to get new tokens

## License

Proprietary - Opex Technologies

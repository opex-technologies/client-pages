# Deployment Guide - Form Builder & Response Scoring System

**Created**: November 5, 2025
**Status**: Phase 1 - Infrastructure & Authentication
**Environment**: Google Cloud Platform (GCP)

## Overview

This document provides complete deployment instructions for the Form Builder & Response Scoring System authentication infrastructure.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Deployment (Authentication API)](#backend-deployment)
3. [Frontend Deployment (Auth UI)](#frontend-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Known Issues](#known-issues)
6. [Monitoring & Logs](#monitoring--logs)
7. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Tools

- **Google Cloud SDK** (gcloud CLI) - v450.0.0+
- **Node.js** - v18.x or later
- **npm** - v9.x or later
- **Python** - v3.10+

### GCP Project Setup

```bash
# Set your GCP project
export PROJECT_ID="opex-data-lake-k23k4y98m"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Authentication

```bash
# Login to GCP
gcloud auth login

# Set application default credentials
gcloud auth application-default login
```

---

## Backend Deployment

### 1. Environment Variables

Create environment variables for deployment:

```bash
export PROJECT_ID="opex-data-lake-k23k4y98m"
export REGION="us-central1"
export JWT_SECRET_KEY="94_ZkQrzjLcZxefMEcFrxFBdlCK5YTpG777czsv-m-A"  # CHANGE IN PRODUCTION
```

⚠️ **Security Warning**: The JWT_SECRET_KEY above is for development. Generate a new secure key for production:

```bash
# Generate secure JWT secret
export JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "JWT_SECRET_KEY: $JWT_SECRET_KEY"
```

### 2. Deploy Authentication API

Navigate to the auth directory and deploy:

```bash
cd "backend/auth"

# Deploy Cloud Function (Gen2)
gcloud functions deploy auth-api \
  --gen2 \
  --runtime=python310 \
  --region=$REGION \
  --source=. \
  --entry-point=auth_handler \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,JWT_SECRET_KEY=$JWT_SECRET_KEY,ENVIRONMENT=production" \
  --timeout=60s \
  --memory=512MB \
  --max-instances=10
```

### 3. Verify Deployment

```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe auth-api \
  --region=$REGION \
  --format='value(serviceConfig.uri)')

echo "Authentication API deployed at: $FUNCTION_URL"

# Test registration endpoint
curl -X POST "$FUNCTION_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestP@ssw0rd123",
    "full_name": "Test User"
  }'
```

### 4. Deployment Output

Expected output:

```
state: ACTIVE
url: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api
```

**API Endpoints Available**:
- `POST /auth/register` - User registration
- `POST /auth/login` - User login (⚠️ see known issues)
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - User logout
- `POST /auth/verify` - Token verification
- `GET /auth/me` - Get current user

---

## Frontend Deployment

### 1. Install Dependencies

```bash
cd "frontend/auth-ui"
npm install
```

### 2. Configure API URL

The production API URL is already configured in `.env.production`:

```bash
VITE_API_BASE_URL=https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api
```

### 3. Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### 4. Deploy to GitHub Pages

```bash
npm run deploy
```

This will:
1. Build the production bundle
2. Deploy to GitHub Pages (gh-pages branch)
3. Make the UI available at your GitHub Pages URL

### 5. Alternative: Deploy to Cloud Storage

For hosting on Google Cloud Storage:

```bash
# Create storage bucket (if not exists)
gsutil mb -p $PROJECT_ID -l $REGION gs://opex-auth-ui

# Enable website hosting
gsutil web set -m index.html -e index.html gs://opex-auth-ui

# Upload dist files
gsutil -m cp -r dist/* gs://opex-auth-ui/

# Make public
gsutil iam ch allUsers:objectViewer gs://opex-auth-ui
```

---

## Environment Configuration

### Backend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `PROJECT_ID` | GCP Project ID | Yes | opex-data-lake-k23k4y98m |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Yes | (must set in production) |
| `ENVIRONMENT` | Deployment environment | No | development |
| `REGION` | GCP region | No | us-central1 |
| `JWT_EXPIRATION_HOURS` | Access token lifespan | No | 24 |
| `JWT_REFRESH_EXPIRATION_DAYS` | Refresh token lifespan | No | 30 |
| `BCRYPT_ROUNDS` | Password hashing cost | No | 12 |
| `MAX_LOGIN_ATTEMPTS` | Failed login limit | No | 5 |
| `ACCOUNT_LOCKOUT_MINUTES` | Lockout duration | No | 30 |

### Frontend Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `VITE_API_BASE_URL` | Authentication API URL | Yes | http://localhost:8080 |

---

## Known Issues

### ⚠️ BigQuery Streaming Buffer Limitation

**Issue**: Login fails for newly registered users (within 90 minutes of registration)

**Cause**: BigQuery's streaming buffer prevents UPDATE/DELETE operations on recently inserted rows. The authentication workflow requires updating user records during login (last_login timestamp, failed_login_attempts counter).

**Impact**:
- ✅ User registration works
- ❌ Login fails with error: "UPDATE statement would affect rows in streaming buffer"
- ✅ Token verification works
- ❌ Failed login tracking doesn't work

**Workaround**: Wait 90 minutes after registration before attempting login

**Permanent Solution**: Migrate authentication data from BigQuery to Firestore or Cloud SQL

See `backend/auth/BIGQUERY_LIMITATIONS.md` for detailed migration plan.

---

## Monitoring & Logs

### View Cloud Function Logs

```bash
# Real-time logs
gcloud functions logs read auth-api \
  --region=$REGION \
  --limit=50 \
  --follow

# Filter errors only
gcloud functions logs read auth-api \
  --region=$REGION \
  --limit=50 | grep "ERROR"
```

### Cloud Console

View logs in the GCP Console:
```
https://console.cloud.google.com/functions/details/us-central1/auth-api?project=opex-data-lake-k23k4y98m
```

### Key Metrics to Monitor

1. **Function Invocations** - Request count
2. **Error Rate** - Failed requests
3. **Execution Time** - Response latency
4. **Memory Usage** - Resource consumption
5. **Cold Starts** - Instance initialization time

### BigQuery Data Verification

Check authentication data:

```sql
-- View all users
SELECT
  user_id,
  email,
  full_name,
  status,
  created_at,
  last_login,
  failed_login_attempts
FROM `opex-data-lake-k23k4y98m.auth.users`
ORDER BY created_at DESC;

-- View active sessions
SELECT
  session_id,
  user_id,
  created_at,
  expires_at,
  is_active
FROM `opex-data-lake-k23k4y98m.auth.sessions`
WHERE is_active = true
  AND expires_at > CURRENT_TIMESTAMP()
ORDER BY created_at DESC;
```

---

## Rollback Procedures

### Rollback Backend

```bash
# List recent revisions
gcloud functions describe auth-api \
  --region=$REGION \
  --format='value(serviceConfig.revision)'

# Deploy previous version
gcloud functions deploy auth-api \
  --gen2 \
  --runtime=python310 \
  --region=$REGION \
  --source=. \
  --entry-point=auth_handler \
  --trigger-http \
  --allow-unauthenticated
```

### Rollback Frontend

GitHub Pages:
```bash
# Revert to previous commit
git revert HEAD
git push origin main

# Redeploy
npm run deploy
```

Cloud Storage:
```bash
# Backup current version
gsutil -m cp -r gs://opex-auth-ui gs://opex-auth-ui-backup-$(date +%Y%m%d)

# Restore previous version
gsutil -m cp -r gs://opex-auth-ui-backup-YYYYMMDD/* gs://opex-auth-ui/
```

---

## Security Checklist

### Before Production Deployment

- [ ] Generate new JWT_SECRET_KEY (not the development key)
- [ ] Set ENVIRONMENT=production
- [ ] Review CORS settings in response_helpers_standalone.py
- [ ] Enable rate limiting (if implemented)
- [ ] Restrict Cloud Function access (remove --allow-unauthenticated)
- [ ] Set up API Gateway with authentication
- [ ] Enable Cloud Armor for DDoS protection
- [ ] Configure Cloud CDN for frontend
- [ ] Set up SSL/TLS certificates
- [ ] Review IAM permissions
- [ ] Enable audit logging
- [ ] Set up alerting for security events

### Post-Deployment

- [ ] Test all endpoints thoroughly
- [ ] Verify CORS headers
- [ ] Check JWT token expiration
- [ ] Test rate limiting
- [ ] Review security logs
- [ ] Perform penetration testing
- [ ] Document API for users

---

## Troubleshooting

### Function Won't Deploy

**Error**: "Container Healthcheck failed"

**Solution**: Check imports in main.py and ensure all standalone files are present.

### Registration Works But Login Fails

**Error**: "UPDATE statement would affect rows in streaming buffer"

**Solution**: This is the known BigQuery limitation. Wait 90 minutes or migrate to Firestore.

### CORS Errors in Browser

**Error**: "Access-Control-Allow-Origin header is missing"

**Solution**: Verify CORS headers in response_helpers_standalone.py:
```python
'Access-Control-Allow-Origin': '*',  # Update for production
'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
'Access-Control-Allow-Headers': 'Content-Type, Authorization'
```

### JWT Verification Fails

**Error**: "Invalid signature"

**Solution**: Ensure JWT_SECRET_KEY matches between all environments and hasn't changed.

---

## Next Steps

1. **Immediate**: Review BigQuery limitations document
2. **Short-term**: Plan Firestore migration (see BIGQUERY_LIMITATIONS.md)
3. **Medium-term**: Implement API Gateway and rate limiting
4. **Long-term**: Add MFA, OAuth, and advanced security features

---

## Support & Contact

**Project**: Form Builder & Response Scoring System
**Owner**: Opex Technologies
**Documentation**: See `IMPLEMENTATION_PLAN.md` and `PROJECT_STATUS.md`
**Issue Tracker**: Track issues in project documentation

---

**Last Updated**: November 5, 2025
**Version**: 1.0.0
**Deployment Status**: ✅ Backend Deployed | ⚠️ Functional with limitations

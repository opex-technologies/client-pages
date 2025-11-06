# Backend Services - Opex Technologies

**Project**: Q4 Form Scoring System
**Status**: Phase 2 Backend Complete ✅
**Last Updated**: November 6, 2025

This directory contains the backend services for the Form Builder & Response Scoring System.

---

## 🚀 Service Status

| Service | Status | Version | Documentation |
|---------|--------|---------|---------------|
| **Auth API** | ✅ Deployed | 1.0 | `auth/QUICK_REFERENCE.md` |
| **Form Builder API** | ✅ Complete | 1.1.0 | `form_builder/GETTING_STARTED.md` ⭐ |
| **Response Scorer API** | ⏭️ Pending | - | (Phase 3) |

### Form Builder API (Phase 2) - COMPLETE ✅
- **Status**: 100% Complete, Production Ready
- **Endpoints**: 9 (all working)
- **Features**: Template CRUD, Question DB, Form Generation, **GitHub Deployment**
- **Documentation**: 13 comprehensive documents (7,400+ lines)
- **Get Started**: [form_builder/GETTING_STARTED.md](./form_builder/GETTING_STARTED.md)

**Latest Achievement**: One-click GitHub Pages deployment added (v1.1.0)

---

## Directory Structure

```
backend/
├── auth/               # Authentication & Authorization API
├── form_builder/       # Form Builder API
├── response_scorer/    # Response Scorer API
├── common/            # Shared utilities and helpers
├── tests/             # Test suite
└── requirements.txt   # Python dependencies
```

## Setup

### 1. Install Dependencies

```bash
cd backend/
pip3 install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the `backend/` directory with the following variables:

```bash
# GCP Configuration
PROJECT_ID=opex-data-lake-k23k4y98m
REGION=us-central1

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# BigQuery Datasets
AUTH_DATASET=auth
FORM_BUILDER_DATASET=form_builder
SCORING_DATASET=scoring
OPEX_DEV_DATASET=opex_dev

# Environment
ENVIRONMENT=development  # development, staging, production
```

### 3. Run Tests

```bash
pytest tests/ -v --cov=. --cov-report=html
```

## Architecture

### Cloud Functions

Each application is deployed as a separate Google Cloud Function:

- **Authentication API**: `auth-api` - User authentication, JWT tokens, permissions
- **Form Builder API**: `form-builder-api` - Form templates, question management, deployment
- **Response Scorer API**: `response-scorer-api` - Response processing, scoring, reporting

### Shared Components

The `common/` directory contains:
- `bigquery_client.py` - BigQuery connection management
- `validators.py` - Input validation utilities
- `response_helpers.py` - HTTP response formatting
- `config.py` - Configuration management
- `logger.py` - Logging infrastructure

## Development

### Local Testing

Each API can be tested locally using the Functions Framework:

```bash
# Test Authentication API
functions-framework --target=auth_handler --source=auth/ --port=8080

# Test Form Builder API
functions-framework --target=form_builder_handler --source=form_builder/ --port=8081

# Test Response Scorer API
functions-framework --target=response_scorer_handler --source=response_scorer/ --port=8082
```

### Code Quality

Before committing, run:

```bash
# Format code
black .

# Lint code
pylint **/*.py

# Type checking
mypy .

# Tests with coverage
pytest tests/ -v --cov=.
```

## Deployment

Deploy to Google Cloud Functions:

```bash
# Deploy Authentication API
gcloud functions deploy auth-api \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-central1 \
  --source auth/ \
  --entry-point auth_handler

# Deploy Form Builder API
gcloud functions deploy form-builder-api \
  --runtime python310 \
  --trigger-http \
  --region us-central1 \
  --source form_builder/ \
  --entry-point form_builder_handler

# Deploy Response Scorer API
gcloud functions deploy response-scorer-api \
  --runtime python310 \
  --trigger-http \
  --region us-central1 \
  --source response_scorer/ \
  --entry-point response_scorer_handler
```

## 🎯 Quick Start

### Get Authentication Token
```bash
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'

export TOKEN="eyJhbGc..."
```

### Use Form Builder API
```bash
export API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api"

# Query questions
curl "$API_URL/form-builder/questions?page_size=5" \
  -H "Authorization: Bearer $TOKEN"
```

**Full Tutorial**: [form_builder/GETTING_STARTED.md](./form_builder/GETTING_STARTED.md)

---

## API Documentation

### Authentication API ✅
**URL**: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - Logout and invalidate token
- `POST /permissions/grant` - Grant permission
- `POST /permissions/revoke` - Revoke permission
- `GET /permissions/user/:user_id` - Get user permissions

**Docs**: `auth/QUICK_REFERENCE.md`

### Form Builder API ✅ (v1.1.0)
**URL**: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api

**Templates**:
- `POST /form-builder/templates` - Create template
- `GET /form-builder/templates` - List templates
- `GET /form-builder/templates/:id` - Get template
- `PUT /form-builder/templates/:id` - Update template
- `DELETE /form-builder/templates/:id` - Delete template
- `POST /form-builder/templates/:id/deploy` - **Deploy to GitHub Pages** ⭐

**Questions**:
- `GET /form-builder/questions` - Query questions
- `GET /form-builder/questions/:id` - Get question

**Preview**:
- `POST /form-builder/preview` - Generate HTML form

**Complete Docs**:
- Quick Start: `form_builder/GETTING_STARTED.md`
- API Reference: `form_builder/API_SPEC.md`
- Quick Reference: `form_builder/QUICK_REFERENCE.md`

### Response Scorer API ⏭️
**Status**: Not Yet Implemented (Phase 3)

**Planned**:
- `GET /responses` - List all scored responses
- `GET /responses/:id` - Get response details
- `POST /responses/score` - Score a new response
- `GET /responses/:id/report` - Generate PDF report
- `GET /analytics/summary` - Get scoring analytics

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_ID` | GCP Project ID | opex-data-lake-k23k4y98m |
| `JWT_SECRET_KEY` | Secret key for JWT signing | (required) |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `JWT_EXPIRATION_HOURS` | Token expiration time | 24 |
| `ENVIRONMENT` | Deployment environment | development |

## Security

- All API endpoints (except login/register) require JWT authentication
- Passwords are hashed with bcrypt (cost factor 12)
- JWT tokens expire after 24 hours
- MFA support via TOTP
- Role-based access control (view, edit, admin)

## Troubleshooting

### BigQuery Connection Issues

```python
# Test BigQuery connectivity
from google.cloud import bigquery
client = bigquery.Client(project='opex-data-lake-k23k4y98m')
query = "SELECT 1"
result = list(client.query(query).result())
print(result)
```

### JWT Token Issues

```python
# Test JWT token generation
import jwt
import datetime

payload = {
    'user_id': 'test-user',
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
}
token = jwt.encode(payload, 'your-secret-key', algorithm='HS256')
print(token)
```

## Contributing

1. Create feature branch from `main`
2. Make changes with appropriate tests
3. Run code quality checks (black, pylint, mypy)
4. Run test suite with coverage
5. Submit pull request

## License

Proprietary - Opex Technologies

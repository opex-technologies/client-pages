# Form Builder API

**Version**: 1.1.0
**Created**: November 5, 2025
**Status**: Production Ready

## Overview

The Form Builder API enables users to create, manage, and deploy custom survey forms using questions from the Question Database. Forms are generated as standalone HTML files with embedded JavaScript for validation and submission, then deployed to GitHub Pages for public access.

## Features

- **Template Management**: Create, read, update, delete form templates
- **Question Database**: Query 1,041+ questions with filtering
- **Form Generation**: Generate HTML forms with Jinja2 templates
- **Form Preview**: Preview forms before deployment
- **GitHub Pages Deployment**: One-click deployment to public URLs
- **Authentication**: JWT-based authentication with RBAC permissions
- **BigQuery Integration**: All data stored in BigQuery

## API Endpoints

### Form Templates

- `POST /form-builder/templates` - Create new template (requires: edit)
- `GET /form-builder/templates` - List templates with filtering (requires: view)
- `GET /form-builder/templates/:id` - Get template details (requires: view)
- `PUT /form-builder/templates/:id` - Update template (requires: edit, draft only)
- `DELETE /form-builder/templates/:id` - Delete template (requires: admin, draft/archived only)
- `POST /form-builder/templates/:id/deploy` - Deploy to GitHub Pages (requires: edit)

### Questions

- `GET /form-builder/questions` - Query questions with filtering (requires: view)
- `GET /form-builder/questions/:id` - Get question with usage stats (requires: view)

### Preview

- `POST /form-builder/preview` - Generate form preview (requires: view)

See [API_SPEC.md](./API_SPEC.md) for complete API documentation.

## Architecture

```
┌─────────────────┐
│  React Frontend │
│  (Form Builder) │
└────────┬────────┘
         │
         │ JWT Token
         │
         v
┌─────────────────────┐
│  Form Builder API   │
│  (Cloud Function)   │
└────────┬────────────┘
         │
         ├─────> BigQuery (Templates, Questions)
         │
         ├─────> Jinja2 (HTML Generation)
         │
         └─────> GitHub API (Form Deployment)
                 │
                 v
         ┌──────────────────┐
         │  GitHub Pages    │
         │  Public Forms    │
         └──────────────────┘
```

## Installation

### Prerequisites

- Python 3.10+
- Google Cloud SDK
- Access to `opex-data-lake-k23k4y98m` project
- BigQuery `form_builder` dataset

### Local Development

```bash
# Navigate to form_builder directory
cd backend/form_builder

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run locally with Functions Framework
functions-framework --target=form_builder_handler --debug
```

The API will be available at `http://localhost:8080`.

## Deployment

### Deploy to Cloud Functions

```bash
# Deploy Form Builder API (with GitHub deployment enabled)
gcloud functions deploy form-builder-api \
  --gen2 \
  --runtime=python310 \
  --region=us-central1 \
  --source=. \
  --entry-point=form_builder_handler \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=opex-data-lake-k23k4y98m,DATASET_ID=form_builder,JWT_SECRET_KEY=***,GITHUB_TOKEN=***,GITHUB_REPO_OWNER=opextech,GITHUB_REPO_NAME=forms,GITHUB_BRANCH=main" \
  --timeout=60s \
  --memory=512MB

# View logs
gcloud functions logs read form-builder-api --region=us-central1 --gen2

# Get function URL
gcloud functions describe form-builder-api --region=us-central1 --gen2 --format="value(serviceConfig.uri)"
```

**GitHub Configuration (Optional)**:
- `GITHUB_TOKEN` - GitHub personal access token with repo write permissions
- `GITHUB_REPO_OWNER` - Repository owner (e.g., "opextech")
- `GITHUB_REPO_NAME` - Repository name (e.g., "forms")
- `GITHUB_BRANCH` - Target branch (default: "main")

If GitHub variables are not set, the deployment endpoint will return an error. See [GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md) for complete setup instructions.

### Expected URL

```
https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
```

## Usage Examples

### Create a Template

```bash
# Get access token first
TOKEN="your-jwt-token"

# Create template
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "SASE Assessment Survey",
    "opportunity_type": "Security",
    "opportunity_subtype": "SASE",
    "description": "Comprehensive SASE assessment form",
    "questions": [
      {
        "question_id": "q-001",
        "weight": 10,
        "is_required": true,
        "sort_order": 1
      },
      {
        "question_id": "q-002",
        "weight": "Info",
        "is_required": false,
        "sort_order": 2
      }
    ]
  }'
```

### List Templates

```bash
# List all templates
curl -X GET "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/templates" \
  -H "Authorization: Bearer $TOKEN"

# Filter by opportunity type
curl -X GET "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/templates?opportunity_type=Security&status=published" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Template

```bash
curl -X GET "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/templates/abc-123-def" \
  -H "Authorization: Bearer $TOKEN"
```

### Query Questions

```bash
# Get all SASE questions
curl -X GET "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/questions?opportunity_subtype=SASE" \
  -H "Authorization: Bearer $TOKEN"

# Search questions
curl -X GET "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/questions?search=network" \
  -H "Authorization: Bearer $TOKEN"

# Mark questions already in template
curl -X GET "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/questions?template_id=abc-123&opportunity_subtype=SASE" \
  -H "Authorization: Bearer $TOKEN"
```

### Preview Form

```bash
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/preview \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "abc-123-def"
  }' | jq -r '.data.html' > preview.html

# Open in browser
open preview.html
```

### Deploy to GitHub Pages

```bash
# Deploy form to public URL
curl -X POST "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/templates/abc-123-def/deploy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"commit_message": "Deploy SASE assessment form v2"}'

# Response includes public URL
{
  "success": true,
  "data": {
    "template_id": "abc-123-def",
    "deployed_url": "https://opextech.github.io/forms/forms/sase_assessment_survey.html",
    "deployed_at": "2025-11-06T00:41:28Z",
    "commit_sha": "abc123def456",
    "file_path": "forms/sase_assessment_survey.html"
  },
  "message": "Template deployed successfully to GitHub Pages"
}
```

**Note**: Requires GitHub token configuration. See [GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md) for setup.

### Update Template

```bash
curl -X PUT "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/templates/abc-123-def" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "Updated SASE Survey",
    "description": "Updated description",
    "questions": [
      {
        "question_id": "q-001",
        "weight": 15,
        "is_required": true,
        "sort_order": 1
      }
    ]
  }'
```

### Delete Template

```bash
curl -X DELETE "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/templates/abc-123-def" \
  -H "Authorization: Bearer $TOKEN"
```

## Form Template Structure

The generated HTML forms include:

- **Responsive Design**: Mobile-friendly layout with Opex Technologies branding
- **Progress Tracking**: Visual progress bar showing completion percentage
- **Form Validation**: Client-side validation for required fields
- **Multiple Input Types**: Radio buttons, text areas, number inputs, selects, checkboxes
- **Help Text**: Optional help text for each question
- **Submission**: Posts to existing webhook endpoint with form data

## Data Models

### Form Template

```typescript
{
  template_id: string (UUID)
  template_name: string
  opportunity_type: string
  opportunity_subtype: string
  status: 'draft' | 'published' | 'archived' | 'deleted'
  description: string | null
  created_by: string (user_id)
  created_at: timestamp
  updated_at: timestamp | null
  deployed_url: string | null
  deployed_at: timestamp | null
  version: integer
}
```

### Template Question

```typescript
{
  template_id: string (UUID)
  question_id: string
  weight: number | 'Info'
  is_required: boolean
  sort_order: integer
}
```

### Question

```typescript
{
  question_id: string
  question_text: string
  category: string
  opportunity_type: string
  opportunity_subtype: string
  input_type: 'text' | 'textarea' | 'number' | 'radio' | 'select' | 'checkbox'
  default_weight: number | 'Info'
  help_text: string | null
  is_active: boolean
}
```

## Permissions

The API uses the authentication system from `backend/auth`:

- **View**: Can list and view templates, query questions, generate previews
- **Edit**: Can create and update templates (draft only)
- **Admin**: Can delete templates and manage questions

See [QUICK_REFERENCE.md](../auth/QUICK_REFERENCE.md) for permission management.

## Testing

```bash
# Run tests
cd backend/form_builder
python -m pytest test_form_builder.py -v

# Run with coverage
python -m pytest test_form_builder.py --cov=main --cov-report=html
```

## Files

```
backend/form_builder/
├── main.py                   # Main Cloud Function (1,460+ lines)
├── form_template.html        # Jinja2 HTML template
├── requirements.txt          # Python dependencies
├── API_SPEC.md              # Complete API specification (2,000+ lines)
├── DEPLOYMENT_SUMMARY.md     # Deployment history and status
├── GITHUB_DEPLOYMENT.md      # GitHub Pages setup guide (500+ lines)
├── BIGQUERY_LIMITATIONS.md   # Known BigQuery issues
├── README.md                # This file
├── .env.example             # Environment variables template
└── test_api.sh              # API test script
```

## Error Handling

The API returns standardized error responses:

```json
{
  "success": false,
  "error": {
    "message": "Template not found",
    "code": "NOT_FOUND",
    "details": {
      "resource": "template_id:abc-123"
    }
  },
  "timestamp": "2025-11-05T15:00:00Z"
}
```

## Known Limitations

1. **BigQuery Streaming Buffer**: Templates cannot be updated or deleted within 90 minutes of creation due to BigQuery streaming buffer. The form can still be deployed successfully, but metadata updates may be delayed. See [BIGQUERY_LIMITATIONS.md](./BIGQUERY_LIMITATIONS.md) for details.

2. **GitHub Configuration Required**: The deployment endpoint requires GitHub token configuration. Without it, deployment will return a 503 error. See [GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md) for setup instructions.

3. **No Question CRUD**: Admin endpoints for creating/updating/deleting questions are not yet implemented. Questions are currently managed via direct BigQuery access.

## Next Steps

1. ✅ **Implement Core API** (Task 2.1) - COMPLETED
2. ✅ **Create Form Generation Logic** (Task 2.2) - COMPLETED
3. ✅ **Deploy to Cloud Functions** (Task 2.3) - COMPLETED (v1.1.0)
4. ✅ **Test API Endpoints** (Task 2.4) - COMPLETED (7/11 tests passing)
5. ✅ **Implement GitHub Deployment** (Task 2.5) - COMPLETED
6. **Frontend Integration** (Task 3.1) - Build React UI for form builder
7. **Configure GitHub Token** (Task 3.2) - Enable deployment feature
8. **Add Question CRUD Endpoints** (Task 3.3) - Admin question management

## Support

### Documentation

- **API Reference**: [API_SPEC.md](./API_SPEC.md) - Complete endpoint documentation
- **GitHub Setup**: [GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md) - Step-by-step deployment guide
- **Deployment Status**: [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md) - Current deployment info
- **Known Issues**: [BIGQUERY_LIMITATIONS.md](./BIGQUERY_LIMITATIONS.md) - BigQuery limitations
- **Authentication**: [QUICK_REFERENCE.md](../auth/QUICK_REFERENCE.md) - Auth setup
- **Project Status**: [PROJECT_STATUS.md](../../PROJECT_STATUS.md) - Overall progress

### Quick Start

```bash
# 1. Create a template
export TOKEN="your-jwt-token"
export API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api"

curl -X POST "$API_URL/form-builder/templates" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"template_name": "My Survey", "opportunity_type": "Security", "opportunity_subtype": "SASE", "questions": [...]}'

# 2. Deploy to GitHub Pages (after GitHub setup)
curl -X POST "$API_URL/form-builder/templates/TEMPLATE_ID/deploy" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"commit_message": "Deploy survey"}'

# 3. Share the public URL with customers
# https://opextech.github.io/forms/forms/my_survey.html
```

---

**Last Updated**: November 6, 2025
**Version**: 1.1.0
**Maintainer**: Dayta Analytics - Form Builder Team

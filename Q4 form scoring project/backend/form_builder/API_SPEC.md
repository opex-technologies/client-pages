# Form Builder API Specification

**Version**: 1.0.0
**Created**: November 5, 2025
**Base URL**: `https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api`

## Overview

The Form Builder API enables users to create, manage, and deploy custom survey forms using questions from the Question Database. Forms are generated as standalone HTML files and deployed to GitHub Pages.

## Authentication

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

## Permissions

- **View**: Can list and view form templates
- **Edit**: Can create and update form templates
- **Admin**: Can delete templates and manage questions

---

## Endpoints

### Form Templates

#### List Templates

**GET** `/form-builder/templates`

List all form templates with filtering and pagination.

**Query Parameters**:
- `opportunity_type` (optional) - Filter by opportunity type
- `opportunity_subtype` (optional) - Filter by opportunity subtype
- `status` (optional) - Filter by status (draft, published, archived)
- `created_by` (optional) - Filter by creator user ID
- `page` (optional, default: 1) - Page number
- `page_size` (optional, default: 50) - Items per page

**Response** (200):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "template_id": "tmpl-abc-123",
        "template_name": "SASE Assessment Survey",
        "opportunity_type": "Security",
        "opportunity_subtype": "SASE",
        "status": "published",
        "question_count": 67,
        "created_by": "user-123",
        "created_by_email": "admin@opextech.com",
        "created_at": "2025-11-05T12:00:00Z",
        "updated_at": "2025-11-05T14:30:00Z",
        "deployed_url": "https://opextech.github.io/forms/sase-survey.html",
        "version": 2
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 50,
      "total_count": 15,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

#### Get Template

**GET** `/form-builder/templates/:template_id`

Get a specific form template with full details including questions.

**Response** (200):
```json
{
  "success": true,
  "data": {
    "template_id": "tmpl-abc-123",
    "template_name": "SASE Assessment Survey",
    "opportunity_type": "Security",
    "opportunity_subtype": "SASE",
    "status": "published",
    "description": "Comprehensive SASE assessment form",
    "questions": [
      {
        "question_id": "q-001",
        "question_text": "Do you have a current network security solution?",
        "input_type": "radio",
        "weight": 10,
        "is_required": true,
        "help_text": "Include firewalls, VPNs, and other security tools",
        "sort_order": 1
      }
    ],
    "created_by": "user-123",
    "created_by_email": "admin@opextech.com",
    "created_at": "2025-11-05T12:00:00Z",
    "updated_at": "2025-11-05T14:30:00Z",
    "deployed_url": "https://opextech.github.io/forms/sase-survey.html",
    "deployed_at": "2025-11-05T14:35:00Z",
    "version": 2
  }
}
```

#### Create Template

**POST** `/form-builder/templates`

Create a new form template.

**Request Body**:
```json
{
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
    }
  ]
}
```

**Response** (201):
```json
{
  "success": true,
  "data": {
    "template_id": "tmpl-abc-123",
    "template_name": "SASE Assessment Survey",
    "status": "draft",
    "question_count": 67,
    "created_at": "2025-11-05T12:00:00Z"
  },
  "message": "Template created successfully"
}
```

#### Update Template

**PUT** `/form-builder/templates/:template_id`

Update an existing form template (draft status only).

**Request Body** (partial update supported):
```json
{
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
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "template_id": "tmpl-abc-123",
    "template_name": "Updated SASE Survey",
    "version": 2,
    "updated_at": "2025-11-05T14:30:00Z"
  },
  "message": "Template updated successfully"
}
```

#### Delete Template

**DELETE** `/form-builder/templates/:template_id`

Soft delete a form template (admin only, draft or archived status only).

**Response** (200):
```json
{
  "success": true,
  "message": "Template deleted successfully"
}
```

#### Deploy Template

**POST** `/form-builder/templates/:template_id/deploy`

Generate HTML form and deploy to GitHub Pages.

**Permission**: `edit`

**Request Body** (optional):
```json
{
  "commit_message": "Deploy SASE survey v2"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "template_id": "tmpl-abc-123",
    "deployed_url": "https://opextech.github.io/forms/forms/sase_assessment_survey.html",
    "deployed_at": "2025-11-05T14:35:00Z",
    "deployed_by": "user-123",
    "commit_sha": "abc123def456",
    "file_path": "forms/sase_assessment_survey.html"
  },
  "message": "Template deployed successfully to GitHub Pages"
}
```

**Response with Warning** (200):
```json
{
  "success": true,
  "data": {
    "template_id": "tmpl-abc-123",
    "deployed_url": "https://opextech.github.io/forms/forms/sase_assessment_survey.html",
    "deployed_at": "2025-11-05T14:35:00Z",
    "deployed_by": "user-123",
    "commit_sha": "abc123def456",
    "file_path": "forms/sase_assessment_survey.html",
    "warning": "Template deployed but metadata update delayed (BigQuery streaming buffer)"
  },
  "message": "Template deployed successfully to GitHub Pages"
}
```

**Error Responses**:

- **404 Not Found**: Template doesn't exist
- **503 Service Unavailable**: GitHub not configured (missing GITHUB_TOKEN)
- **500 Internal Server Error**: GitHub API error or deployment failure

**How it Works**:

1. Validates template exists and user has `edit` permission
2. Retrieves template and associated questions from BigQuery
3. Generates HTML form using Jinja2 template
4. Sanitizes template name for filename (e.g., "SASE Assessment" → "sase_assessment.html")
5. Creates or updates file in GitHub repository at `forms/{sanitized_name}.html`
6. Attempts to update template metadata with deployment info
7. Returns deployed URL and commit SHA

**GitHub Configuration** (required environment variables):

- `GITHUB_TOKEN` - GitHub personal access token with repo write permissions
- `GITHUB_REPO_OWNER` - Repository owner (default: "opextech")
- `GITHUB_REPO_NAME` - Repository name (default: "forms")
- `GITHUB_BRANCH` - Target branch (default: "main")

**Note**: If template was recently created (within 90 minutes), the metadata update may fail due to BigQuery streaming buffer limitation. The form will still be deployed successfully, but the template status and deployed_url fields may not update immediately. A warning will be included in the response if this occurs.

### Questions

#### Query Questions

**GET** `/form-builder/questions`

Query the Question Database with filtering.

**Query Parameters**:
- `category` (optional) - Filter by category
- `opportunity_type` (optional) - Filter by opportunity type
- `opportunity_subtype` (optional) - Filter by opportunity subtype
- `search` (optional) - Keyword search in question text
- `template_id` (optional) - Mark questions already in template
- `page` (optional, default: 1)
- `page_size` (optional, default: 100)

**Response** (200):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "question_id": "q-001",
        "question_text": "Do you have a current network security solution?",
        "category": "Network Security",
        "opportunity_type": "Security",
        "opportunity_subtype": "SASE",
        "input_type": "radio",
        "default_weight": 10,
        "help_text": "Include firewalls, VPNs, and other security tools",
        "is_selected": false,
        "is_active": true
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 100,
      "total_count": 1041,
      "total_pages": 11
    }
  }
}
```

#### Get Question

**GET** `/form-builder/questions/:question_id`

Get a specific question with usage statistics.

**Response** (200):
```json
{
  "success": true,
  "data": {
    "question_id": "q-001",
    "question_text": "Do you have a current network security solution?",
    "category": "Network Security",
    "opportunity_type": "Security",
    "opportunity_subtype": "SASE",
    "input_type": "radio",
    "default_weight": 10,
    "help_text": "Include firewalls, VPNs, and other security tools",
    "is_active": true,
    "usage_count": 5,
    "templates_using": [
      {
        "template_id": "tmpl-abc-123",
        "template_name": "SASE Survey"
      }
    ]
  }
}
```

#### Create Question (Admin Only)

**POST** `/form-builder/questions`

Create a new question in the database.

**Request Body**:
```json
{
  "question_text": "Do you have a current network security solution?",
  "category": "Network Security",
  "opportunity_type": "Security",
  "opportunity_subtype": "SASE",
  "input_type": "radio",
  "default_weight": 10,
  "help_text": "Include firewalls, VPNs, and other security tools"
}
```

**Response** (201):
```json
{
  "success": true,
  "data": {
    "question_id": "q-1042",
    "question_text": "Do you have a current network security solution?",
    "created_at": "2025-11-05T15:00:00Z"
  },
  "message": "Question created successfully"
}
```

#### Update Question (Admin Only)

**PUT** `/form-builder/questions/:question_id`

Update an existing question.

**Request Body** (partial update supported):
```json
{
  "question_text": "Updated question text",
  "help_text": "Updated help text"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "question_id": "q-001",
    "version": 2,
    "updated_at": "2025-11-05T15:30:00Z"
  },
  "message": "Question updated successfully"
}
```

#### Delete Question (Admin Only)

**DELETE** `/form-builder/questions/:question_id`

Soft delete a question (sets is_active = false).

**Response** (200):
```json
{
  "success": true,
  "message": "Question deactivated successfully",
  "warning": "Question is used in 3 templates"
}
```

### Form Preview

#### Generate Preview

**POST** `/form-builder/preview`

Generate a preview HTML of a form template without deploying.

**Request Body**:
```json
{
  "template_id": "tmpl-abc-123"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "html": "<html>...</html>",
    "preview_url": "data:text/html;base64,PGh0bWw+Li4uPC9odG1sPg=="
  }
}
```

---

## Error Responses

### 400 Bad Request

```json
{
  "success": false,
  "error": {
    "message": "Invalid request parameters",
    "code": "BAD_REQUEST",
    "details": {
      "template_name": "Template name is required"
    }
  },
  "timestamp": "2025-11-05T15:00:00Z"
}
```

### 401 Unauthorized

```json
{
  "success": false,
  "error": {
    "message": "Invalid or expired token",
    "code": "UNAUTHORIZED"
  },
  "timestamp": "2025-11-05T15:00:00Z"
}
```

### 403 Forbidden

```json
{
  "success": false,
  "error": {
    "message": "Insufficient permissions: requires 'edit' level",
    "code": "FORBIDDEN"
  },
  "timestamp": "2025-11-05T15:00:00Z"
}
```

### 404 Not Found

```json
{
  "success": false,
  "error": {
    "message": "Template not found",
    "code": "NOT_FOUND",
    "details": {
      "resource": "template_id:tmpl-abc-123"
    }
  },
  "timestamp": "2025-11-05T15:00:00Z"
}
```

### 409 Conflict

```json
{
  "success": false,
  "error": {
    "message": "Template with this name already exists",
    "code": "CONFLICT",
    "details": {
      "template_name": "SASE Survey"
    }
  },
  "timestamp": "2025-11-05T15:00:00Z"
}
```

---

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
  questions: TemplateQuestion[]
  created_by: string (user_id)
  created_at: timestamp
  updated_at: timestamp | null
  updated_by: string | null
  deployed_url: string | null
  deployed_at: timestamp | null
  version: integer
}
```

### Template Question

```typescript
{
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
  created_at: timestamp
  updated_at: timestamp | null
  version: integer
}
```

---

## Permission Matrix

| Endpoint | View | Edit | Admin |
|----------|------|------|-------|
| GET /templates | ✓ | ✓ | ✓ |
| GET /templates/:id | ✓ | ✓ | ✓ |
| POST /templates | ✗ | ✓ | ✓ |
| PUT /templates/:id | ✗ | ✓ | ✓ |
| DELETE /templates/:id | ✗ | ✗ | ✓ |
| POST /templates/:id/deploy | ✗ | ✓ | ✓ |
| GET /questions | ✓ | ✓ | ✓ |
| GET /questions/:id | ✓ | ✓ | ✓ |
| POST /questions | ✗ | ✗ | ✓ |
| PUT /questions/:id | ✗ | ✗ | ✓ |
| DELETE /questions/:id | ✗ | ✗ | ✓ |
| POST /preview | ✓ | ✓ | ✓ |

---

## Rate Limits

- **General**: 100 requests/minute per user
- **Deploy**: 10 requests/hour per template
- **Question CRUD**: 50 requests/minute (admin only)

---

**Last Updated**: November 5, 2025
**Maintainer**: Dayta Analytics - Form Builder Team

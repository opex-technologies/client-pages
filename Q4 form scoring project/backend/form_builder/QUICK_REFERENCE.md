# Form Builder API - Quick Reference

**Version**: 1.1.0 | **Base URL**: `https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api`

## 🔑 Authentication

All endpoints require JWT token:
```bash
-H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📋 Endpoints Cheat Sheet

### Templates

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/form-builder/templates` | edit | Create template |
| GET | `/form-builder/templates` | view | List templates |
| GET | `/form-builder/templates/:id` | view | Get template |
| PUT | `/form-builder/templates/:id` | edit | Update template |
| DELETE | `/form-builder/templates/:id` | admin | Delete template |
| POST | `/form-builder/templates/:id/deploy` | edit | Deploy to GitHub |

### Questions

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/form-builder/questions` | view | Query questions |
| GET | `/form-builder/questions/:id` | view | Get question |

### Preview

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/form-builder/preview` | view | Generate HTML |

---

## 🚀 Quick Start

### 1. Create a Template

```bash
curl -X POST "$API_URL/form-builder/templates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "SASE Assessment",
    "opportunity_type": "Security",
    "opportunity_subtype": "SASE",
    "questions": [
      {"question_id": "q-001", "weight": 10, "is_required": true, "sort_order": 1}
    ]
  }'
```

**Response**: Returns `template_id`

### 2. Deploy to GitHub Pages

```bash
curl -X POST "$API_URL/form-builder/templates/TEMPLATE_ID/deploy" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"commit_message": "Deploy form"}'
```

**Response**: Returns `deployed_url`

---

## 📝 Common Operations

### List All Templates

```bash
curl "$API_URL/form-builder/templates" \
  -H "Authorization: Bearer $TOKEN"
```

### Filter Templates by Type

```bash
curl "$API_URL/form-builder/templates?opportunity_type=Security&status=published" \
  -H "Authorization: Bearer $TOKEN"
```

### Search Questions

```bash
curl "$API_URL/form-builder/questions?search=firewall&opportunity_subtype=SASE" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Template with Questions

```bash
curl "$API_URL/form-builder/templates/TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### Preview Form HTML

```bash
curl -X POST "$API_URL/form-builder/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"template_id": "TEMPLATE_ID"}' \
  | jq -r '.data.html' > preview.html
```

### Update Template

```bash
curl -X PUT "$API_URL/form-builder/templates/TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "template_name": "Updated Name",
    "questions": [...]
  }'
```

**⚠️ Note**: Cannot update within 90 minutes of creation (BigQuery limitation)

### Delete Template

```bash
curl -X DELETE "$API_URL/form-builder/templates/TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**⚠️ Note**: Cannot delete within 90 minutes of creation (BigQuery limitation)

---

## 🔍 Query Parameters

### Templates

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `opportunity_type` | string | Filter by type | `Security` |
| `opportunity_subtype` | string | Filter by subtype | `SASE` |
| `status` | string | Filter by status | `draft`, `published` |
| `created_by` | string | Filter by creator | `user-123` |
| `page` | integer | Page number | `1` |
| `page_size` | integer | Items per page | `50` |

### Questions

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `category` | string | Filter by category | `Security` |
| `opportunity_type` | string | Filter by type | `Security` |
| `opportunity_subtype` | string | Filter by subtype | `SASE` |
| `search` | string | Keyword search | `firewall` |
| `template_id` | string | Mark selected | `abc-123` |
| `page` | integer | Page number | `1` |
| `page_size` | integer | Items per page | `100` |

---

## 💡 Request Body Examples

### Create Template

```json
{
  "template_name": "SASE Assessment Survey",
  "opportunity_type": "Security",
  "opportunity_subtype": "SASE",
  "description": "Comprehensive SASE assessment",
  "questions": [
    {
      "question_id": "bf525059-8543-4316-9580-dd5e36eee15d",
      "weight": 10,
      "is_required": true,
      "sort_order": 1
    },
    {
      "question_id": "121c344e-8ff0-42da-a3fc-1210dd0f23d0",
      "weight": "Info",
      "is_required": false,
      "sort_order": 2
    }
  ]
}
```

### Update Template (Partial)

```json
{
  "template_name": "Updated Name"
}
```

### Deploy Template

```json
{
  "commit_message": "Deploy SASE assessment v2"
}
```

---

## ✅ Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "timestamp": "2025-11-06T12:00:00Z"
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "message": "Template not found",
    "code": "NOT_FOUND",
    "details": {}
  },
  "timestamp": "2025-11-06T12:00:00Z"
}
```

---

## 🎨 Special Features

### "Info" Weight

Use `"weight": "Info"` for informational questions (no scoring):
- Stored as `NULL` in BigQuery
- Returned as `null` in API responses
- Excluded from scoring calculations

### Pagination

All list endpoints return:
```json
{
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "page_size": 50,
      "total_count": 150,
      "total_pages": 3,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### Selected Questions

When querying questions with `template_id`, selected questions are marked:
```json
{
  "question_id": "q-001",
  "is_selected": true,
  "selected_weight": 10,
  "selected_required": true
}
```

---

## 🔧 Configuration

### Environment Variables

```bash
PROJECT_ID=opex-data-lake-k23k4y98m
DATASET_ID=form_builder
JWT_SECRET_KEY=***
GITHUB_TOKEN=***                    # Optional, for deployment
GITHUB_REPO_OWNER=opextech
GITHUB_REPO_NAME=forms
GITHUB_BRANCH=main
```

### GitHub Setup (for deployment)

1. Create GitHub repository (public)
2. Enable GitHub Pages (Settings → Pages)
3. Generate personal access token (repo scope)
4. Set `GITHUB_TOKEN` environment variable
5. Deploy Cloud Function with GitHub config

See [GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md) for details.

---

## ⚠️ Known Limitations

### BigQuery Streaming Buffer

**Issue**: Cannot UPDATE or DELETE templates within 90 minutes of creation

**Workaround**:
- Wait 90 minutes before updating/deleting
- Or migrate to Firestore (see BIGQUERY_LIMITATIONS.md)

**Forms can still be deployed immediately** - only metadata updates are delayed.

### GitHub Configuration

Deployment endpoint returns error without GitHub token:
```json
{
  "error": {
    "code": "CONFIGURATION_ERROR",
    "message": "GitHub deployment not configured (missing GITHUB_TOKEN)"
  }
}
```

---

## 📊 Common HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | Success | Request completed |
| 201 | Created | Template created |
| 400 | Bad Request | Invalid JSON, missing fields |
| 401 | Unauthorized | Invalid/missing token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Template/question doesn't exist |
| 500 | Internal Error | BigQuery/GitHub API error |
| 503 | Service Unavailable | GitHub not configured |

---

## 🧪 Testing

```bash
# Set environment
export TOKEN="your-jwt-token"
export API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api"

# Run comprehensive tests
cd backend/form_builder
./test_api.sh

# Or test individual endpoints
curl "$API_URL/form-builder/questions?page_size=5" -H "Authorization: Bearer $TOKEN"
```

---

## 📚 Documentation

- **Complete API Spec**: [API_SPEC.md](./API_SPEC.md)
- **GitHub Setup**: [GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md)
- **Usage Guide**: [README.md](./README.md)
- **Deployment Info**: [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)
- **Known Issues**: [BIGQUERY_LIMITATIONS.md](./BIGQUERY_LIMITATIONS.md)

---

## 🆘 Troubleshooting

### "Invalid token"
- Check token expiration (24 hours)
- Verify `Authorization: Bearer TOKEN` header format
- Get new token from auth API

### "Permission denied"
- Check user has required permission (view/edit/admin)
- Use permission API to grant permissions

### "Template not found"
- Verify template_id is correct
- Check template wasn't deleted

### "Cannot update template"
- Wait 90 minutes after creation (BigQuery limitation)
- Or create new template version instead

### "GitHub deployment not configured"
- Set `GITHUB_TOKEN` environment variable
- See [GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md)

---

**Quick Links**:
- API URL: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
- Current Version: 1.1.0
- Last Updated: November 6, 2025

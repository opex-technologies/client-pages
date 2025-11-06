# Form Builder API - Testing Checklist

**Version**: 1.1.0
**Last Updated**: November 6, 2025
**Purpose**: QA validation and acceptance testing

---

## 🎯 Overview

This checklist ensures all Form Builder API functionality is working correctly. Use this for:
- Post-deployment validation
- Release testing
- Regression testing
- Frontend integration testing

---

## ✅ Pre-Testing Setup

### Environment Setup
- [ ] API URL confirmed: `https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api`
- [ ] Valid JWT token obtained
- [ ] Test user has appropriate permissions (view, edit, or admin)
- [ ] Tools installed: `curl`, `jq` (optional)

### Test Data Preparation
- [ ] Know question IDs for testing (use `/form-builder/questions` endpoint)
- [ ] Have test opportunity types: `Security`, `Network`, `Cloud`
- [ ] Have test opportunity subtypes: `SASE`, `SD-WAN`, `UCaaS`

### Set Environment Variables
```bash
export TOKEN="your-jwt-token-here"
export API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api"
```

---

## 📋 API Endpoint Tests

### 1. Question Endpoints

#### 1.1 Query Questions
- [ ] **Test**: Get all questions (first page)
  ```bash
  curl "$API_URL/form-builder/questions?page_size=10" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns 200 status
  - [ ] Response contains `items` array
  - [ ] Response contains `pagination` object
  - [ ] Items have required fields: `question_id`, `question_text`, `input_type`

#### 1.2 Filter Questions by Opportunity Type
- [ ] **Test**: Filter by `opportunity_type=Security`
  ```bash
  curl "$API_URL/form-builder/questions?opportunity_type=Security&page_size=5" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns only Security questions
  - [ ] All items have `opportunity_type: "Security"`

#### 1.3 Filter Questions by Opportunity Subtype
- [ ] **Test**: Filter by `opportunity_subtype=SASE`
  ```bash
  curl "$API_URL/form-builder/questions?opportunity_subtype=SASE&page_size=5" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns only SASE questions
  - [ ] All items have `opportunity_subtype: "SASE"`

#### 1.4 Search Questions by Keyword
- [ ] **Test**: Search for "firewall"
  ```bash
  curl "$API_URL/form-builder/questions?search=firewall&page_size=5" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns questions containing "firewall" in text
  - [ ] Returns relevant results

#### 1.5 Get Specific Question
- [ ] **Test**: Get question by ID
  ```bash
  curl "$API_URL/form-builder/questions/QUESTION_ID" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns 200 status
  - [ ] Returns single question object
  - [ ] Includes `usage_count` field
  - [ ] Includes `templates` array (if used)

#### 1.6 Pagination
- [ ] **Test**: Request page 2
  ```bash
  curl "$API_URL/form-builder/questions?page=2&page_size=10" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns second page of results
  - [ ] `pagination.page` is 2
  - [ ] `pagination.has_prev` is true

---

### 2. Template Endpoints

#### 2.1 Create Template
- [ ] **Test**: Create new template
  ```bash
  curl -X POST "$API_URL/form-builder/templates" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "template_name": "Test Template",
      "opportunity_type": "Security",
      "opportunity_subtype": "SASE",
      "description": "Test description",
      "questions": [
        {"question_id": "VALID_QUESTION_ID", "weight": 10, "is_required": true, "sort_order": 1}
      ]
    }'
  ```
  - [ ] Returns 201 status
  - [ ] Response includes `template_id`
  - [ ] Template has `status: "draft"`
  - [ ] Save `template_id` for subsequent tests

#### 2.2 Create Template with "Info" Weight
- [ ] **Test**: Create template with Info question
  ```bash
  curl -X POST "$API_URL/form-builder/templates" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "template_name": "Template with Info",
      "opportunity_type": "Security",
      "opportunity_subtype": "SASE",
      "questions": [
        {"question_id": "VALID_QUESTION_ID", "weight": "Info", "is_required": false, "sort_order": 1}
      ]
    }'
  ```
  - [ ] Returns 201 status
  - [ ] Question weight stored as NULL in database
  - [ ] Retrieved weight returns as `null` (not "Info")

#### 2.3 List All Templates
- [ ] **Test**: Get all templates
  ```bash
  curl "$API_URL/form-builder/templates" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns 200 status
  - [ ] Response contains templates created above
  - [ ] Each template has required fields

#### 2.4 Filter Templates by Status
- [ ] **Test**: Filter by `status=draft`
  ```bash
  curl "$API_URL/form-builder/templates?status=draft" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns only draft templates
  - [ ] All items have `status: "draft"`

#### 2.5 Filter Templates by Opportunity Type
- [ ] **Test**: Filter by `opportunity_type=Security`
  ```bash
  curl "$API_URL/form-builder/templates?opportunity_type=Security" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns only Security templates

#### 2.6 Get Specific Template
- [ ] **Test**: Get template by ID (use ID from 2.1)
  ```bash
  curl "$API_URL/form-builder/templates/TEMPLATE_ID" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns 200 status
  - [ ] Includes `questions` array with full question details
  - [ ] Questions include `weight`, `is_required`, `sort_order`
  - [ ] Questions are sorted by `sort_order`

#### 2.7 Update Template (after 90 minutes)
⚠️ **Note**: This test will fail if template was created within 90 minutes (BigQuery limitation)

- [ ] **Test**: Update template name
  ```bash
  curl -X PUT "$API_URL/form-builder/templates/TEMPLATE_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"template_name": "Updated Template Name"}'
  ```
  - [ ] Returns 200 status (if > 90 min old)
  - [ ] OR returns error about streaming buffer (if < 90 min)
  - [ ] Template name updated if successful

#### 2.8 Delete Template (admin only, after 90 minutes)
⚠️ **Note**: Requires admin permission. Will fail if < 90 minutes old.

- [ ] **Test**: Delete template
  ```bash
  curl -X DELETE "$API_URL/form-builder/templates/TEMPLATE_ID" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns 200 status (if admin and > 90 min)
  - [ ] OR returns 403 if not admin
  - [ ] OR returns error about streaming buffer (if < 90 min)

---

### 3. Preview Endpoint

#### 3.1 Generate Preview
- [ ] **Test**: Generate HTML preview
  ```bash
  curl -X POST "$API_URL/form-builder/preview" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"template_id": "TEMPLATE_ID"}'
  ```
  - [ ] Returns 200 status
  - [ ] Response contains `html` field
  - [ ] HTML is valid (contains `<!DOCTYPE html>`)
  - [ ] HTML includes template name
  - [ ] HTML includes all questions
  - [ ] Save HTML to file and verify it opens in browser

#### 3.2 Preview with "Info" Questions
- [ ] **Test**: Preview template with Info weight questions
  - [ ] Info questions appear in HTML
  - [ ] Info questions show no weight/scoring indicator
  - [ ] Info questions can be optional

---

### 4. Deployment Endpoint

#### 4.1 Deploy Template (requires GitHub configuration)
⚠️ **Note**: Requires `GITHUB_TOKEN` to be set in Cloud Function

- [ ] **Test**: Deploy template to GitHub
  ```bash
  curl -X POST "$API_URL/form-builder/templates/TEMPLATE_ID/deploy" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"commit_message": "Test deployment"}'
  ```
  - [ ] Returns 200 status (if GitHub configured)
  - [ ] OR returns 503 Service Unavailable (if not configured)
  - [ ] Response includes `deployed_url`
  - [ ] Response includes `commit_sha`
  - [ ] Response includes `file_path`
  - [ ] Visit `deployed_url` after 1-2 minutes and verify form loads

#### 4.2 Deploy Without Commit Message
- [ ] **Test**: Deploy with default commit message
  ```bash
  curl -X POST "$API_URL/form-builder/templates/TEMPLATE_ID/deploy" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{}'
  ```
  - [ ] Uses default commit message
  - [ ] Deployment succeeds

#### 4.3 Redeploy Template
- [ ] **Test**: Deploy same template again
  - [ ] Updates existing file in GitHub
  - [ ] Returns new commit SHA
  - [ ] Form updates on GitHub Pages (after rebuild)

---

## 🔒 Authentication & Authorization Tests

### 5.1 Missing Token
- [ ] **Test**: Request without Authorization header
  ```bash
  curl "$API_URL/form-builder/templates"
  ```
  - [ ] Returns 401 Unauthorized
  - [ ] Error message indicates missing authentication

### 5.2 Invalid Token
- [ ] **Test**: Request with invalid token
  ```bash
  curl "$API_URL/form-builder/templates" -H "Authorization: Bearer invalid_token"
  ```
  - [ ] Returns 401 Unauthorized
  - [ ] Error message indicates invalid token

### 5.3 Insufficient Permissions
- [ ] **Test**: Delete template without admin permission
  ```bash
  curl -X DELETE "$API_URL/form-builder/templates/TEMPLATE_ID" -H "Authorization: Bearer $NON_ADMIN_TOKEN"
  ```
  - [ ] Returns 403 Forbidden
  - [ ] Error message indicates insufficient permissions

---

## ⚠️ Error Handling Tests

### 6.1 Invalid Template ID
- [ ] **Test**: Get non-existent template
  ```bash
  curl "$API_URL/form-builder/templates/invalid-id" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns 404 Not Found
  - [ ] Error message is clear

### 6.2 Invalid Question ID
- [ ] **Test**: Create template with invalid question ID
  ```bash
  curl -X POST "$API_URL/form-builder/templates" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"template_name": "Test", "opportunity_type": "Security", "opportunity_subtype": "SASE", "questions": [{"question_id": "invalid", "weight": 10, "is_required": true, "sort_order": 1}]}'
  ```
  - [ ] Returns 400 Bad Request OR creates template (depends on validation)
  - [ ] If created, question won't join properly

### 6.3 Missing Required Fields
- [ ] **Test**: Create template without required fields
  ```bash
  curl -X POST "$API_URL/form-builder/templates" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"template_name": "Test"}'
  ```
  - [ ] Returns 400 Bad Request
  - [ ] Error indicates missing fields

### 6.4 Invalid JSON
- [ ] **Test**: Send malformed JSON
  ```bash
  curl -X POST "$API_URL/form-builder/templates" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{invalid json}'
  ```
  - [ ] Returns 400 Bad Request
  - [ ] Error indicates JSON parse error

---

## 🔄 Pagination Tests

### 7.1 First Page
- [ ] **Test**: Get first page
  ```bash
  curl "$API_URL/form-builder/questions?page=1&page_size=10" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] `pagination.page` is 1
  - [ ] `pagination.has_prev` is false
  - [ ] `pagination.has_next` is true (if more than 10 questions exist)

### 7.2 Last Page
- [ ] **Test**: Get last page
  ```bash
  curl "$API_URL/form-builder/questions?page=999&page_size=10" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns last page (not error)
  - [ ] `pagination.has_next` is false
  - [ ] Items array may be smaller than page_size

### 7.3 Custom Page Size
- [ ] **Test**: Request 50 items per page
  ```bash
  curl "$API_URL/form-builder/questions?page_size=50" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Returns up to 50 items
  - [ ] `pagination.page_size` is 50

---

## 🎨 Special Feature Tests

### 8.1 "Info" Weight Handling
- [ ] **Test**: Create template with "Info" weight
  - [ ] Weight "Info" accepted in request
  - [ ] Stored as NULL in database
  - [ ] Returned as `null` (not "Info") in response
  - [ ] Displays correctly in preview

### 8.2 Question Selection Marking
- [ ] **Test**: Query questions with template_id filter
  ```bash
  curl "$API_URL/form-builder/questions?template_id=TEMPLATE_ID&opportunity_subtype=SASE" -H "Authorization: Bearer $TOKEN"
  ```
  - [ ] Questions in template have `is_selected: true`
  - [ ] Questions in template show `selected_weight`
  - [ ] Questions in template show `selected_required`
  - [ ] Questions not in template have `is_selected: false`

### 8.3 Question Ordering
- [ ] **Test**: Get template with multiple questions
  - [ ] Questions sorted by `sort_order` ascending
  - [ ] Order matches what was specified in creation

### 8.4 Template Status Workflow
- [ ] **Test**: Template lifecycle
  - [ ] New templates have `status: "draft"`
  - [ ] Deployed templates update to `status: "published"` (if metadata update succeeds)
  - [ ] Can filter templates by status

---

## 📊 Performance Tests

### 9.1 Response Time
- [ ] List templates responds in < 500ms
- [ ] Get template responds in < 500ms
- [ ] Query questions responds in < 500ms
- [ ] Create template responds in < 1000ms
- [ ] Generate preview responds in < 1000ms
- [ ] Deploy template responds in < 5000ms

### 9.2 Large Result Sets
- [ ] Query all questions (1,041+ questions) with pagination works
- [ ] Page size up to 100 works without timeout
- [ ] Template with 100+ questions works

---

## 🔍 Data Integrity Tests

### 10.1 Template-Question Association
- [ ] Questions added to template appear in GET /templates/:id
- [ ] Question details are complete (not just IDs)
- [ ] Weight, required, and sort_order are preserved

### 10.2 Concurrent Operations
- [ ] Create multiple templates simultaneously
- [ ] Deploy multiple templates simultaneously
- [ ] No data corruption or conflicts

### 10.3 Data Validation
- [ ] Weight must be number or "Info"
- [ ] Sort order must be positive integer
- [ ] Question IDs must be valid UUIDs

---

## 📝 Documentation Tests

### 11.1 API Responses Match Documentation
- [ ] Response structure matches API_SPEC.md
- [ ] Field names are correct
- [ ] Data types are correct
- [ ] Error codes match documentation

### 11.2 Examples Work
- [ ] Examples in QUICK_REFERENCE.md work
- [ ] Examples in API_SPEC.md work
- [ ] deploy_example.sh script works

---

## 🚀 Integration Tests

### 12.1 Complete Workflow
- [ ] **Test**: Full template creation to deployment
  1. [ ] Query questions
  2. [ ] Create template with selected questions
  3. [ ] Get template to verify
  4. [ ] Generate preview
  5. [ ] Deploy to GitHub
  6. [ ] Verify form on GitHub Pages
  - [ ] All steps complete successfully
  - [ ] Form is publicly accessible
  - [ ] Form includes all questions
  - [ ] Form functions correctly (validation, submission)

### 12.2 Template Management Workflow
- [ ] **Test**: CRUD operations
  1. [ ] Create template
  2. [ ] List and find template
  3. [ ] Get template details
  4. [ ] Update template (after 90 min)
  5. [ ] Delete template (after 90 min)

---

## 🐛 Known Issues Verification

### 13.1 BigQuery Streaming Buffer
- [ ] **Verify**: Cannot update template within 90 minutes
  - [ ] Update within 90 min returns appropriate error
  - [ ] Error message mentions streaming buffer
  - [ ] Update after 90 min succeeds

- [ ] **Verify**: Cannot delete template within 90 minutes
  - [ ] Delete within 90 min returns appropriate error
  - [ ] Error message mentions streaming buffer
  - [ ] Delete after 90 min succeeds

### 13.2 GitHub Configuration
- [ ] **Verify**: Deploy fails gracefully without GitHub token
  - [ ] Returns 503 Service Unavailable
  - [ ] Error message mentions GitHub configuration
  - [ ] Suggests checking GITHUB_TOKEN

- [ ] **Verify**: Deploy works with GitHub token
  - [ ] Returns 200 with deployed_url
  - [ ] File appears in GitHub repository
  - [ ] Form accessible on GitHub Pages

---

## ✅ Test Summary

### Test Results
- **Total Tests**: ___ / 100+
- **Passed**: ___
- **Failed**: ___
- **Skipped**: ___

### Critical Issues Found
1. ___
2. ___
3. ___

### Minor Issues Found
1. ___
2. ___
3. ___

### Recommendations
1. ___
2. ___
3. ___

---

## 📅 Sign-Off

**Tester Name**: _______________
**Date**: _______________
**Version Tested**: 1.1.0
**Environment**: Production / Staging / Development

**Approved for**:
- [ ] Frontend Integration
- [ ] Production Deployment
- [ ] User Acceptance Testing

**Notes**:
_______________________________________________
_______________________________________________
_______________________________________________

---

## 🔧 Automated Testing Script

Save this as `run_tests.sh` for automated testing:

```bash
#!/bin/bash

# Form Builder API Test Suite
# Run all API tests automatically

set -e

# Configuration
API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api"
TOKEN="${TOKEN:-}"

# Check prerequisites
if [ -z "$TOKEN" ]; then
    echo "Error: TOKEN environment variable not set"
    echo "Usage: export TOKEN='your-jwt-token' && ./run_tests.sh"
    exit 1
fi

echo "🧪 Starting Form Builder API Tests..."
echo ""

# Test counters
TOTAL=0
PASSED=0
FAILED=0

# Helper function to run test
run_test() {
    local test_name="$1"
    local command="$2"

    TOTAL=$((TOTAL + 1))
    echo -n "Test $TOTAL: $test_name... "

    if eval "$command" > /dev/null 2>&1; then
        echo "✅ PASSED"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAILED"
        FAILED=$((FAILED + 1))
    fi
}

# Run tests
echo "📋 Testing Question Endpoints..."
run_test "Query all questions" "curl -f '$API_URL/form-builder/questions?page_size=5' -H 'Authorization: Bearer $TOKEN'"
run_test "Filter by opportunity type" "curl -f '$API_URL/form-builder/questions?opportunity_type=Security' -H 'Authorization: Bearer $TOKEN'"
run_test "Search questions" "curl -f '$API_URL/form-builder/questions?search=firewall' -H 'Authorization: Bearer $TOKEN'"

echo ""
echo "📝 Testing Template Endpoints..."
run_test "List templates" "curl -f '$API_URL/form-builder/templates' -H 'Authorization: Bearer $TOKEN'"
run_test "Filter templates" "curl -f '$API_URL/form-builder/templates?status=draft' -H 'Authorization: Bearer $TOKEN'"

echo ""
echo "🎨 Testing Preview Endpoint..."
# Note: Requires valid template_id
# run_test "Generate preview" "curl -f -X POST '$API_URL/form-builder/preview' -H 'Authorization: Bearer $TOKEN' -d '{\"template_id\":\"...\"}'"

echo ""
echo "📊 Test Results"
echo "==============="
echo "Total: $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
```

---

**Last Updated**: November 6, 2025
**Version**: 1.1.0

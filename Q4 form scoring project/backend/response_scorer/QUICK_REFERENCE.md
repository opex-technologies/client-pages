# Response Scorer API - Quick Reference

**Version**: 1.0.0
**Status**: Complete ✅
**Base URL**: `https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/response-scorer-api`

## Overview

The Response Scorer API handles form response submissions, automatic scoring, and analytics. It provides endpoints for submitting responses (public), managing responses (authenticated), and viewing analytics.

---

## Endpoints

### 1. Submit Response (PUBLIC)

**POST** `/responses/submit`

Submit a form response and receive automatic scoring.

**Authentication**: None (public endpoint)

**Request Body**:
```json
{
  "template_id": "550e8400-e29b-41d4-a716-446655440000",
  "submitter_email": "john.doe@example.com",
  "submitter_name": "John Doe",
  "answers": {
    "Q001": "Yes, we have a firewall",
    "Q002": "50",
    "Q003": "Cisco Meraki"
  }
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "response_id": "abc-123-def-456",
    "total_score": 85.0,
    "max_possible_score": 100.0,
    "score_percentage": 85.0,
    "completion_percentage": 90.5,
    "submitted_at": "2025-11-06T12:34:56.789Z"
  },
  "message": "Response submitted and scored successfully"
}
```

---

### 2. List Responses

**GET** `/responses`

List all responses with optional filtering and pagination.

**Authentication**: Required (Bearer token)

**Query Parameters**:
- `template_id` (optional): Filter by template
- `opportunity_type` (optional): Filter by opportunity type
- `submitter_email` (optional): Filter by submitter
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 50, max: 100): Items per page

**Example**:
```bash
curl "$API_URL/responses?template_id=550e8400&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "response_id": "abc-123",
        "template_id": "550e8400",
        "template_name": "Network SASE Assessment",
        "opportunity_type": "Network",
        "opportunity_subtype": "SASE",
        "submitter_email": "john@example.com",
        "submitter_name": "John Doe",
        "total_score": 85.0,
        "max_possible_score": 100.0,
        "score_percentage": 85.0,
        "total_questions": 44,
        "answered_questions": 42,
        "completion_percentage": 95.5,
        "submitted_at": "2025-11-06T12:34:56Z",
        "created_at": "2025-11-06T12:34:56Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_count": 156,
      "total_pages": 8
    }
  }
}
```

---

### 3. Get Response Details

**GET** `/responses/:id`

Get detailed information about a specific response, including all answers and scoring breakdown.

**Authentication**: Required (Bearer token)

**Example**:
```bash
curl "$API_URL/responses/abc-123-def-456" \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "response_id": "abc-123",
    "template_id": "550e8400",
    "template_name": "Network SASE Assessment",
    "opportunity_type": "Network",
    "opportunity_subtype": "SASE",
    "submitter_email": "john@example.com",
    "submitter_name": "John Doe",
    "total_score": 85.0,
    "max_possible_score": 100.0,
    "score_percentage": 85.0,
    "total_questions": 44,
    "answered_questions": 42,
    "completion_percentage": 95.5,
    "submitted_at": "2025-11-06T12:34:56Z",
    "created_at": "2025-11-06T12:34:56Z",
    "answers": [
      {
        "answer_id": "ans-001",
        "question_id": "Q001",
        "question_text": "Do you have a firewall?",
        "answer_value": "Yes",
        "points_earned": 10.0,
        "points_possible": 10.0,
        "created_at": "2025-11-06T12:34:56Z"
      },
      {
        "answer_id": "ans-002",
        "question_id": "Q002",
        "question_text": "How many employees?",
        "answer_value": "50",
        "points_earned": 0.0,
        "points_possible": 0.0,
        "created_at": "2025-11-06T12:34:56Z"
      }
    ]
  }
}
```

---

### 4. Delete Response

**DELETE** `/responses/:id`

Delete a response and all its answers (admin only).

**Authentication**: Required (Bearer token with admin permission)

**Example**:
```bash
curl -X DELETE "$API_URL/responses/abc-123-def-456" \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Response abc-123-def-456 deleted successfully"
}
```

---

### 5. Get Analytics Summary

**GET** `/analytics/summary`

Get overall analytics including response statistics and breakdowns.

**Authentication**: Required (Bearer token)

**Example**:
```bash
curl "$API_URL/analytics/summary" \
  -H "Authorization: Bearer $TOKEN"
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_responses": 156,
      "avg_score_percentage": 78.5,
      "avg_completion_percentage": 92.3,
      "min_score": 45.0,
      "max_score": 98.5,
      "unique_templates": 8,
      "unique_submitters": 89
    },
    "by_template": [
      {
        "template_name": "Network SASE Assessment",
        "response_count": 45,
        "avg_score": 82.3
      },
      {
        "template_name": "Security MDR Assessment",
        "response_count": 38,
        "avg_score": 75.8
      }
    ],
    "by_opportunity_type": [
      {
        "opportunity_type": "Network",
        "response_count": 78,
        "avg_score": 79.2
      },
      {
        "opportunity_type": "Security",
        "response_count": 56,
        "avg_score": 77.1
      }
    ]
  }
}
```

---

## Scoring Algorithm

The scoring algorithm works as follows:

1. **Iterate through all template questions**
   - Get each question's weight (points possible)
   - Check if question was answered

2. **Calculate points per question**
   - If question has a weight AND is answered: points_earned = weight
   - If question has a weight but NOT answered: points_earned = 0
   - If question has no weight (Info question): does not contribute to score

3. **Calculate totals**
   - total_score = sum of all points_earned
   - max_possible_score = sum of all weights for scoring questions
   - score_percentage = (total_score / max_possible_score) × 100

4. **Calculate completion**
   - answered_questions = count of questions with answers
   - total_questions = count of all questions
   - completion_percentage = (answered_questions / total_questions) × 100

**Example**:
```
Template has 5 questions:
- Q1: Weight 10, answered "Yes" → 10 points earned
- Q2: Weight 15, answered "No" → 15 points earned
- Q3: Weight 10, NOT answered → 0 points earned
- Q4: Info (no weight), answered → 0 points (doesn't count)
- Q5: Weight 20, answered "Yes" → 20 points earned

Results:
- total_score = 45
- max_possible_score = 55 (10 + 15 + 10 + 20)
- score_percentage = 81.8%
- answered_questions = 4
- total_questions = 5
- completion_percentage = 80%
```

---

## Authentication

All endpoints except `/responses/submit` require JWT authentication:

```bash
# Get token first
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "your-password"}'

# Use token
export TOKEN="eyJhbGc..."

curl "$API_URL/responses" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "message": "Human-readable error message",
    "code": "ERROR_CODE",
    "details": {
      "additional": "information"
    }
  },
  "timestamp": "2025-11-06T12:34:56.789Z"
}
```

**Common Error Codes**:
- `VALIDATION_ERROR` (400): Invalid request data
- `UNAUTHORIZED` (401): Missing or invalid authentication
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `INTERNAL_ERROR` (500): Server error

---

## Quick Start

### Submit a Response

```bash
# Set API URL
export API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/response-scorer-api"

# Submit response (no auth required)
curl -X POST "$API_URL/responses/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "your-template-id",
    "submitter_email": "user@example.com",
    "submitter_name": "John Doe",
    "answers": {
      "Q001": "Answer to question 1",
      "Q002": "Answer to question 2"
    }
  }'
```

### View Responses

```bash
# Get auth token
export TOKEN="your-jwt-token"

# List all responses
curl "$API_URL/responses" \
  -H "Authorization: Bearer $TOKEN"

# Get specific response
curl "$API_URL/responses/abc-123-def-456" \
  -H "Authorization: Bearer $TOKEN"

# View analytics
curl "$API_URL/analytics/summary" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Database Schema

### responses table
- `response_id` (STRING): Unique response identifier
- `template_id` (STRING): Template used for response
- `template_name` (STRING): Template name
- `opportunity_type` (STRING): Opportunity type
- `opportunity_subtype` (STRING): Opportunity subtype
- `submitter_email` (STRING): Submitter email
- `submitter_name` (STRING): Submitter name
- `total_score` (FLOAT): Total points earned
- `max_possible_score` (FLOAT): Maximum possible points
- `score_percentage` (FLOAT): Score as percentage
- `total_questions` (INTEGER): Total questions in template
- `answered_questions` (INTEGER): Number of questions answered
- `completion_percentage` (FLOAT): Completion percentage
- `submitted_at` (TIMESTAMP): Submission timestamp
- `created_at` (TIMESTAMP): Record creation timestamp

### response_answers table
- `answer_id` (STRING): Unique answer identifier
- `response_id` (STRING): Parent response ID
- `question_id` (STRING): Question identifier
- `question_text` (STRING): Full question text
- `answer_value` (STRING): Answer provided
- `points_earned` (FLOAT): Points earned for this answer
- `points_possible` (FLOAT): Maximum points for this question
- `created_at` (TIMESTAMP): Record creation timestamp

---

## Support

For issues or questions, contact the development team or refer to the full API documentation.

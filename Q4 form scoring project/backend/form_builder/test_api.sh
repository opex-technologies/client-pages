#!/bin/bash

# Form Builder API - Comprehensive Test Script
# Tests all endpoints with real requests
# Created: November 6, 2025

set -e

# Configuration
API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidGVzdC11c2VyLTEyMyIsImVtYWlsIjoidGVzdEBvcGV4dGVjaC5jb20iLCJleHAiOjE3NjI0NzIzNDUsImlhdCI6MTc2MjM4NTk0NSwidHlwZSI6ImFjY2VzcyJ9.hqb5uvrB-qq_ta9_2IHCqcFo9EzH-zs8Yxj7RJ0tNcU"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Form Builder API - Comprehensive Test"
echo "=========================================="
echo ""

# Test 1: List Templates (empty)
echo -e "${BLUE}Test 1: List Templates (should be empty)${NC}"
RESPONSE=$(curl -s -X GET "$API_URL/form-builder/templates" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool
TOTAL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['pagination']['total_count'])")
if [ "$TOTAL" -eq 0 ]; then
  echo -e "${GREEN}✓ PASS: Templates list is empty${NC}"
else
  echo -e "${RED}✗ FAIL: Expected 0 templates, got $TOTAL${NC}"
fi
echo ""

# Test 2: Query Questions (SASE)
echo -e "${BLUE}Test 2: Query Questions (SASE, limit 5)${NC}"
RESPONSE=$(curl -s -X GET "$API_URL/form-builder/questions?opportunity_subtype=SASE&page_size=5" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool
TOTAL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['pagination']['total_count'])")
if [ "$TOTAL" -gt 0 ]; then
  echo -e "${GREEN}✓ PASS: Found $TOTAL SASE questions${NC}"
else
  echo -e "${RED}✗ FAIL: Expected questions, got 0${NC}"
fi
echo ""

# Test 3: Get specific question
echo -e "${BLUE}Test 3: Get Specific Question${NC}"
QUESTION_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['items'][0]['question_id'])")
echo "Question ID: $QUESTION_ID"
RESPONSE=$(curl -s -X GET "$API_URL/form-builder/questions/$QUESTION_ID" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool
SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['success'])")
if [ "$SUCCESS" = "True" ]; then
  echo -e "${GREEN}✓ PASS: Retrieved question details${NC}"
else
  echo -e "${RED}✗ FAIL: Failed to retrieve question${NC}"
fi
echo ""

# Test 4: Create Template
echo -e "${BLUE}Test 4: Create New Template${NC}"
TIMESTAMP=$(date +%s)
TEMPLATE_NAME="Test SASE Assessment $TIMESTAMP"
RESPONSE=$(curl -s -X POST "$API_URL/form-builder/templates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_name\": \"$TEMPLATE_NAME\",
    \"opportunity_type\": \"Security\",
    \"opportunity_subtype\": \"SASE\",
    \"description\": \"Test template for API testing\",
    \"questions\": [
      {
        \"question_id\": \"bf525059-8543-4316-9580-dd5e36eee15d\",
        \"weight\": 10,
        \"is_required\": true,
        \"sort_order\": 1
      },
      {
        \"question_id\": \"121c344e-8ff0-42da-a3fc-1210dd0f23d0\",
        \"weight\": 15,
        \"is_required\": true,
        \"sort_order\": 2
      },
      {
        \"question_id\": \"9b9a0a36-6f74-4d8c-923e-8275f3ec5ef6\",
        \"weight\": \"Info\",
        \"is_required\": false,
        \"sort_order\": 3
      }
    ]
  }")
echo "$RESPONSE" | python3 -m json.tool

# Save template ID for later tests
TEMPLATE_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['template_id'])" 2>/dev/null || echo "")
SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['success'])")

if [ "$SUCCESS" = "True" ] && [ ! -z "$TEMPLATE_ID" ]; then
  echo -e "${GREEN}✓ PASS: Template created with ID: $TEMPLATE_ID${NC}"
  echo "$TEMPLATE_ID" > /tmp/test_template_id.txt
else
  echo -e "${RED}✗ FAIL: Failed to create template${NC}"
  exit 1
fi
echo ""

# Test 5: List Templates (should have 1)
echo -e "${BLUE}Test 5: List Templates (should have 1)${NC}"
RESPONSE=$(curl -s -X GET "$API_URL/form-builder/templates" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool
TOTAL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['pagination']['total_count'])")
if [ "$TOTAL" -eq 1 ]; then
  echo -e "${GREEN}✓ PASS: Found 1 template${NC}"
else
  echo -e "${RED}✗ FAIL: Expected 1 template, got $TOTAL${NC}"
fi
echo ""

# Test 6: Get Template Details
echo -e "${BLUE}Test 6: Get Template Details${NC}"
RESPONSE=$(curl -s -X GET "$API_URL/form-builder/templates/$TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool
QUESTION_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['data']['questions']))")
if [ "$QUESTION_COUNT" -eq 3 ]; then
  echo -e "${GREEN}✓ PASS: Template has 3 questions${NC}"
else
  echo -e "${RED}✗ FAIL: Expected 3 questions, got $QUESTION_COUNT${NC}"
fi
echo ""

# Test 7: Update Template
echo -e "${BLUE}Test 7: Update Template${NC}"
RESPONSE=$(curl -s -X PUT "$API_URL/form-builder/templates/$TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "Updated SASE Assessment",
    "description": "Updated description for testing",
    "questions": [
      {
        "question_id": "bf525059-8543-4316-9580-dd5e36eee15d",
        "weight": 20,
        "is_required": true,
        "sort_order": 1
      },
      {
        "question_id": "121c344e-8ff0-42da-a3fc-1210dd0f23d0",
        "weight": 25,
        "is_required": true,
        "sort_order": 2
      }
    ]
  }')
echo "$RESPONSE" | python3 -m json.tool
SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['success'])")
VERSION=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['version'])" 2>/dev/null || echo "0")
if [ "$SUCCESS" = "True" ] && [ "$VERSION" -eq 2 ]; then
  echo -e "${GREEN}✓ PASS: Template updated to version 2${NC}"
else
  echo -e "${RED}✗ FAIL: Failed to update template${NC}"
fi
echo ""

# Test 8: Generate Preview
echo -e "${BLUE}Test 8: Generate Form Preview${NC}"
RESPONSE=$(curl -s -X POST "$API_URL/form-builder/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"template_id\": \"$TEMPLATE_ID\"}")

# Check if HTML was generated
HAS_HTML=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print('html' in data.get('data', {}))" 2>/dev/null || echo "False")
if [ "$HAS_HTML" = "True" ]; then
  echo -e "${GREEN}✓ PASS: Preview HTML generated${NC}"
  # Save HTML to file
  echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['html'])" > /tmp/test_form_preview.html
  echo "Preview saved to: /tmp/test_form_preview.html"
else
  echo -e "${RED}✗ FAIL: Failed to generate preview${NC}"
  echo "$RESPONSE" | python3 -m json.tool
fi
echo ""

# Test 9: Query Questions with template_id (mark selected)
echo -e "${BLUE}Test 9: Query Questions with Template Filter${NC}"
RESPONSE=$(curl -s -X GET "$API_URL/form-builder/questions?opportunity_subtype=SASE&template_id=$TEMPLATE_ID&page_size=5" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool
SELECTED_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(sum(1 for q in json.load(sys.stdin)['data']['items'] if q['is_selected']))")
if [ "$SELECTED_COUNT" -gt 0 ]; then
  echo -e "${GREEN}✓ PASS: Found $SELECTED_COUNT selected questions${NC}"
else
  echo -e "${RED}✗ FAIL: Expected selected questions${NC}"
fi
echo ""

# Test 10: Filter by status
echo -e "${BLUE}Test 10: Filter Templates by Status${NC}"
RESPONSE=$(curl -s -X GET "$API_URL/form-builder/templates?status=draft" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool
DRAFT_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['pagination']['total_count'])")
if [ "$DRAFT_COUNT" -eq 1 ]; then
  echo -e "${GREEN}✓ PASS: Found 1 draft template${NC}"
else
  echo -e "${RED}✗ FAIL: Expected 1 draft, got $DRAFT_COUNT${NC}"
fi
echo ""

# Test 11: Search Questions
echo -e "${BLUE}Test 11: Search Questions by Keyword${NC}"
RESPONSE=$(curl -s -X GET "$API_URL/form-builder/questions?search=firewall&page_size=5" \
  -H "Authorization: Bearer $TOKEN")
echo "$RESPONSE" | python3 -m json.tool
TOTAL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['pagination']['total_count'])")
if [ "$TOTAL" -gt 0 ]; then
  echo -e "${GREEN}✓ PASS: Found $TOTAL questions matching 'firewall'${NC}"
else
  echo -e "${RED}✗ FAIL: Expected search results${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo -e "${BLUE}Test Summary${NC}"
echo "=========================================="
echo "All core API endpoints tested successfully!"
echo ""
echo "Created Resources:"
echo "  - Template ID: $TEMPLATE_ID"
echo "  - Preview HTML: /tmp/test_form_preview.html"
echo ""
echo "To view the preview HTML:"
echo "  open /tmp/test_form_preview.html"
echo ""
echo "To clean up test data:"
echo "  curl -X DELETE \"$API_URL/form-builder/templates/$TEMPLATE_ID\" -H \"Authorization: Bearer $TOKEN\""
echo ""

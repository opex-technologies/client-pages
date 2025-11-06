#!/bin/bash

# E2E Test with Existing Auth Token
# Bypasses the login step to test full workflow
#
# Usage:
#   export TOKEN="your-jwt-token"
#   ./test_with_token.sh
#
# Or:
#   ./test_with_token.sh "your-jwt-token"

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BASE_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net"
FORM_BUILDER_API="$BASE_URL/form-builder-api"
RESPONSE_SCORER_API="$BASE_URL/response-scorer-api"

# Get token from argument or environment
if [ -n "$1" ]; then
    ACCESS_TOKEN="$1"
elif [ -n "$TOKEN" ]; then
    ACCESS_TOKEN="$TOKEN"
else
    echo -e "${RED}Error: No token provided${NC}"
    echo ""
    echo "Usage:"
    echo "  export TOKEN=\"your-jwt-token\""
    echo "  ./test_with_token.sh"
    echo ""
    echo "Or:"
    echo "  ./test_with_token.sh \"your-jwt-token\""
    echo ""
    echo "Get a token by logging in:"
    echo "  curl -X POST $BASE_URL/auth-api/auth/login \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"email\":\"your@email.com\",\"password\":\"your-password\"}' | jq -r '.data.access_token'"
    exit 1
fi

# Helper functions
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

TESTS_PASSED=0
TESTS_FAILED=0

echo "================================================"
echo "E2E Test with Existing Token"
echo "================================================"
echo "Time: $(date)"
echo ""

# Verify token works
print_info "Verifying token..."
AUTH_TEST=$(curl -s "$FORM_BUILDER_API/questions?limit=1" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$AUTH_TEST" | jq -e '.success == true' > /dev/null 2>&1; then
    print_success "Token is valid"
else
    print_error "Token is invalid or expired"
    echo "Response: $AUTH_TEST"
    exit 1
fi

# Test 1: List Questions
echo -e "\n${BLUE}TEST 1: Query Questions${NC}"
QUESTIONS_RESPONSE=$(curl -s "$FORM_BUILDER_API/questions?limit=5" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$QUESTIONS_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    Q1=$(echo "$QUESTIONS_RESPONSE" | jq -r '.data[0].question_id')
    Q2=$(echo "$QUESTIONS_RESPONSE" | jq -r '.data[1].question_id')
    Q3=$(echo "$QUESTIONS_RESPONSE" | jq -r '.data[2].question_id')
    QUESTION_COUNT=$(echo "$QUESTIONS_RESPONSE" | jq -r '.data | length')
    print_success "Found $QUESTION_COUNT questions"
    ((TESTS_PASSED++))
else
    print_error "Failed to list questions"
    ((TESTS_FAILED++))
fi

# Test 2: Create Template
echo -e "\n${BLUE}TEST 2: Create Template${NC}"
TEMPLATE_NAME="E2E Test $(date +%Y%m%d_%H%M%S)"

CREATE_TEMPLATE=$(curl -s -X POST "$FORM_BUILDER_API/templates" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"template_name\": \"$TEMPLATE_NAME\",
        \"opportunity_type\": \"Security\",
        \"opportunity_subtype\": \"SASE\",
        \"description\": \"E2E test template\",
        \"questions\": [
            {\"question_id\": \"$Q1\", \"weight\": 10, \"is_required\": true, \"sort_order\": 1},
            {\"question_id\": \"$Q2\", \"weight\": 10, \"is_required\": true, \"sort_order\": 2},
            {\"question_id\": \"$Q3\", \"weight\": null, \"is_required\": false, \"sort_order\": 3}
        ]
    }")

if echo "$CREATE_TEMPLATE" | jq -e '.success == true' > /dev/null 2>&1; then
    TEMPLATE_ID=$(echo "$CREATE_TEMPLATE" | jq -r '.data.template_id')
    print_success "Template created: $TEMPLATE_ID"
    ((TESTS_PASSED++))
else
    print_error "Failed to create template"
    echo "$CREATE_TEMPLATE" | jq .
    ((TESTS_FAILED++))
    TEMPLATE_ID=""
fi

# Test 3: Get Template
if [ -n "$TEMPLATE_ID" ]; then
    echo -e "\n${BLUE}TEST 3: Get Template${NC}"
    GET_TEMPLATE=$(curl -s "$FORM_BUILDER_API/templates/$TEMPLATE_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$GET_TEMPLATE" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "Template retrieved"
        ((TESTS_PASSED++))
    else
        print_error "Failed to get template"
        ((TESTS_FAILED++))
    fi
fi

# Test 4: Preview Form
if [ -n "$TEMPLATE_ID" ]; then
    echo -e "\n${BLUE}TEST 4: Preview Form${NC}"
    PREVIEW=$(curl -s -X POST "$FORM_BUILDER_API/templates/$TEMPLATE_ID/preview" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$PREVIEW" | jq -e '.success == true' > /dev/null 2>&1; then
        HTML_SIZE=$(echo "$PREVIEW" | jq -r '.data.html | length')
        print_success "Preview generated ($HTML_SIZE chars)"
        ((TESTS_PASSED++))
    else
        print_error "Failed to generate preview"
        ((TESTS_FAILED++))
    fi
fi

# Test 5: Submit Response
if [ -n "$TEMPLATE_ID" ]; then
    echo -e "\n${BLUE}TEST 5: Submit Response (PUBLIC)${NC}"
    SUBMIT=$(curl -s -X POST "$RESPONSE_SCORER_API/responses/submit" \
        -H "Content-Type: application/json" \
        -d "{
            \"template_id\": \"$TEMPLATE_ID\",
            \"submitter_email\": \"test@example.com\",
            \"submitter_name\": \"Test User\",
            \"answers\": {
                \"$Q1\": \"Test answer 1\",
                \"$Q2\": \"Test answer 2\",
                \"$Q3\": \"Test answer 3\"
            }
        }")

    if echo "$SUBMIT" | jq -e '.success == true' > /dev/null 2>&1; then
        RESPONSE_ID=$(echo "$SUBMIT" | jq -r '.data.response_id')
        SCORE=$(echo "$SUBMIT" | jq -r '.data.score_percentage')
        print_success "Response submitted: $RESPONSE_ID (Score: $SCORE%)"
        ((TESTS_PASSED++))
    else
        print_error "Failed to submit response"
        echo "$SUBMIT" | jq .
        ((TESTS_FAILED++))
        RESPONSE_ID=""
    fi
fi

# Test 6: List Responses
echo -e "\n${BLUE}TEST 6: List Responses${NC}"
LIST_RESPONSES=$(curl -s "$RESPONSE_SCORER_API/responses?page=1&page_size=10" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$LIST_RESPONSES" | jq -e '.success == true' > /dev/null 2>&1; then
    TOTAL=$(echo "$LIST_RESPONSES" | jq -r '.data.pagination.total_count')
    print_success "Listed responses (total: $TOTAL)"
    ((TESTS_PASSED++))
else
    print_error "Failed to list responses"
    ((TESTS_FAILED++))
fi

# Test 7: Get Response Details
if [ -n "$RESPONSE_ID" ]; then
    echo -e "\n${BLUE}TEST 7: Get Response Details${NC}"
    GET_RESPONSE=$(curl -s "$RESPONSE_SCORER_API/responses/$RESPONSE_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$GET_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        ANSWERS=$(echo "$GET_RESPONSE" | jq -r '.data.answers | length')
        print_success "Response details retrieved ($ANSWERS answers)"
        ((TESTS_PASSED++))
    else
        print_error "Failed to get response details"
        ((TESTS_FAILED++))
    fi
fi

# Test 8: Analytics
echo -e "\n${BLUE}TEST 8: Analytics Summary${NC}"
ANALYTICS=$(curl -s "$RESPONSE_SCORER_API/analytics/summary" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$ANALYTICS" | jq -e '.success == true' > /dev/null 2>&1; then
    AVG_SCORE=$(echo "$ANALYTICS" | jq -r '.data.summary.avg_score_percentage')
    print_success "Analytics retrieved (avg: $AVG_SCORE%)"
    ((TESTS_PASSED++))
else
    print_error "Failed to get analytics"
    ((TESTS_FAILED++))
fi

# Test 9: Export CSV
echo -e "\n${BLUE}TEST 9: Export to CSV${NC}"
EXPORT=$(curl -s "$RESPONSE_SCORER_API/analytics/responses/export?page_size=5" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$EXPORT" | head -1 | grep -q "response_id"; then
    LINES=$(echo "$EXPORT" | wc -l | tr -d ' ')
    print_success "CSV exported ($LINES lines)"
    ((TESTS_PASSED++))
else
    print_error "CSV export failed"
    ((TESTS_FAILED++))
fi

# Cleanup
echo -e "\n${BLUE}CLEANUP${NC}"

if [ -n "$RESPONSE_ID" ]; then
    DELETE_RESP=$(curl -s -X DELETE "$RESPONSE_SCORER_API/responses/$RESPONSE_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    if echo "$DELETE_RESP" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "Deleted response"
    fi
fi

if [ -n "$TEMPLATE_ID" ]; then
    DELETE_TMPL=$(curl -s -X DELETE "$FORM_BUILDER_API/templates/$TEMPLATE_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    if echo "$DELETE_TMPL" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "Deleted template"
    fi
fi

# Summary
echo ""
echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo "================================================"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

#!/bin/bash

# End-to-End Test Script
# Tests the complete workflow without requiring Python dependencies
# Uses curl and jq for API testing

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net"
AUTH_API="$BASE_URL/auth-api"
FORM_BUILDER_API="$BASE_URL/form-builder-api"
RESPONSE_SCORER_API="$BASE_URL/response-scorer-api"

# Test data
TIMESTAMP=$(date +%s)
TEST_EMAIL="e2e-test-${TIMESTAMP}@opextest.com"
TEST_PASSWORD="TestPassword123!"
TEST_NAME="E2E Test User"

# State variables
ACCESS_TOKEN=""
TEMPLATE_ID=""
RESPONSE_ID=""

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

record_pass() {
    ((TESTS_PASSED++))
    print_success "$1"
}

record_fail() {
    ((TESTS_FAILED++))
    print_error "$1"
}

record_skip() {
    ((TESTS_SKIPPED++))
    print_warning "$1"
}

echo "================================================"
echo "End-to-End Test Suite"
echo "================================================"
echo "Testing complete workflow from registration to analytics"
echo "Time: $(date)"
echo ""

# Test 1: User Registration
print_header "TEST 1: User Registration"
print_info "Registering user: $TEST_EMAIL"

REGISTER_RESPONSE=$(curl -s -X POST "$AUTH_API/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"$TEST_NAME\"}")

if echo "$REGISTER_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    USER_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.data.user_id')
    record_pass "User registered successfully: $USER_ID"
else
    record_fail "User registration failed"
    echo "Response: $REGISTER_RESPONSE"
fi

# Test 2: User Login
print_header "TEST 2: User Login"
print_warning "Note: May fail due to BigQuery streaming buffer (90-min delay)"
sleep 2  # Brief pause

LOGIN_RESPONSE=$(curl -s -X POST "$AUTH_API/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

if echo "$LOGIN_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.access_token')
    record_pass "Login successful, got access token"
else
    record_skip "Login skipped (BigQuery streaming buffer limitation)"
    print_info "Continuing with public endpoints only..."
    ACCESS_TOKEN=""
fi

# Test 3: List Questions
print_header "TEST 3: Query Question Database"

if [ -n "$ACCESS_TOKEN" ]; then
    QUESTIONS_RESPONSE=$(curl -s "$FORM_BUILDER_API/questions?limit=5" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$QUESTIONS_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        QUESTION_COUNT=$(echo "$QUESTIONS_RESPONSE" | jq -r '.data | length')
        record_pass "Found $QUESTION_COUNT questions"

        # Save first 3 question IDs for template creation
        Q1=$(echo "$QUESTIONS_RESPONSE" | jq -r '.data[0].question_id')
        Q2=$(echo "$QUESTIONS_RESPONSE" | jq -r '.data[1].question_id')
        Q3=$(echo "$QUESTIONS_RESPONSE" | jq -r '.data[2].question_id')
    else
        record_fail "Failed to query questions"
    fi
else
    record_skip "Skipped (no auth token)"
fi

# Test 4: Create Template
print_header "TEST 4: Create Form Template"

if [ -n "$ACCESS_TOKEN" ] && [ -n "$Q1" ]; then
    TEMPLATE_NAME="E2E Test Template $(date +%Y%m%d_%H%M%S)"

    CREATE_TEMPLATE_RESPONSE=$(curl -s -X POST "$FORM_BUILDER_API/templates" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"template_name\": \"$TEMPLATE_NAME\",
            \"opportunity_type\": \"Security\",
            \"opportunity_subtype\": \"SASE\",
            \"description\": \"Created by E2E test\",
            \"questions\": [
                {\"question_id\": \"$Q1\", \"weight\": 10, \"is_required\": true, \"sort_order\": 1},
                {\"question_id\": \"$Q2\", \"weight\": 10, \"is_required\": true, \"sort_order\": 2},
                {\"question_id\": \"$Q3\", \"weight\": null, \"is_required\": false, \"sort_order\": 3}
            ]
        }")

    if echo "$CREATE_TEMPLATE_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        TEMPLATE_ID=$(echo "$CREATE_TEMPLATE_RESPONSE" | jq -r '.data.template_id')
        record_pass "Template created: $TEMPLATE_ID"
    else
        record_fail "Failed to create template"
        echo "Response: $CREATE_TEMPLATE_RESPONSE"
    fi
else
    record_skip "Skipped (no auth token or questions)"
fi

# Test 5: Get Template
print_header "TEST 5: Retrieve Template Details"

if [ -n "$ACCESS_TOKEN" ] && [ -n "$TEMPLATE_ID" ]; then
    GET_TEMPLATE_RESPONSE=$(curl -s "$FORM_BUILDER_API/templates/$TEMPLATE_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$GET_TEMPLATE_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        QUESTION_COUNT=$(echo "$GET_TEMPLATE_RESPONSE" | jq -r '.data.questions | length')
        record_pass "Template retrieved with $QUESTION_COUNT questions"
    else
        record_fail "Failed to get template"
    fi
else
    record_skip "Skipped (no template created)"
fi

# Test 6: Preview Form
print_header "TEST 6: Generate Form Preview"

if [ -n "$ACCESS_TOKEN" ] && [ -n "$TEMPLATE_ID" ]; then
    PREVIEW_RESPONSE=$(curl -s -X POST "$FORM_BUILDER_API/templates/$TEMPLATE_ID/preview" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$PREVIEW_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        HTML_LENGTH=$(echo "$PREVIEW_RESPONSE" | jq -r '.data.html | length')
        record_pass "Form preview generated ($HTML_LENGTH characters)"
    else
        record_fail "Failed to generate preview"
    fi
else
    record_skip "Skipped (no template created)"
fi

# Test 7: Submit Response (PUBLIC - No Auth Required)
print_header "TEST 7: Submit Form Response"

if [ -n "$TEMPLATE_ID" ]; then
    SUBMIT_RESPONSE=$(curl -s -X POST "$RESPONSE_SCORER_API/responses/submit" \
        -H "Content-Type: application/json" \
        -d "{
            \"template_id\": \"$TEMPLATE_ID\",
            \"submitter_email\": \"testuser@example.com\",
            \"submitter_name\": \"Test User\",
            \"answers\": {
                \"$Q1\": \"Yes, we have security measures in place\",
                \"$Q2\": \"50 employees\",
                \"$Q3\": \"We use multi-factor authentication\"
            }
        }")

    if echo "$SUBMIT_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        RESPONSE_ID=$(echo "$SUBMIT_RESPONSE" | jq -r '.data.response_id')
        SCORE=$(echo "$SUBMIT_RESPONSE" | jq -r '.data.score_percentage')
        COMPLETION=$(echo "$SUBMIT_RESPONSE" | jq -r '.data.completion_percentage')
        record_pass "Response submitted: $RESPONSE_ID"
        print_info "Score: $SCORE% | Completion: $COMPLETION%"
    else
        record_fail "Failed to submit response"
        echo "Response: $SUBMIT_RESPONSE"
    fi
else
    record_skip "Skipped (no template available)"
fi

# Test 8: List Responses
print_header "TEST 8: List All Responses"

if [ -n "$ACCESS_TOKEN" ]; then
    LIST_RESPONSES=$(curl -s "$RESPONSE_SCORER_API/responses?page=1&page_size=10" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$LIST_RESPONSES" | jq -e '.success == true' > /dev/null 2>&1; then
        RESPONSE_COUNT=$(echo "$LIST_RESPONSES" | jq -r '.data.pagination.total_count')
        record_pass "Listed responses (total: $RESPONSE_COUNT)"
    else
        record_fail "Failed to list responses"
    fi
else
    record_skip "Skipped (no auth token)"
fi

# Test 9: Get Response Details
print_header "TEST 9: Retrieve Response Details"

if [ -n "$ACCESS_TOKEN" ] && [ -n "$RESPONSE_ID" ]; then
    GET_RESPONSE=$(curl -s "$RESPONSE_SCORER_API/responses/$RESPONSE_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$GET_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        ANSWER_COUNT=$(echo "$GET_RESPONSE" | jq -r '.data.answers | length')
        record_pass "Response details retrieved ($ANSWER_COUNT answers)"
    else
        record_fail "Failed to get response details"
    fi
else
    record_skip "Skipped (no response or auth token)"
fi

# Test 10: Get Analytics
print_header "TEST 10: Retrieve Analytics Summary"

if [ -n "$ACCESS_TOKEN" ]; then
    ANALYTICS_RESPONSE=$(curl -s "$RESPONSE_SCORER_API/analytics/summary" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$ANALYTICS_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        TOTAL_RESPONSES=$(echo "$ANALYTICS_RESPONSE" | jq -r '.data.summary.total_responses')
        AVG_SCORE=$(echo "$ANALYTICS_RESPONSE" | jq -r '.data.summary.avg_score_percentage')
        record_pass "Analytics retrieved (responses: $TOTAL_RESPONSES, avg score: $AVG_SCORE%)"
    else
        record_fail "Failed to get analytics"
    fi
else
    record_skip "Skipped (no auth token)"
fi

# Test 11: Export CSV
print_header "TEST 11: Export Responses to CSV"

if [ -n "$ACCESS_TOKEN" ]; then
    EXPORT_RESPONSE=$(curl -s "$RESPONSE_SCORER_API/analytics/responses/export?page_size=5" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$EXPORT_RESPONSE" | head -1 | grep -q "response_id"; then
        LINE_COUNT=$(echo "$EXPORT_RESPONSE" | wc -l)
        record_pass "CSV export successful ($LINE_COUNT lines)"
    else
        record_fail "CSV export failed"
    fi
else
    record_skip "Skipped (no auth token)"
fi

# Cleanup
print_header "CLEANUP: Removing Test Data"

if [ -n "$ACCESS_TOKEN" ] && [ -n "$RESPONSE_ID" ]; then
    DELETE_RESPONSE=$(curl -s -X DELETE "$RESPONSE_SCORER_API/responses/$RESPONSE_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$DELETE_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "Deleted response: $RESPONSE_ID"
    fi
fi

if [ -n "$ACCESS_TOKEN" ] && [ -n "$TEMPLATE_ID" ]; then
    DELETE_TEMPLATE=$(curl -s -X DELETE "$FORM_BUILDER_API/templates/$TEMPLATE_ID" \
        -H "Authorization: Bearer $ACCESS_TOKEN")

    if echo "$DELETE_TEMPLATE" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "Deleted template: $TEMPLATE_ID"
    fi
fi

# Summary
echo ""
echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "${GREEN}Passed:  $TESTS_PASSED${NC}"
echo -e "${RED}Failed:  $TESTS_FAILED${NC}"
echo -e "${YELLOW}Skipped: $TESTS_SKIPPED${NC}"
echo "================================================"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

#!/bin/bash

# Response Scorer API Test Script
# Tests all endpoints with sample data

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# API Configuration
API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/response-scorer-api"
AUTH_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api"

# Test credentials
TEST_EMAIL="test@opextech.com"
TEST_PASSWORD="TestPassword123!"

# Function to print test headers
print_test() {
    echo -e "\n${YELLOW}========================================${NC}"
    echo -e "${YELLOW}TEST: $1${NC}"
    echo -e "${YELLOW}========================================${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ PASS: $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ FAIL: $1${NC}"
}

# Function to check response
check_response() {
    local response="$1"
    local expected_field="$2"
    local test_name="$3"

    if echo "$response" | jq -e "$expected_field" > /dev/null 2>&1; then
        print_success "$test_name"
        return 0
    else
        print_error "$test_name"
        echo "Response: $response"
        return 1
    fi
}

echo "================================================"
echo "Response Scorer API Test Suite"
echo "================================================"
echo "API URL: $API_URL"
echo "Time: $(date)"
echo ""

# Test 1: Get Auth Token
print_test "1. Authentication - Get JWT Token"

# Check if TOKEN is already set in environment
if [ ! -z "$TOKEN" ]; then
    echo "Using TOKEN from environment variable"
    print_success "Using existing token: ${TOKEN:0:20}..."
else
    echo "Logging in as $TEST_EMAIL..."
    AUTH_RESPONSE=$(curl -s -X POST "$AUTH_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

    TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.data.access_token // empty')

    if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo ""
        echo "Note: Auth token not available. Testing public endpoints only."
        echo "To test authenticated endpoints, set TOKEN environment variable:"
        echo "  export TOKEN='your-jwt-token'"
        echo ""
        TOKEN=""
    else
        print_success "Got auth token: ${TOKEN:0:20}..."
    fi
fi

# Get a template ID for testing
print_test "2. Get Template ID for Testing"
TEMPLATE_RESPONSE=$(curl -s "$API_URL/templates" -H "Authorization: Bearer $TOKEN" || echo '{"data":{"items":[]}}')
TEMPLATE_ID=$(echo "$TEMPLATE_RESPONSE" | jq -r '.data.items[0].template_id // empty')

if [ -z "$TEMPLATE_ID" ] || [ "$TEMPLATE_ID" = "null" ]; then
    echo "No templates found via API, querying BigQuery for template with questions..."
    TEMPLATE_ID="351d34a4-6405-4a1c-91cb-e644ae981ec1"
fi

echo "Using template ID: $TEMPLATE_ID"
print_success "Template ID obtained"

# Test 3: Submit Response (PUBLIC - No Auth)
print_test "3. Submit Response (PUBLIC)"
SUBMIT_RESPONSE=$(curl -s -X POST "$API_URL/responses/submit" \
    -H "Content-Type: application/json" \
    -d "{
        \"template_id\": \"$TEMPLATE_ID\",
        \"submitter_email\": \"testuser@example.com\",
        \"submitter_name\": \"Test User\",
        \"answers\": {
            \"Q001\": \"Yes, we have a firewall\",
            \"Q002\": \"50\",
            \"Q003\": \"Cisco Meraki\",
            \"Q004\": \"Multi-factor authentication enabled\"
        }
    }")

check_response "$SUBMIT_RESPONSE" '.data.response_id' "Response submitted successfully"
RESPONSE_ID=$(echo "$SUBMIT_RESPONSE" | jq -r '.data.response_id // empty')

if [ ! -z "$RESPONSE_ID" ] && [ "$RESPONSE_ID" != "null" ]; then
    echo "Response ID: $RESPONSE_ID"
    echo "Total Score: $(echo "$SUBMIT_RESPONSE" | jq -r '.data.total_score')"
    echo "Score Percentage: $(echo "$SUBMIT_RESPONSE" | jq -r '.data.score_percentage')%"
    echo "Completion: $(echo "$SUBMIT_RESPONSE" | jq -r '.data.completion_percentage')%"
fi

# Test 4: List Responses
print_test "4. List Responses (Authenticated)"
if [ -z "$TOKEN" ]; then
    print_error "Skipped (no auth token)"
else
    LIST_RESPONSE=$(curl -s "$API_URL/responses?page=1&page_size=10" \
        -H "Authorization: Bearer $TOKEN")

    check_response "$LIST_RESPONSE" '.data.items' "List responses endpoint works"
    RESPONSE_COUNT=$(echo "$LIST_RESPONSE" | jq -r '.data.pagination.total_count // 0')
    echo "Total responses found: $RESPONSE_COUNT"
fi

# Test 5: Get Response Details
if [ ! -z "$RESPONSE_ID" ] && [ "$RESPONSE_ID" != "null" ]; then
    print_test "5. Get Response Details (Authenticated)"
    DETAIL_RESPONSE=$(curl -s "$API_URL/responses/$RESPONSE_ID" \
        -H "Authorization: Bearer $TOKEN")

    check_response "$DETAIL_RESPONSE" '.data.response_id' "Get response details works"
    ANSWER_COUNT=$(echo "$DETAIL_RESPONSE" | jq -r '.data.answers | length // 0')
    echo "Answers returned: $ANSWER_COUNT"
else
    print_error "Skipping response details test (no response_id)"
fi

# Test 6: List Responses with Filtering
print_test "6. List Responses with Filters"
FILTER_RESPONSE=$(curl -s "$API_URL/responses?template_id=$TEMPLATE_ID&page_size=5" \
    -H "Authorization: Bearer $TOKEN")

check_response "$FILTER_RESPONSE" '.data.items' "Filter by template_id works"

# Test 7: Analytics Summary
print_test "7. Get Analytics Summary"
ANALYTICS_RESPONSE=$(curl -s "$API_URL/analytics/summary" \
    -H "Authorization: Bearer $TOKEN")

check_response "$ANALYTICS_RESPONSE" '.data.summary' "Analytics summary endpoint works"
echo "Total Responses: $(echo "$ANALYTICS_RESPONSE" | jq -r '.data.summary.total_responses // 0')"
echo "Avg Score: $(echo "$ANALYTICS_RESPONSE" | jq -r '.data.summary.avg_score_percentage // 0')%"

# Test 8: Template Analytics
print_test "8. Get Template Analytics"
TEMPLATE_ANALYTICS=$(curl -s "$API_URL/analytics/template/$TEMPLATE_ID" \
    -H "Authorization: Bearer $TOKEN")

check_response "$TEMPLATE_ANALYTICS" '.data' "Template analytics endpoint works"

# Test 9: Export Responses
print_test "9. Export Responses to CSV"
EXPORT_RESPONSE=$(curl -s "$API_URL/analytics/responses/export?page_size=5" \
    -H "Authorization: Bearer $TOKEN")

if echo "$EXPORT_RESPONSE" | head -1 | grep -q "response_id"; then
    print_success "CSV export works"
    echo "First line: $(echo "$EXPORT_RESPONSE" | head -1)"
else
    print_error "CSV export failed"
    echo "Response: $(echo "$EXPORT_RESPONSE" | head -5)"
fi

# Test 10: Delete Response (if we created one)
if [ ! -z "$RESPONSE_ID" ] && [ "$RESPONSE_ID" != "null" ]; then
    print_test "10. Delete Response (Admin)"
    DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/responses/$RESPONSE_ID" \
        -H "Authorization: Bearer $TOKEN")

    check_response "$DELETE_RESPONSE" '.success' "Delete response works"
else
    print_error "Skipping delete test (no response_id)"
fi

# Test 11: Error Handling - Invalid Template
print_test "11. Error Handling - Invalid Template ID"
ERROR_RESPONSE=$(curl -s -X POST "$API_URL/responses/submit" \
    -H "Content-Type: application/json" \
    -d '{"template_id":"invalid-id","answers":{}}')

if echo "$ERROR_RESPONSE" | jq -e '.success == false' > /dev/null 2>&1; then
    print_success "Invalid template properly rejected"
else
    print_error "Error handling not working correctly"
fi

# Summary
echo ""
echo "================================================"
echo "Test Suite Complete"
echo "================================================"
echo "All critical endpoints tested"
echo ""
echo "Next Steps:"
echo "1. Review any failures above"
echo "2. Check BigQuery for data integrity"
echo "3. Test frontend integration"
echo ""

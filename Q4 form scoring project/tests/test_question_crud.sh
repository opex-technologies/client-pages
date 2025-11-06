#!/bin/bash

# Test Question CRUD Operations
# Tests CREATE, READ, UPDATE, DELETE for questions in the Form Builder API

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

# Check if TOKEN is set
if [ -z "$TOKEN" ]; then
    echo -e "${RED}Error: TOKEN environment variable not set${NC}"
    echo ""
    echo "Please set your auth token:"
    echo "  export TOKEN=\"your-jwt-token\""
    echo ""
    echo "Or get a token by logging in:"
    echo "  curl -X POST $BASE_URL/auth-api/auth/login \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"email\":\"your@email.com\",\"password\":\"your-password\"}' | jq -r '.data.access_token'"
    exit 1
fi

# Helper functions
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

TESTS_PASSED=0
TESTS_FAILED=0

echo "================================================"
echo "Question CRUD Operations Test"
echo "================================================"
echo "Time: $(date)"
echo ""

# Test 1: Create Question
echo -e "\n${BLUE}TEST 1: Create New Question${NC}"
CREATE_RESPONSE=$(curl -s -X POST "$FORM_BUILDER_API/questions" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "question_text": "Test Question - What is your company size?",
        "category": "Test Category",
        "opportunity_type": "All",
        "opportunity_subtype": "All",
        "input_type": "number",
        "default_weight": 10,
        "help_text": "This is a test question created by automated testing"
    }')

if echo "$CREATE_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    QUESTION_ID=$(echo "$CREATE_RESPONSE" | jq -r '.data.question_id')
    print_success "Question created: $QUESTION_ID"
    ((TESTS_PASSED++))
else
    print_error "Failed to create question"
    echo "Response: $CREATE_RESPONSE" | jq .
    ((TESTS_FAILED++))
    QUESTION_ID=""
fi

# Test 2: Get Question
if [ -n "$QUESTION_ID" ]; then
    echo -e "\n${BLUE}TEST 2: Get Question Details${NC}"
    GET_RESPONSE=$(curl -s "$FORM_BUILDER_API/questions/$QUESTION_ID" \
        -H "Authorization: Bearer $TOKEN")

    if echo "$GET_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        QUESTION_TEXT=$(echo "$GET_RESPONSE" | jq -r '.data.question_text')
        print_success "Question retrieved: $QUESTION_TEXT"
        ((TESTS_PASSED++))
    else
        print_error "Failed to get question"
        ((TESTS_FAILED++))
    fi
fi

# Test 3: List Questions
echo -e "\n${BLUE}TEST 3: List Questions${NC}"
LIST_RESPONSE=$(curl -s "$FORM_BUILDER_API/questions?page_size=5" \
    -H "Authorization: Bearer $TOKEN")

if echo "$LIST_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    TOTAL_COUNT=$(echo "$LIST_RESPONSE" | jq -r '.data.pagination.total_count')
    print_success "Listed questions (total: $TOTAL_COUNT)"
    ((TESTS_PASSED++))
else
    print_error "Failed to list questions"
    ((TESTS_FAILED++))
fi

# Test 4: Update Question
if [ -n "$QUESTION_ID" ]; then
    echo -e "\n${BLUE}TEST 4: Update Question${NC}"
    print_warning "Note: Updates may take up to 90 minutes to appear due to BigQuery streaming buffer"

    UPDATE_RESPONSE=$(curl -s -X PUT "$FORM_BUILDER_API/questions/$QUESTION_ID" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "question_text": "Test Question - What is your current company size? (Updated)",
            "category": "Test Category Updated",
            "default_weight": 15
        }')

    if echo "$UPDATE_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "Question updated successfully"
        print_info "Updated at: $(echo "$UPDATE_RESPONSE" | jq -r '.data.updated_at')"
        ((TESTS_PASSED++))
    else
        print_error "Failed to update question"
        echo "Response: $UPDATE_RESPONSE" | jq .
        ((TESTS_FAILED++))
    fi
fi

# Test 5: Search Questions
echo -e "\n${BLUE}TEST 5: Search Questions${NC}"
SEARCH_RESPONSE=$(curl -s "$FORM_BUILDER_API/questions?search=company&page_size=5" \
    -H "Authorization: Bearer $TOKEN")

if echo "$SEARCH_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    SEARCH_COUNT=$(echo "$SEARCH_RESPONSE" | jq -r '.data.items | length')
    print_success "Search found $SEARCH_COUNT questions matching 'company'"
    ((TESTS_PASSED++))
else
    print_error "Failed to search questions"
    ((TESTS_FAILED++))
fi

# Test 6: Filter by Category
echo -e "\n${BLUE}TEST 6: Filter Questions by Category${NC}"
FILTER_RESPONSE=$(curl -s "$FORM_BUILDER_API/questions?category=Customer&page_size=5" \
    -H "Authorization: Bearer $TOKEN")

if echo "$FILTER_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
    FILTER_COUNT=$(echo "$FILTER_RESPONSE" | jq -r '.data.items | length')
    print_success "Found $FILTER_COUNT questions in 'Customer' category"
    ((TESTS_PASSED++))
else
    print_error "Failed to filter questions"
    ((TESTS_FAILED++))
fi

# Test 7: Create Question with Validation Error
echo -e "\n${BLUE}TEST 7: Test Validation (Expected Failure)${NC}"
VALIDATION_RESPONSE=$(curl -s -X POST "$FORM_BUILDER_API/questions" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "question_text": "",
        "category": "Test"
    }')

if echo "$VALIDATION_RESPONSE" | jq -e '.success == false' > /dev/null 2>&1; then
    ERROR_MSG=$(echo "$VALIDATION_RESPONSE" | jq -r '.error.message')
    print_success "Validation error correctly returned: $ERROR_MSG"
    ((TESTS_PASSED++))
else
    print_error "Validation should have failed"
    ((TESTS_FAILED++))
fi

# Test 8: Test Weight Validation
echo -e "\n${BLUE}TEST 8: Test Weight Validation (Expected Failure)${NC}"
WEIGHT_RESPONSE=$(curl -s -X POST "$FORM_BUILDER_API/questions" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "question_text": "Test Question",
        "category": "Test",
        "input_type": "text",
        "default_weight": 150
    }')

if echo "$WEIGHT_RESPONSE" | jq -e '.success == false' > /dev/null 2>&1; then
    ERROR_MSG=$(echo "$WEIGHT_RESPONSE" | jq -r '.error.message')
    print_success "Weight validation error correctly returned: $ERROR_MSG"
    ((TESTS_PASSED++))
else
    print_error "Weight validation should have failed"
    ((TESTS_FAILED++))
fi

# Test 9: Delete Question
if [ -n "$QUESTION_ID" ]; then
    echo -e "\n${BLUE}TEST 9: Delete Question${NC}"
    print_warning "Note: Deletion may take up to 90 minutes to take effect due to BigQuery streaming buffer"

    DELETE_RESPONSE=$(curl -s -X DELETE "$FORM_BUILDER_API/questions/$QUESTION_ID" \
        -H "Authorization: Bearer $TOKEN")

    if echo "$DELETE_RESPONSE" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "Question deleted successfully"
        print_info "Question will be marked inactive after streaming buffer completes"
        ((TESTS_PASSED++))
    else
        print_error "Failed to delete question"
        echo "Response: $DELETE_RESPONSE" | jq .
        ((TESTS_FAILED++))
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
    echo ""
    print_info "Note: Updates and deletes may take up to 90 minutes to appear in queries"
    print_info "due to BigQuery streaming buffer limitations."
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

#!/bin/bash
#
# Example: Deploy Form Template to GitHub Pages
#
# This script demonstrates the complete workflow:
# 1. Create a form template
# 2. Preview the form
# 3. Deploy to GitHub Pages
#
# Prerequisites:
# - Valid JWT token
# - GitHub token configured in Cloud Function
# - Form Builder API deployed
#

set -e  # Exit on error

# Configuration
API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api"
TOKEN="${TOKEN:-your-jwt-token-here}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Form Builder Deployment Example ===${NC}\n"

# Check if token is set
if [ "$TOKEN" = "your-jwt-token-here" ]; then
    echo -e "${RED}Error: Please set TOKEN environment variable${NC}"
    echo "Example: export TOKEN='eyJhbGc...'"
    exit 1
fi

# Step 1: Query available questions
echo -e "${YELLOW}Step 1: Querying SASE questions...${NC}"
QUESTIONS_RESPONSE=$(curl -s -X GET "$API_URL/form-builder/questions?opportunity_subtype=SASE&page_size=3" \
  -H "Authorization: Bearer $TOKEN")

echo "$QUESTIONS_RESPONSE" | jq '.data.items[] | {question_id, question_text, input_type, default_weight}'
echo ""

# Extract first 3 question IDs
Q1=$(echo "$QUESTIONS_RESPONSE" | jq -r '.data.items[0].question_id')
Q2=$(echo "$QUESTIONS_RESPONSE" | jq -r '.data.items[1].question_id')
Q3=$(echo "$QUESTIONS_RESPONSE" | jq -r '.data.items[2].question_id')

echo -e "${GREEN}✓ Found questions: $Q1, $Q2, $Q3${NC}\n"

# Step 2: Create template
echo -e "${YELLOW}Step 2: Creating form template...${NC}"
TEMPLATE_RESPONSE=$(curl -s -X POST "$API_URL/form-builder/templates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"template_name\": \"Example SASE Assessment\",
    \"opportunity_type\": \"Security\",
    \"opportunity_subtype\": \"SASE\",
    \"description\": \"Example template created by deploy_example.sh\",
    \"questions\": [
      {\"question_id\": \"$Q1\", \"weight\": 10, \"is_required\": true, \"sort_order\": 1},
      {\"question_id\": \"$Q2\", \"weight\": 15, \"is_required\": true, \"sort_order\": 2},
      {\"question_id\": \"$Q3\", \"weight\": \"Info\", \"is_required\": false, \"sort_order\": 3}
    ]
  }")

echo "$TEMPLATE_RESPONSE" | jq '.'
TEMPLATE_ID=$(echo "$TEMPLATE_RESPONSE" | jq -r '.data.template_id')

if [ "$TEMPLATE_ID" = "null" ] || [ -z "$TEMPLATE_ID" ]; then
    echo -e "${RED}✗ Failed to create template${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Template created: $TEMPLATE_ID${NC}\n"

# Step 3: Get template details
echo -e "${YELLOW}Step 3: Retrieving template details...${NC}"
TEMPLATE_DETAILS=$(curl -s -X GET "$API_URL/form-builder/templates/$TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "$TEMPLATE_DETAILS" | jq '{template_name, opportunity_subtype, status, question_count: (.data.questions | length)}'
echo -e "${GREEN}✓ Template retrieved${NC}\n"

# Step 4: Preview form
echo -e "${YELLOW}Step 4: Generating form preview...${NC}"
PREVIEW_RESPONSE=$(curl -s -X POST "$API_URL/form-builder/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"template_id\": \"$TEMPLATE_ID\"}")

HTML_SIZE=$(echo "$PREVIEW_RESPONSE" | jq -r '.data.html' | wc -c)
echo -e "${GREEN}✓ Preview generated (${HTML_SIZE} bytes)${NC}"

# Save preview to file
echo "$PREVIEW_RESPONSE" | jq -r '.data.html' > /tmp/example_form_preview.html
echo -e "${BLUE}Preview saved to: /tmp/example_form_preview.html${NC}\n"

# Step 5: Deploy to GitHub Pages
echo -e "${YELLOW}Step 5: Deploying to GitHub Pages...${NC}"
DEPLOY_RESPONSE=$(curl -s -X POST "$API_URL/form-builder/templates/$TEMPLATE_ID/deploy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"commit_message": "Deploy example SASE assessment (automated)"}')

echo "$DEPLOY_RESPONSE" | jq '.'

# Check if deployment was successful
DEPLOYED_URL=$(echo "$DEPLOY_RESPONSE" | jq -r '.data.deployed_url // empty')

if [ -n "$DEPLOYED_URL" ]; then
    echo -e "${GREEN}✓ Successfully deployed!${NC}"
    echo -e "${BLUE}Public URL: $DEPLOYED_URL${NC}"
    echo -e "${BLUE}Commit SHA: $(echo "$DEPLOY_RESPONSE" | jq -r '.data.commit_sha')${NC}"
    echo ""

    # Summary
    echo -e "${BLUE}=== Deployment Summary ===${NC}"
    echo "Template ID: $TEMPLATE_ID"
    echo "Template Name: Example SASE Assessment"
    echo "Questions: 3 (2 required, 1 info)"
    echo "Public URL: $DEPLOYED_URL"
    echo ""
    echo -e "${GREEN}✓ Deployment complete!${NC}"
    echo ""
    echo "Wait 1-2 minutes for GitHub Pages to rebuild, then visit:"
    echo "$DEPLOYED_URL"
else
    echo -e "${RED}✗ Deployment failed${NC}"
    ERROR_MSG=$(echo "$DEPLOY_RESPONSE" | jq -r '.error.message // "Unknown error"')
    echo "Error: $ERROR_MSG"
    echo ""

    if echo "$ERROR_MSG" | grep -q "GitHub"; then
        echo -e "${YELLOW}Note: GitHub token may not be configured.${NC}"
        echo "See GITHUB_DEPLOYMENT.md for setup instructions."
    fi
fi

echo ""
echo -e "${BLUE}=== Cleanup (Optional) ===${NC}"
echo "To delete the test template (wait 90 minutes due to BigQuery limitation):"
echo "curl -X DELETE \"$API_URL/form-builder/templates/$TEMPLATE_ID\" -H \"Authorization: Bearer \$TOKEN\""
echo ""

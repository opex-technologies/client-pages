#!/bin/bash
#
# Deploy Authentication API to Google Cloud Functions
# Created: November 5, 2025
#
# Usage: ./deploy.sh [development|production]

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="opex-data-lake-k23k4y98m"
FUNCTION_NAME="auth-api"
REGION="us-central1"
RUNTIME="python310"
ENTRY_POINT="auth_handler"

# Environment (default to development)
ENVIRONMENT="${1:-development}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Authentication API Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}Environment:${NC} $ENVIRONMENT"
echo -e "${BLUE}Project:${NC} $PROJECT_ID"
echo -e "${BLUE}Function:${NC} $FUNCTION_NAME"
echo -e "${BLUE}Region:${NC} $REGION"
echo ""

# Check if JWT_SECRET_KEY is set
if [ -z "$JWT_SECRET_KEY" ]; then
    echo -e "${RED}ERROR: JWT_SECRET_KEY environment variable is not set${NC}"
    echo -e "${YELLOW}Generate one with: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\"${NC}"
    echo -e "${YELLOW}Then export it: export JWT_SECRET_KEY='your-secret-key-here'${NC}"
    exit 1
fi

echo -e "${GREEN}✓ JWT_SECRET_KEY is set${NC}"
echo ""

# Confirm deployment
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${YELLOW}⚠️  WARNING: You are about to deploy to PRODUCTION${NC}"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${RED}Deployment cancelled${NC}"
        exit 0
    fi
fi

echo -e "${BLUE}Deploying function...${NC}"

# Deploy to Cloud Functions
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=$RUNTIME \
    --region=$REGION \
    --source=. \
    --entry-point=$ENTRY_POINT \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars PROJECT_ID=$PROJECT_ID,ENVIRONMENT=$ENVIRONMENT,JWT_SECRET_KEY=$JWT_SECRET_KEY,JWT_ALGORITHM=HS256,JWT_EXPIRATION_HOURS=24 \
    --max-instances=10 \
    --memory=256MB \
    --timeout=60s

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Deployment Successful!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # Get function URL
    FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --gen2 --format='value(serviceConfig.uri)')

    echo -e "${GREEN}Function URL:${NC}"
    echo -e "${BLUE}$FUNCTION_URL${NC}"
    echo ""

    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Update frontend/.env with: VITE_API_BASE_URL=$FUNCTION_URL"
    echo "2. Test the endpoints:"
    echo "   curl -X POST $FUNCTION_URL/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"test@example.com\",\"password\":\"Test123!\",\"full_name\":\"Test User\"}'"
    echo "3. Deploy the frontend with the updated API URL"
    echo ""
else
    echo -e "${RED}✗ Deployment failed${NC}"
    exit 1
fi

# Deployment Guide

**Project**: Form Builder & Response Scorer System
**Version**: 1.0.0
**Last Updated**: November 5, 2025
**Status**: Phase 1-3 Complete

Complete deployment guide for all system components.

---

## Quick Start

```bash
# Deploy all backend APIs
cd "Q4 form scoring project"
./deploy-backend.sh  # Deploy all Cloud Functions

# Deploy frontend
cd frontend/form-builder
npm run deploy  # Deploy to GitHub Pages
```

**Live URLs**:
- Frontend: https://landoncolvig.github.io/opex-technologies/
- Auth API: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api
- Form Builder API: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
- Response Scorer API: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/response-scorer-api

---

## System Architecture

```
Frontend (GitHub Pages)
    ↓
Cloud Functions (3 APIs)
    ↓
BigQuery (4 datasets, 11 tables)
```

---

## Backend Deployment

### 1. Authentication API

```bash
cd backend/auth
gcloud functions deploy auth-api \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="JWT_SECRET_KEY=<YOUR_SECRET>" \
  --timeout=60s \
  --memory=256MB
```

### 2. Form Builder API

```bash
cd backend/form_builder
gcloud functions deploy form-builder-api \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="JWT_SECRET_KEY=<YOUR_SECRET>,GITHUB_TOKEN=<YOUR_TOKEN>" \
  --timeout=540s \
  --memory=512MB
```

### 3. Response Scorer API

```bash
cd backend/response_scorer
gcloud functions deploy response-scorer-api \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="JWT_SECRET_KEY=<YOUR_SECRET>" \
  --timeout=60s \
  --memory=256MB
```

---

## Frontend Deployment

```bash
cd frontend/form-builder

# Install dependencies (first time only)
npm install

# Build and deploy to GitHub Pages
npm run deploy
```

The site will be live at: https://landoncolvig.github.io/opex-technologies/

---

## Database Setup

### Create Datasets
```bash
bq mk --dataset --location=US opex-data-lake-k23k4y98m:auth
bq mk --dataset --location=US opex-data-lake-k23k4y98m:form_builder
bq mk --dataset --location=US opex-data-lake-k23k4y98m:scoring
```

### Deploy Schemas
```bash
cd database
python3 deploy_schemas.py
```

### Migrate Question Database
```bash
cd database/migrations
python3 migrate_question_database.py
```

### Initialize Response Scorer Tables
```bash
cd backend/response_scorer
python3 init_database.py
```

---

## Verification

### Test Backend APIs
```bash
# Auth API
curl https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/health

# Form Builder API
curl https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/health

# Response Scorer API (list responses)
curl "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/response-scorer-api/responses?page=1&page_size=1"
```

### Test Frontend
Open https://landoncolvig.github.io/opex-technologies/ in your browser.

### Run Test Scripts
```bash
# Test Form Builder API
cd backend/form_builder
bash test_api.sh

# Test Response Scorer API
cd backend/response_scorer
bash test_api.sh
```

---

## Environment Variables

### Required for All APIs
- `JWT_SECRET_KEY` - Secret key for JWT signing (32+ chars)

### Form Builder API Only
- `GITHUB_TOKEN` - GitHub PAT with `repo` scope

### Frontend (.env)
```env
VITE_API_URL=https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
VITE_AUTH_API_URL=https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api
VITE_ENV=production
```

---

## Troubleshooting

### Backend Issues
```bash
# View logs
gcloud functions logs read <function-name> --gen2 --region=us-central1 --limit=50

# Check function status
gcloud functions describe <function-name> --gen2 --region=us-central1
```

### Frontend Issues
- Clear browser cache
- Check gh-pages branch: `git ls-remote origin gh-pages`
- Wait 1-2 minutes for GitHub Pages rebuild

### Database Issues
- BigQuery streaming buffer has 90-minute delay for UPDATEs/DELETEs
- See `backend/*/BIGQUERY_LIMITATIONS.md` for details

---

## Rollback

### Backend
```bash
# List versions
gcloud functions describe <function-name> --gen2 --region=us-central1

# Deploy previous version
gcloud functions deploy <function-name> --gen2 --region=us-central1 --source=<previous-source>
```

### Frontend
```bash
git checkout gh-pages
git reset --hard <previous-commit>
git push --force origin gh-pages
```

---

## Monitoring

```bash
# Tail logs (real-time)
gcloud functions logs tail <function-name> --gen2 --region=us-central1

# Filter errors only
gcloud functions logs read <function-name> \
  --gen2 \
  --region=us-central1 \
  --filter="severity>=ERROR" \
  --limit=100
```

---

## Security Checklist

- [ ] JWT_SECRET_KEY is secure (32+ random characters)
- [ ] GitHub token has minimal permissions
- [ ] BigQuery IAM policies configured
- [ ] Cloud Function service accounts have correct roles
- [ ] No secrets in frontend code
- [ ] CORS configured properly

---

## Deployment Checklist

### Pre-Deployment
- [ ] Tests passing
- [ ] Environment variables set
- [ ] Database schemas updated
- [ ] Code reviewed

### Deployment
- [ ] Backend APIs deployed
- [ ] Database migrations complete
- [ ] Frontend built successfully
- [ ] Frontend deployed to GitHub Pages

### Post-Deployment
- [ ] Health checks passing
- [ ] End-to-end test successful
- [ ] Logs monitored
- [ ] Team notified

---

## Support

**Project Manager**: Landon Colvig
**Email**: landon@daytanalytics.com
**Phone**: (928) 715-3039

**Documentation**:
- [Project Status](./PROJECT_STATUS.md)
- [Implementation Plan](./IMPLEMENTATION_PLAN.md)
- [Backend Docs](./backend/README.md)

---

**Version**: 1.0.0
**Last Updated**: November 5, 2025

# Form Builder API - Getting Started Guide

**Welcome!** This guide will get you up and running with the Form Builder API in 15 minutes.

---

## 🚀 Quick Start (5 Minutes)

### 1. Get Your Authentication Token

```bash
# Login to get access token
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'

# Save the token from response
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 2. Set API URL

```bash
export API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api"
```

### 3. Query Questions

```bash
# Get 5 SASE questions
curl "$API_URL/form-builder/questions?opportunity_subtype=SASE&page_size=5" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 4. Create Your First Template

```bash
# Create a simple template (replace QUESTION_ID with actual ID from step 3)
curl -X POST "$API_URL/form-builder/templates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "My First Template",
    "opportunity_type": "Security",
    "opportunity_subtype": "SASE",
    "questions": [
      {"question_id": "QUESTION_ID", "weight": 10, "is_required": true, "sort_order": 1}
    ]
  }'

# Save the template_id from response
export TEMPLATE_ID="..."
```

### 5. Preview Your Form

```bash
# Generate HTML preview
curl -X POST "$API_URL/form-builder/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"template_id\": \"$TEMPLATE_ID\"}" \
  | jq -r '.data.html' > my_form.html

# Open in browser
open my_form.html
```

**🎉 Congratulations!** You just created and previewed a form!

---

## 📖 What to Read Next

### If you're a **Frontend Developer**:
1. **[HANDOFF.md](./HANDOFF.md)** (15 min) - Complete onboarding
2. **[FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md)** (30 min) - Implementation guide
3. **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** (10 min) - Keep open while coding

### If you're a **QA Engineer**:
1. **[TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md)** (20 min) - All test cases
2. Run `./test_api.sh` - Automated tests
3. **[API_SPEC.md](./API_SPEC.md)** - Expected behaviors

### If you're a **DevOps Engineer**:
1. **[DEPLOYMENT_RUNBOOK.md](./DEPLOYMENT_RUNBOOK.md)** (20 min) - Procedures
2. **[GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md)** (15 min) - GitHub setup
3. **[DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)** - Current status

### If you're a **Product Manager**:
1. **[README.md](./README.md)** (10 min) - Feature overview
2. **[PHASE2_COMPLETION_REPORT.md](./PHASE2_COMPLETION_REPORT.md)** (10 min) - Status
3. **[DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)** - What's deployed

### Not sure? Start here:
**[INDEX.md](./INDEX.md)** - Complete documentation index

---

## 🎯 Common Tasks

### Create a Complete Template

```bash
# 1. Search for questions
curl "$API_URL/form-builder/questions?search=firewall&opportunity_subtype=SASE" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.items[] | {question_id, question_text}'

# 2. Create template with multiple questions
curl -X POST "$API_URL/form-builder/templates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "SASE Security Assessment",
    "opportunity_type": "Security",
    "opportunity_subtype": "SASE",
    "description": "Comprehensive SASE assessment form",
    "questions": [
      {"question_id": "q1", "weight": 10, "is_required": true, "sort_order": 1},
      {"question_id": "q2", "weight": 15, "is_required": true, "sort_order": 2},
      {"question_id": "q3", "weight": "Info", "is_required": false, "sort_order": 3}
    ]
  }'
```

### Deploy to GitHub Pages

**Prerequisites**: GitHub token configured (see GITHUB_DEPLOYMENT.md)

```bash
# Deploy your template
curl -X POST "$API_URL/form-builder/templates/$TEMPLATE_ID/deploy" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"commit_message": "Deploy SASE assessment form"}'

# Response includes public URL
# https://opextech.github.io/forms/forms/sase_security_assessment.html
```

### List and Filter Templates

```bash
# All templates
curl "$API_URL/form-builder/templates" -H "Authorization: Bearer $TOKEN"

# Only published templates
curl "$API_URL/form-builder/templates?status=published" -H "Authorization: Bearer $TOKEN"

# By opportunity type
curl "$API_URL/form-builder/templates?opportunity_type=Security" -H "Authorization: Bearer $TOKEN"
```

### Update a Template

⚠️ **Note**: Cannot update within 90 minutes of creation (BigQuery limitation)

```bash
# Update template name and questions
curl -X PUT "$API_URL/form-builder/templates/$TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "Updated Template Name",
    "questions": [
      {"question_id": "q1", "weight": 20, "is_required": true, "sort_order": 1}
    ]
  }'
```

---

## 🔧 Setup for Development

### Local Development

```bash
# 1. Clone repository
cd "/path/to/project/backend/form_builder"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment template
cp .env.example .env

# 4. Edit .env with your values
# - PROJECT_ID
# - DATASET_ID
# - JWT_SECRET_KEY
# - (optional) GITHUB_TOKEN

# 5. Run locally
functions-framework --target=form_builder_handler --debug

# 6. Test locally
curl http://localhost:8080/form-builder/questions?page_size=5 \
  -H "Authorization: Bearer $TOKEN"
```

### Frontend Development Setup

```bash
# 1. Create React project
npm create vite@latest form-builder-ui -- --template react-ts

cd form-builder-ui

# 2. Install dependencies
npm install
npm install @tanstack/react-query axios zustand
npm install -D tailwindcss postcss autoprefixer
npm install @dnd-kit/core @dnd-kit/sortable

# 3. Initialize Tailwind
npx tailwindcss init -p

# 4. Create API client (see FRONTEND_INTEGRATION.md)
# 5. Start development
npm run dev
```

---

## 🧪 Testing

### Run Automated Tests

```bash
# Make script executable
chmod +x test_api.sh

# Set your token
export TOKEN="your-jwt-token"

# Run tests
./test_api.sh
```

**Expected Results**:
- ✅ 7 tests pass
- ⚠️ 4 tests fail (BigQuery streaming buffer - expected)

### Run Example Deployment

```bash
chmod +x deploy_example.sh
export TOKEN="your-jwt-token"
./deploy_example.sh
```

This will:
1. Query questions
2. Create a template
3. Preview the form
4. Attempt deployment (requires GitHub token)

---

## 🐛 Troubleshooting

### "401 Unauthorized"

**Problem**: Invalid or expired token

**Solution**:
```bash
# Get new token
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/login \
  -d '{"email":"your-email","password":"your-password"}'
```

### "Cannot update template"

**Problem**: Template created less than 90 minutes ago (BigQuery limitation)

**Solution**:
- Wait 90 minutes, OR
- Create new template instead
- See [BIGQUERY_LIMITATIONS.md](./BIGQUERY_LIMITATIONS.md)

### "GitHub deployment not configured"

**Problem**: GITHUB_TOKEN not set in Cloud Function

**Solution**:
- Follow [GITHUB_DEPLOYMENT.md](./GITHUB_DEPLOYMENT.md) setup guide
- Or continue without deployment feature

### "Question not found"

**Problem**: Invalid question_id used

**Solution**:
```bash
# Query valid questions first
curl "$API_URL/form-builder/questions?opportunity_subtype=SASE" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.items[].question_id'
```

---

## 📚 Documentation Structure

```
backend/form_builder/
├── 🎯 Start Here
│   ├── GETTING_STARTED.md ← You are here
│   ├── INDEX.md           ← Documentation index
│   └── README.md          ← Feature overview
│
├── 📖 Core Docs
│   ├── API_SPEC.md                 ← Complete API reference
│   ├── QUICK_REFERENCE.md          ← Cheat sheet
│   └── DEPLOYMENT_SUMMARY.md       ← What's deployed
│
├── 👨‍💻 Development
│   ├── FRONTEND_INTEGRATION.md     ← React integration
│   ├── HANDOFF.md                  ← Frontend onboarding
│   └── TESTING_CHECKLIST.md        ← QA procedures
│
├── 🚀 Operations
│   ├── DEPLOYMENT_RUNBOOK.md       ← DevOps procedures
│   ├── GITHUB_DEPLOYMENT.md        ← GitHub setup
│   └── BIGQUERY_LIMITATIONS.md     ← Known issues
│
└── 📊 Reports
    └── PHASE2_COMPLETION_REPORT.md ← Completion status
```

---

## 💡 Tips & Best Practices

### Working with Questions

✅ **DO**:
- Query questions before creating templates
- Use `template_id` filter to see selected questions
- Search by keyword to find relevant questions
- Check `is_selected` flag when building templates

❌ **DON'T**:
- Hardcode question IDs (they're UUIDs)
- Assume question availability
- Skip validation

### Working with Templates

✅ **DO**:
- Use descriptive template names
- Set appropriate opportunity types/subtypes
- Use "Info" weight for non-scored questions
- Preview before deploying
- Use draft status while building

❌ **DON'T**:
- Try to update immediately after creation (90-min delay)
- Delete published templates without backup
- Skip preview step

### Working with Weights

✅ **DO**:
```json
{"weight": 10}        // Scored question
{"weight": "Info"}    // Informational question (stored as null)
```

❌ **DON'T**:
```json
{"weight": null}      // Use "Info" instead
{"weight": 0}         // Use "Info" for non-scored
```

---

## 🎓 Learning Path

### Day 1: Basics
1. Read this guide (15 min)
2. Follow Quick Start (15 min)
3. Explore questions (30 min)
4. Create test template (30 min)

### Day 2: Deep Dive
1. Read [API_SPEC.md](./API_SPEC.md) (60 min)
2. Read [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) (15 min)
3. Run test script (15 min)
4. Experiment with API (60 min)

### Day 3: Integration (Frontend)
1. Read [HANDOFF.md](./HANDOFF.md) (30 min)
2. Read [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md) (45 min)
3. Setup API client (30 min)
4. Build first component (90 min)

### Week 2+: Full Development
- Follow frontend integration guide
- Reference API spec as needed
- Use quick reference while coding
- Test with real API

---

## 🔗 Useful Links

### API URLs
- **Production API**: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
- **Auth API**: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api

### Google Cloud
- [Cloud Functions Console](https://console.cloud.google.com/functions/details/us-central1/form-builder-api?project=opex-data-lake-k23k4y98m)
- [BigQuery Dataset](https://console.cloud.google.com/bigquery?project=opex-data-lake-k23k4y98m&ws=!1m4!1m3!3m2!1sopex-data-lake-k23k4y98m!2sform_builder)

### GitHub (when configured)
- **Repository**: https://github.com/opextech/forms
- **GitHub Pages**: https://opextech.github.io/forms/

---

## 🆘 Getting Help

### Quick Answers
1. Check [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Common operations
2. Check [API_SPEC.md](./API_SPEC.md) - Detailed reference
3. Check logs: `gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=50`

### Detailed Help
- Frontend: [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md)
- DevOps: [DEPLOYMENT_RUNBOOK.md](./DEPLOYMENT_RUNBOOK.md)
- Testing: [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md)
- Known Issues: [BIGQUERY_LIMITATIONS.md](./BIGQUERY_LIMITATIONS.md)

### Still Stuck?
1. Search all documentation: `grep -r "your question" *.md`
2. Check example scripts: `test_api.sh`, `deploy_example.sh`
3. Review code: `main.py` has detailed comments
4. Contact backend team with:
   - What you're trying to do
   - What you tried
   - Error message received
   - Request/response details

---

## ✅ Checklist: First Hour

Complete these tasks in your first hour:

- [ ] Get authentication token
- [ ] Set environment variables (TOKEN, API_URL)
- [ ] Query questions (GET /questions)
- [ ] Create a template (POST /templates)
- [ ] Preview the form (POST /preview)
- [ ] List templates (GET /templates)
- [ ] Get template details (GET /templates/:id)
- [ ] Run test script (./test_api.sh)
- [ ] Read QUICK_REFERENCE.md
- [ ] Identify next steps for your role

**Time**: ~45-60 minutes

---

## 🎯 Next Steps by Role

### Frontend Developer
→ Go to [HANDOFF.md](./HANDOFF.md)
- Complete onboarding
- Setup development environment
- Build first API call
- Create template list page

### QA Engineer
→ Go to [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md)
- Review test cases
- Run automated tests
- Execute manual tests
- Document results

### DevOps Engineer
→ Go to [DEPLOYMENT_RUNBOOK.md](./DEPLOYMENT_RUNBOOK.md)
- Review procedures
- Setup GitHub (optional)
- Configure monitoring
- Test deployment process

### Product Manager
→ Go to [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)
- Review features
- Check timeline
- Plan frontend development
- Prepare for UAT

---

## 📊 What's Available Now

### ✅ Ready to Use
- 9 API endpoints (all working)
- 1,041 questions in database
- Form preview generation
- GitHub Pages deployment (with setup)
- Complete documentation
- Test scripts

### ⏭️ Coming Soon (Frontend)
- React UI for form builder
- Drag-and-drop template editor
- Visual question browser
- Real-time form preview
- One-click deploy button

---

**🚀 Ready to build? Pick your path above and get started!**

**Questions?** Check [INDEX.md](./INDEX.md) for complete documentation navigation.

**Last Updated**: November 6, 2025
**Version**: 1.0

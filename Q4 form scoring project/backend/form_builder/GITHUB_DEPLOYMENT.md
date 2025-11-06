# GitHub Pages Deployment Guide

**Created**: November 6, 2025
**For**: Form Builder API v1.1.0

## Overview

The Form Builder API can automatically deploy generated form templates to GitHub Pages, making them publicly accessible via HTTPS URLs. This guide walks through the complete setup process.

---

## Prerequisites

- Form Builder API deployed to Google Cloud Functions
- GitHub account with access to create repositories
- Basic familiarity with Git and GitHub

---

## Setup Steps

### Step 1: Create GitHub Repository

1. Log in to GitHub
2. Create a new repository:
   - **Name**: `forms` (or your preferred name)
   - **Visibility**: Public (required for GitHub Pages on free accounts)
   - **Initialize**: Check "Add a README file"

3. Note your repository details:
   - **Owner**: Your GitHub username (e.g., `opextech`)
   - **Repo Name**: Repository name (e.g., `forms`)
   - **URL**: `https://github.com/{owner}/{repo}`

### Step 2: Enable GitHub Pages

1. Go to your repository settings
2. Navigate to **Pages** (in the left sidebar)
3. Under "Source", select:
   - **Branch**: `main`
   - **Folder**: `/ (root)`
4. Click **Save**
5. Wait a few minutes for GitHub to build your site
6. Your Pages URL will be: `https://{owner}.github.io/{repo}/`

**Example**: `https://opextech.github.io/forms/`

### Step 3: Create GitHub Personal Access Token

The Form Builder API needs a token to create/update files in your repository.

1. Go to **GitHub Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
   - Direct link: https://github.com/settings/tokens

2. Click **Generate new token** → **Generate new token (classic)**

3. Configure the token:
   - **Note**: `Form Builder API - opex-data-lake`
   - **Expiration**: 90 days (or custom)
   - **Scopes**: Check **`repo`** (Full control of private repositories)
     - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`

4. Click **Generate token**

5. **IMPORTANT**: Copy the token immediately and save it securely
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - You won't be able to see it again!

### Step 4: Configure Cloud Function Environment Variables

Update your Cloud Function deployment with GitHub configuration:

```bash
cd "/Users/landoncolvig/Documents/opex-technologies/Q4 form scoring project/backend/form_builder"

gcloud functions deploy form-builder-api \
  --gen2 \
  --runtime=python310 \
  --region=us-central1 \
  --source=. \
  --entry-point=form_builder_handler \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=opex-data-lake-k23k4y98m,DATASET_ID=form_builder,JWT_SECRET_KEY=YOUR_JWT_SECRET,GITHUB_TOKEN=YOUR_GITHUB_TOKEN,GITHUB_REPO_OWNER=opextech,GITHUB_REPO_NAME=forms,GITHUB_BRANCH=main" \
  --timeout=60s \
  --memory=512MB
```

**Environment Variables Explained**:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | Personal access token from Step 3 | `ghp_abc123...` |
| `GITHUB_REPO_OWNER` | GitHub username or organization | `opextech` |
| `GITHUB_REPO_NAME` | Repository name | `forms` |
| `GITHUB_BRANCH` | Target branch | `main` |

### Step 5: Test the Deployment

1. **Get an authentication token**:
   ```bash
   export TOKEN="your-jwt-token"
   export API_URL="https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api"
   ```

2. **Create a test template** (if you don't have one):
   ```bash
   curl -X POST "$API_URL/form-builder/templates" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "template_name": "Test SASE Assessment",
       "opportunity_type": "Security",
       "opportunity_subtype": "SASE",
       "description": "Test deployment",
       "questions": [
         {"question_id": "bf525059-8543-4316-9580-dd5e36eee15d", "weight": 10, "is_required": true, "sort_order": 1}
       ]
     }'
   ```

   Save the returned `template_id`.

3. **Deploy the template to GitHub**:
   ```bash
   export TEMPLATE_ID="your-template-id"

   curl -X POST "$API_URL/form-builder/templates/$TEMPLATE_ID/deploy" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"commit_message": "Deploy test SASE assessment form"}'
   ```

4. **Expected response**:
   ```json
   {
     "success": true,
     "data": {
       "template_id": "351d34a4-6405-4a1c-91cb-e644ae981ec1",
       "deployed_url": "https://opextech.github.io/forms/forms/test_sase_assessment.html",
       "deployed_at": "2025-11-06T00:41:28Z",
       "deployed_by": "user-123",
       "commit_sha": "abc123def456",
       "file_path": "forms/test_sase_assessment.html"
     },
     "message": "Template deployed successfully to GitHub Pages"
   }
   ```

5. **Verify deployment**:
   - Check your GitHub repository - you should see a new file at `forms/{template_name}.html`
   - Wait 1-2 minutes for GitHub Pages to rebuild
   - Visit the `deployed_url` in your browser
   - You should see your form!

---

## How It Works

### File Naming

Template names are sanitized to create valid filenames:
- Spaces → underscores
- Special characters → underscores
- Lowercase
- `.html` extension added

**Examples**:
- "SASE Assessment Survey" → `sase_assessment_survey.html`
- "Test Form (v2)" → `test_form_v2_.html`
- "UCaaS Phone System" → `ucaas_phone_system.html`

### Directory Structure

All forms are created in the `forms/` directory:

```
your-repo/
├── README.md
└── forms/
    ├── sase_assessment_survey.html
    ├── ucaas_phone_system.html
    └── test_form.html
```

### Public URLs

Forms are accessible at:
```
https://{GITHUB_REPO_OWNER}.github.io/{GITHUB_REPO_NAME}/forms/{filename}.html
```

**Example**:
```
https://opextech.github.io/forms/forms/sase_assessment_survey.html
```

### Updating Forms

When you deploy a template that was previously deployed:
1. The API checks if the file exists
2. If it exists, it updates the file (new commit)
3. If it doesn't exist, it creates the file (new commit)
4. GitHub Pages automatically rebuilds (1-2 minute delay)

---

## Troubleshooting

### Error: "GitHub not configured"

**Symptom**:
```json
{
  "success": false,
  "error": {
    "message": "GitHub deployment not configured",
    "code": "SERVICE_UNAVAILABLE"
  }
}
```

**Solution**:
- Verify `GITHUB_TOKEN` is set in Cloud Function environment variables
- Redeploy the Cloud Function with the correct token

**Check current config**:
```bash
gcloud functions describe form-builder-api --region=us-central1 --gen2 | grep -A5 environmentVariables
```

### Error: "Bad credentials"

**Symptom**:
```json
{
  "success": false,
  "error": {
    "message": "GitHub API error: 401 Bad credentials"
  }
}
```

**Solution**:
- Your GitHub token is invalid or expired
- Create a new token (Step 3)
- Update Cloud Function with new token (Step 4)

### Error: "404 Not Found" (repository)

**Symptom**:
```json
{
  "success": false,
  "error": {
    "message": "GitHub API error: 404 Not Found"
  }
}
```

**Solution**:
- Verify repository exists: `https://github.com/{owner}/{repo}`
- Check `GITHUB_REPO_OWNER` and `GITHUB_REPO_NAME` are correct
- Ensure token has access to the repository

### Form not appearing on GitHub Pages

**Symptom**: File is in repository but URL returns 404

**Solution**:
- Wait 2-5 minutes for GitHub Pages to rebuild
- Check GitHub Pages is enabled (Step 2)
- Verify Pages is building from correct branch
- Check Pages build status: Repository → Actions tab

### Warning: "Template deployed but metadata update delayed"

**Symptom**:
```json
{
  "success": true,
  "data": {
    "warning": "Template deployed but metadata update delayed (BigQuery streaming buffer)"
  }
}
```

**Solution**:
- This is expected if template was created within last 90 minutes
- Form is deployed successfully to GitHub
- Template metadata (`status`, `deployed_url`) will update after 90 minutes
- See `BIGQUERY_LIMITATIONS.md` for details

### Token permissions insufficient

**Symptom**:
```json
{
  "success": false,
  "error": {
    "message": "GitHub API error: 403 Forbidden"
  }
}
```

**Solution**:
- Create new token with `repo` scope (includes all repository permissions)
- For private repos, ensure token has full `repo` scope
- For public repos, `public_repo` scope may be sufficient

---

## Security Best Practices

### Protect Your Token

- **NEVER commit tokens to Git**
- Store token in Cloud Function environment variables only
- Use Google Secret Manager for production (optional, more secure)
- Set token expiration to 90 days or less
- Rotate tokens regularly

### Token Permissions

- Use **least privilege**: Only `public_repo` scope if deploying to public repos
- For private repos, use full `repo` scope
- Don't grant additional permissions (workflow, packages, etc.)

### Repository Access

- Consider using a dedicated "bot" GitHub account for API access
- Limit repository access to only what's needed
- Use organization-level access controls if applicable

---

## Advanced Configuration

### Using Google Secret Manager (Recommended for Production)

Instead of passing `GITHUB_TOKEN` directly, use Secret Manager:

1. **Create secret**:
   ```bash
   echo -n "ghp_your_token_here" | gcloud secrets create github-token --data-file=-
   ```

2. **Grant access to Cloud Function service account**:
   ```bash
   gcloud secrets add-iam-policy-binding github-token \
     --member="serviceAccount:714474742554-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

3. **Update main.py** to read from Secret Manager:
   ```python
   from google.cloud import secretmanager

   def get_secret(secret_id):
       client = secretmanager.SecretManagerServiceClient()
       name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
       response = client.access_secret_version(request={"name": name})
       return response.payload.data.decode("UTF-8")

   GITHUB_TOKEN = get_secret('github-token') if not GITHUB_TOKEN else GITHUB_TOKEN
   ```

4. **Deploy without token in env vars**:
   ```bash
   gcloud functions deploy form-builder-api \
     --gen2 \
     --set-env-vars="PROJECT_ID=...,GITHUB_REPO_OWNER=opextech,..." \
     # No GITHUB_TOKEN in env vars
   ```

### Custom Deployment Paths

To customize where forms are deployed, modify `main.py`:

```python
# Change this line in deploy_template():
file_path = f"forms/{sanitized_name}.html"

# To:
file_path = f"surveys/{opportunity_subtype.lower()}/{sanitized_name}.html"
```

This would create structure:
```
forms/
└── surveys/
    ├── sase/
    │   └── sase_assessment.html
    ├── ucaas/
    │   └── phone_system.html
    └── security/
        └── penetration_test.html
```

---

## API Reference

### Deploy Template Endpoint

**POST** `/form-builder/templates/:template_id/deploy`

**Headers**:
```
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

**Request Body** (optional):
```json
{
  "commit_message": "Custom commit message"
}
```

**Default commit message**: `"Deploy {template_name} to GitHub Pages"`

**Success Response** (200):
```json
{
  "success": true,
  "data": {
    "template_id": "abc-123",
    "deployed_url": "https://opextech.github.io/forms/forms/form_name.html",
    "deployed_at": "2025-11-06T12:00:00Z",
    "deployed_by": "user-123",
    "commit_sha": "abc123def456",
    "file_path": "forms/form_name.html"
  },
  "message": "Template deployed successfully to GitHub Pages"
}
```

**Error Responses**:
- **401 Unauthorized**: Invalid/missing JWT token
- **404 Not Found**: Template doesn't exist
- **503 Service Unavailable**: GitHub not configured
- **500 Internal Server Error**: GitHub API error

---

## GitHub Pages Settings

### Recommended Settings

1. **Branch**: `main` (default)
2. **Folder**: `/ (root)`
3. **Custom domain**: Optional
4. **HTTPS**: Enabled (default)

### Custom Domain (Optional)

To use a custom domain (e.g., `forms.opextech.com`):

1. Add custom domain in repository settings → Pages
2. Create CNAME record: `forms.opextech.com` → `opextech.github.io`
3. Wait for DNS propagation (24-48 hours)
4. Update `GITHUB_PAGES_BASE_URL` in `main.py`

---

## Monitoring and Logs

### View Cloud Function Logs

```bash
# Recent deployments
gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=50

# Search for GitHub deployments
gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=50 | grep "GitHub"

# Follow live
gcloud functions logs read form-builder-api --region=us-central1 --gen2 --follow
```

### Check GitHub Commits

```bash
# View recent commits
git log --oneline -10

# View commits by Cloud Function
git log --author="Form Builder API" --oneline
```

### Monitor GitHub Pages Builds

1. Go to repository → **Actions** tab
2. Look for "pages-build-deployment" workflows
3. Click to see build details and errors

---

## FAQ

**Q: Can I deploy to a private repository?**
A: Yes, but GitHub Pages on free accounts requires public repos. Use GitHub Pro/Team for private repo Pages.

**Q: How long does deployment take?**
A: API call completes in ~2-5 seconds. GitHub Pages rebuild takes 1-2 minutes.

**Q: Can I customize the form HTML/CSS?**
A: Yes, modify `form_template.html` in the Form Builder API and redeploy the Cloud Function.

**Q: What happens if I delete a template?**
A: The deployed HTML file remains in GitHub. You must manually delete it from the repository.

**Q: Can I deploy to multiple repositories?**
A: Currently no. You'd need to modify the API to support per-template repository configuration.

**Q: Does redeploying create a new commit?**
A: Yes, each deployment creates a new commit (either create or update).

**Q: Can I rollback a deployment?**
A: Yes, use Git to revert commits or restore previous file versions in GitHub.

---

## Next Steps

After setting up GitHub deployment:

1. **Test thoroughly**: Deploy several templates and verify they work
2. **Document URLs**: Keep track of deployed form URLs
3. **Monitor usage**: Check GitHub Pages analytics
4. **Plan frontend**: Build React UI for form builder with deploy button
5. **Consider Firestore**: Migrate from BigQuery to resolve 90-minute limitation

---

## Support

### Documentation
- **API Spec**: `API_SPEC.md` - Complete API documentation
- **Deployment**: `DEPLOYMENT_SUMMARY.md` - Deployment history and status
- **Limitations**: `BIGQUERY_LIMITATIONS.md` - Known issues

### Troubleshooting
- Check Cloud Function logs for errors
- Verify GitHub token permissions
- Test API endpoint with curl commands above
- Review GitHub Pages build status

---

**Last Updated**: November 6, 2025
**Version**: 1.0
**For Form Builder API**: v1.1.0
**Maintainer**: Dayta Analytics - Form Builder Team

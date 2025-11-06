# Form Builder API - Deployment Runbook

**Version**: 1.1.0
**Last Updated**: November 6, 2025
**Maintainer**: DevOps Team

---

## 📋 Overview

This runbook provides step-by-step procedures for deploying, monitoring, and maintaining the Form Builder API in Google Cloud Functions.

**Use this runbook for**:
- Initial deployment
- Version updates
- Configuration changes
- Troubleshooting
- Rollback procedures

---

## 🎯 Prerequisites

### Required Access
- [ ] Google Cloud Project: `opex-data-lake-k23k4y98m`
- [ ] IAM Roles:
  - `roles/cloudfunctions.developer`
  - `roles/iam.serviceAccountUser`
  - `roles/bigquery.dataViewer`

### Required Tools
- [ ] Google Cloud SDK (`gcloud`) installed
- [ ] Authenticated to GCP: `gcloud auth login`
- [ ] Project set: `gcloud config set project opex-data-lake-k23k4y98m`

### Required Information
- [ ] JWT Secret Key
- [ ] GitHub Personal Access Token (optional, for deployment feature)
- [ ] GitHub Repository details (if using deployment)

---

## 🚀 Deployment Procedures

### Procedure 1: Initial Deployment

**When to use**: First-time setup of Form Builder API

**Estimated time**: 10-15 minutes

**Steps**:

1. **Navigate to project directory**
   ```bash
   cd "/Users/landoncolvig/Documents/opex-technologies/Q4 form scoring project/backend/form_builder"
   ```

2. **Verify files are present**
   ```bash
   ls -la
   # Should see: main.py, form_template.html, requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export JWT_SECRET_KEY="your-secret-key-here"
   export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"  # Optional
   ```

4. **Deploy to Cloud Functions**
   ```bash
   gcloud functions deploy form-builder-api \
     --gen2 \
     --runtime=python310 \
     --region=us-central1 \
     --source=. \
     --entry-point=form_builder_handler \
     --trigger-http \
     --allow-unauthenticated \
     --set-env-vars="PROJECT_ID=opex-data-lake-k23k4y98m,DATASET_ID=form_builder,JWT_SECRET_KEY=$JWT_SECRET_KEY,GITHUB_TOKEN=$GITHUB_TOKEN,GITHUB_REPO_OWNER=opextech,GITHUB_REPO_NAME=forms,GITHUB_BRANCH=main" \
     --timeout=60s \
     --memory=512MB \
     --max-instances=60
   ```

5. **Wait for deployment** (2-5 minutes)
   ```
   Look for: "Deploying function... DONE"
   ```

6. **Get function URL**
   ```bash
   gcloud functions describe form-builder-api --region=us-central1 --gen2 --format="value(serviceConfig.uri)"
   ```

   Expected: `https://form-builder-api-xxxxxxxxxx-uc.a.run.app`

7. **Verify deployment**
   ```bash
   curl "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api/form-builder/questions?page_size=1" \
     -H "Authorization: Bearer $TOKEN"
   ```

   Expected: 200 response with questions

**Rollback procedure**: N/A (initial deployment)

---

### Procedure 2: Update Deployment (Code Changes)

**When to use**: After code changes in main.py or form_template.html

**Estimated time**: 5-10 minutes

**Steps**:

1. **Verify changes**
   ```bash
   git status
   git diff main.py
   ```

2. **Test locally** (optional but recommended)
   ```bash
   functions-framework --target=form_builder_handler --debug
   # Test on http://localhost:8080
   ```

3. **Deploy updated function**
   ```bash
   gcloud functions deploy form-builder-api \
     --gen2 \
     --runtime=python310 \
     --region=us-central1 \
     --source=. \
     --entry-point=form_builder_handler \
     --trigger-http \
     --allow-unauthenticated \
     --timeout=60s \
     --memory=512MB
   ```

4. **Monitor deployment logs**
   ```bash
   gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=20 --follow
   ```

5. **Test updated function**
   ```bash
   # Run test script
   ./test_api.sh

   # Or manual test
   curl "$API_URL/form-builder/templates" -H "Authorization: Bearer $TOKEN"
   ```

6. **Verify specific changes**
   - Test the specific functionality that was changed
   - Check logs for errors
   - Verify response format

**Rollback procedure**: See Procedure 5

---

### Procedure 3: Update Environment Variables

**When to use**: Changing JWT secret, GitHub token, or other config

**Estimated time**: 3-5 minutes

**Steps**:

1. **List current environment variables**
   ```bash
   gcloud functions describe form-builder-api --region=us-central1 --gen2 --format="value(serviceConfig.environmentVariables)"
   ```

2. **Update environment variables**
   ```bash
   gcloud functions deploy form-builder-api \
     --gen2 \
     --region=us-central1 \
     --update-env-vars="JWT_SECRET_KEY=new-secret,GITHUB_TOKEN=new-token"
   ```

   **Note**: This only updates specified variables, others remain unchanged

3. **Verify update**
   ```bash
   gcloud functions describe form-builder-api --region=us-central1 --gen2 --format="value(serviceConfig.environmentVariables)"
   ```

4. **Test with new credentials**
   - Get new JWT token with new secret
   - Test API endpoints
   - Verify GitHub deployment (if token changed)

**Rollback procedure**:
```bash
# Redeploy with old values
gcloud functions deploy form-builder-api --gen2 --region=us-central1 --update-env-vars="JWT_SECRET_KEY=old-secret"
```

---

### Procedure 4: Scale Configuration Update

**When to use**: Adjusting memory, timeout, or max instances

**Estimated time**: 2-3 minutes

**Steps**:

1. **Current configuration**
   ```bash
   gcloud functions describe form-builder-api --region=us-central1 --gen2 \
     --format="value(serviceConfig.availableMemory,serviceConfig.timeoutSeconds,serviceConfig.maxInstanceCount)"
   ```

2. **Update scaling configuration**
   ```bash
   gcloud functions deploy form-builder-api \
     --gen2 \
     --region=us-central1 \
     --memory=1024MB \          # Options: 128MB, 256MB, 512MB, 1024MB, 2048MB, 4096MB
     --timeout=120s \           # Max: 540s (9 minutes)
     --max-instances=100        # Adjust based on load
   ```

3. **Monitor performance**
   ```bash
   # Check function metrics
   gcloud functions describe form-builder-api --region=us-central1 --gen2
   ```

**When to increase memory/timeout**:
- Seeing timeout errors in logs
- High memory usage (> 80%)
- Preview generation taking too long

**When to increase max instances**:
- High request rate
- Seeing cold start latency
- Traffic spikes expected

---

### Procedure 5: Rollback to Previous Version

**When to use**: Critical bug in new deployment

**Estimated time**: 5-10 minutes

**Steps**:

1. **List recent revisions**
   ```bash
   gcloud functions describe form-builder-api --region=us-central1 --gen2 \
     --format="value(serviceConfig.revision)"
   ```

   Current revision format: `form-builder-api-00005-kad`

2. **Check revision history**
   ```bash
   # View all revisions
   gcloud run revisions list --region=us-central1 --service=form-builder-api
   ```

3. **Identify working revision**
   - Find last known good revision number
   - Check deployment history in DEPLOYMENT_SUMMARY.md

4. **Rollback deployment**
   ```bash
   # Method 1: Redeploy from previous source
   cd /path/to/previous/version
   gcloud functions deploy form-builder-api --gen2 --region=us-central1 --source=.

   # Method 2: Set traffic to previous revision (Cloud Run)
   gcloud run services update-traffic form-builder-api \
     --region=us-central1 \
     --to-revisions=form-builder-api-00004-hut=100
   ```

5. **Verify rollback**
   ```bash
   # Test API
   curl "$API_URL/form-builder/templates" -H "Authorization: Bearer $TOKEN"

   # Check logs
   gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=20
   ```

6. **Update documentation**
   - Note rollback in DEPLOYMENT_SUMMARY.md
   - Document issue in incident log
   - Create ticket for fix

---

## 📊 Monitoring Procedures

### Procedure 6: View Logs

**Real-time logs**:
```bash
gcloud functions logs read form-builder-api --region=us-central1 --gen2 --follow
```

**Recent logs** (last 50):
```bash
gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=50
```

**Filter by severity**:
```bash
# Errors only
gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=50 | grep ERROR

# Warnings and errors
gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=50 | grep -E "ERROR|WARNING"
```

**Search logs**:
```bash
# Search for specific template ID
gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=100 | grep "template_id_here"

# Search for GitHub deployments
gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=100 | grep "deploy"
```

**Time-based logs**:
```bash
# Logs from last hour
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=form-builder-api" \
  --limit=50 \
  --freshness=1h
```

---

### Procedure 7: Check Function Health

**Steps**:

1. **Function status**
   ```bash
   gcloud functions describe form-builder-api --region=us-central1 --gen2 --format="value(state)"
   ```

   Expected: `ACTIVE`

2. **Service endpoint**
   ```bash
   gcloud functions describe form-builder-api --region=us-central1 --gen2 --format="value(serviceConfig.uri)"
   ```

3. **Health check**
   ```bash
   # Quick health check
   curl "$API_URL/form-builder/questions?page_size=1" -H "Authorization: Bearer $TOKEN"
   ```

4. **Check metrics** (via Cloud Console)
   - Invocations per second
   - Error rate
   - Execution time (p50, p95, p99)
   - Memory usage
   - Active instances

---

### Procedure 8: Performance Analysis

**View metrics**:
```bash
# Get function details
gcloud functions describe form-builder-api --region=us-central1 --gen2
```

**Analyze logs for performance**:
```bash
# Find slow requests
gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=1000 | grep -E "took [0-9]{4,}ms"

# Count requests by endpoint
gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=1000 | grep "form-builder" | cut -d' ' -f10 | sort | uniq -c | sort -rn
```

**Metrics to monitor**:
- Average response time: < 500ms (most endpoints)
- Error rate: < 1%
- Cold start frequency
- Memory usage: < 80% of allocated
- Instance count vs max instances

---

## 🔧 Maintenance Procedures

### Procedure 9: Update Dependencies

**When to use**: Security patches, library updates

**Estimated time**: 10-15 minutes

**Steps**:

1. **Review current dependencies**
   ```bash
   cat requirements.txt
   ```

2. **Check for updates**
   ```bash
   # In local environment
   pip list --outdated
   ```

3. **Test updates locally**
   ```bash
   # Create virtual environment
   python3 -m venv test_env
   source test_env/bin/activate

   # Install updated dependencies
   pip install -r requirements.txt --upgrade

   # Test locally
   functions-framework --target=form_builder_handler
   ```

4. **Update requirements.txt**
   ```bash
   pip freeze > requirements.txt
   ```

5. **Deploy with updated dependencies**
   ```bash
   gcloud functions deploy form-builder-api --gen2 --region=us-central1 --source=.
   ```

6. **Test thoroughly**
   ```bash
   ./test_api.sh
   ```

---

### Procedure 10: Database Maintenance

**BigQuery table optimization**:

1. **Check table sizes**
   ```bash
   bq show --format=prettyjson opex-data-lake-k23k4y98m:form_builder.form_templates
   bq show --format=prettyjson opex-data-lake-k23k4y98m:form_builder.template_questions
   ```

2. **Query performance check**
   ```sql
   -- Run in BigQuery Console
   SELECT
     creation_time,
     total_slot_ms,
     total_bytes_processed
   FROM `opex-data-lake-k23k4y98m`.`region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
   WHERE job_type = 'QUERY'
     AND statement_type = 'SELECT'
     AND referenced_tables LIKE '%form_templates%'
   ORDER BY creation_time DESC
   LIMIT 10
   ```

3. **Clean up old test data** (if needed)
   ```sql
   -- Find old test templates
   SELECT template_id, template_name, created_at
   FROM `opex-data-lake-k23k4y98m.form_builder.form_templates`
   WHERE template_name LIKE 'Test%'
     AND created_at < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
   ```

---

### Procedure 11: GitHub Integration Maintenance

**Update GitHub token**:

1. **Generate new token** (GitHub → Settings → Developer settings → Personal access tokens)

2. **Update environment variable**
   ```bash
   gcloud functions deploy form-builder-api \
     --gen2 \
     --region=us-central1 \
     --update-env-vars="GITHUB_TOKEN=new_token_here"
   ```

3. **Test deployment**
   ```bash
   curl -X POST "$API_URL/form-builder/templates/TEMPLATE_ID/deploy" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"commit_message": "Test deployment after token update"}'
   ```

**Verify GitHub Pages**:
- Check repository: https://github.com/opextech/forms
- Check Pages site: https://opextech.github.io/forms/
- Verify latest forms are accessible

---

## 🚨 Troubleshooting Procedures

### Procedure 12: Debug 500 Errors

**Steps**:

1. **Check recent logs**
   ```bash
   gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=50 | grep ERROR
   ```

2. **Identify error pattern**
   - BigQuery query errors?
   - GitHub API errors?
   - Python exceptions?

3. **Common causes and fixes**:

   **BigQuery errors**:
   ```bash
   # Check BigQuery permissions
   gcloud projects get-iam-policy opex-data-lake-k23k4y98m --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:serviceAccount"
   ```

   **GitHub API errors**:
   - Check token validity
   - Check rate limits
   - Verify repository exists

   **Python exceptions**:
   - Check recent code changes
   - Review stack trace in logs
   - Test locally with same data

4. **Enable debug logging** (if needed)
   - Add print statements to code
   - Redeploy
   - Reproduce issue
   - Review detailed logs

---

### Procedure 13: Debug Deployment Failures

**Symptoms**: Forms not appearing on GitHub Pages

**Steps**:

1. **Check deployment response**
   ```bash
   # Should return deployed_url and commit_sha
   curl -X POST "$API_URL/form-builder/templates/TEMPLATE_ID/deploy" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{}'
   ```

2. **Verify file in GitHub**
   - Go to https://github.com/opextech/forms
   - Check `forms/` directory
   - Verify file exists with correct name

3. **Check GitHub Pages build**
   - Repository → Actions tab
   - Look for "pages-build-deployment" workflow
   - Check for errors

4. **Common issues**:
   - **GitHub token expired**: Update token (Procedure 11)
   - **Repository doesn't exist**: Create repository
   - **Pages not enabled**: Enable in repository settings
   - **Wrong branch**: Check GITHUB_BRANCH env var

---

### Procedure 14: Debug Authentication Issues

**Symptoms**: 401 Unauthorized errors

**Steps**:

1. **Verify token is valid**
   ```bash
   # Check token expiration
   echo $TOKEN | cut -d'.' -f2 | base64 --decode | jq .exp

   # Compare to current time
   date +%s
   ```

2. **Verify JWT secret matches**
   ```bash
   # Check function's JWT secret (first few chars)
   gcloud functions describe form-builder-api --region=us-central1 --gen2 --format="value(serviceConfig.environmentVariables.JWT_SECRET_KEY)" | cut -c1-10
   ```

3. **Test with fresh token**
   ```bash
   # Get new token from auth API
   curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/login \
     -d '{"email":"user@example.com","password":"password"}'
   ```

4. **Check auth middleware logs**
   ```bash
   gcloud functions logs read form-builder-api --region=us-central1 --gen2 --limit=50 | grep -i auth
   ```

---

## 📚 Reference Information

### Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `PROJECT_ID` | Yes | - | GCP Project ID |
| `DATASET_ID` | Yes | `form_builder` | BigQuery dataset |
| `JWT_SECRET_KEY` | Yes | - | JWT token validation |
| `GITHUB_TOKEN` | No | `""` | GitHub API access |
| `GITHUB_REPO_OWNER` | No | `opextech` | GitHub repository owner |
| `GITHUB_REPO_NAME` | No | `forms` | GitHub repository name |
| `GITHUB_BRANCH` | No | `main` | Target branch |

### Resource Limits

| Resource | Current | Max | Notes |
|----------|---------|-----|-------|
| Memory | 512MB | 8192MB | Increase if needed |
| Timeout | 60s | 540s | Increase for large templates |
| Max Instances | 60 | 1000 | Adjust for traffic |
| Concurrent Requests | 1 | 1000 | Per instance |

### Important URLs

- **API Base**: https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api
- **Cloud Console**: https://console.cloud.google.com/functions/details/us-central1/form-builder-api?project=opex-data-lake-k23k4y98m
- **GitHub Repo**: https://github.com/opextech/forms
- **GitHub Pages**: https://opextech.github.io/forms/

### Support Contacts

- **Primary**: DevOps Team
- **Secondary**: Backend Development Team
- **Emergency**: On-call Engineer

---

## 📝 Change Log Template

**When making changes, document here:**

| Date | Version | Revision | Changes | Deployed By |
|------|---------|----------|---------|-------------|
| 2025-11-06 | 1.1.0 | form-builder-api-00005-kad | Added GitHub deployment | DevOps |
| 2025-11-06 | 1.0.4 | form-builder-api-00004-hut | Fixed Info weight | DevOps |

---

## ✅ Deployment Checklist

**Use this checklist for each deployment:**

### Pre-Deployment
- [ ] Code changes reviewed
- [ ] Local testing completed
- [ ] Test script passed (`./test_api.sh`)
- [ ] Environment variables verified
- [ ] Backup plan ready

### Deployment
- [ ] Deployment command executed
- [ ] Build completed successfully
- [ ] Function status is ACTIVE
- [ ] URL accessible

### Post-Deployment
- [ ] API health check passed
- [ ] Test script passed in production
- [ ] Logs reviewed (no errors)
- [ ] Documentation updated
- [ ] Change log updated
- [ ] Team notified

### Rollback (if needed)
- [ ] Previous version identified
- [ ] Rollback procedure executed
- [ ] Service restored
- [ ] Incident documented

---

**Last Updated**: November 6, 2025
**Version**: 1.0
**Next Review**: December 6, 2025

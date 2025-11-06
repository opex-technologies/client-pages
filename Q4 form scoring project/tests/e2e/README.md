# End-to-End Testing Suite

Comprehensive E2E tests for the Form Builder & Response Scorer System.

## Overview

This test suite validates the complete user journey through the system:

1. **Authentication** - User registration and login
2. **Template Creation** - Creating forms with questions
3. **Form Preview** - Generating HTML previews
4. **Response Submission** - Submitting form responses (public)
5. **Scoring** - Automatic scoring of responses
6. **Analytics** - Viewing statistics and exporting data

## Test Approaches

We provide two testing approaches:

### 1. Bash Script (Recommended for CI/CD)
Simple shell script using curl and jq.

**Pros**:
- No Python dependencies
- Fast execution
- Easy to integrate into CI/CD
- Works in any bash environment

**Cons**:
- Limited assertions
- Less detailed error messages

### 2. Python/Pytest (Recommended for Development)
Full-featured test suite with pytest.

**Pros**:
- Detailed test reports
- Better error messages
- HTML test reports
- More maintainable

**Cons**:
- Requires Python + dependencies
- Slightly slower

---

## Quick Start

### Option 1: Bash Script

```bash
# Install jq (if not already installed)
brew install jq  # macOS
# or
sudo apt-get install jq  # Linux

# Run tests
cd tests/e2e
./run_e2e_tests.sh
```

### Option 2: Python/Pytest

```bash
# Install dependencies
cd tests/e2e
pip3 install -r requirements.txt

# Run tests
pytest test_complete_workflow.py -v

# Generate HTML report
pytest test_complete_workflow.py -v --html=report.html --self-contained-html
```

---

## Test Coverage

### Authentication Tests
- ✅ User registration
- ⚠️ User login (skipped due to BigQuery limitation)
- ⚠️ Token refresh (depends on login)

### Form Builder Tests
- ✅ Query question database
- ✅ Create template
- ✅ Retrieve template details
- ✅ Generate form preview
- ⚠️ Deploy to GitHub (requires GitHub token)

### Response Scorer Tests
- ✅ Submit response (PUBLIC - no auth)
- ✅ List responses
- ✅ Get response details
- ✅ Calculate scores automatically
- ✅ View analytics summary
- ✅ Export to CSV
- ✅ Delete response

### Integration Tests
- ✅ End-to-end workflow
- ✅ Data consistency across APIs
- ✅ Error handling
- ✅ Cleanup after tests

---

## Known Limitations

### BigQuery Streaming Buffer
The authentication system uses BigQuery, which has a 90-minute streaming buffer delay for UPDATE/DELETE operations. This means:

- ✅ User **registration** works immediately
- ❌ User **login** fails for newly registered users (password check requires reading updated data)
- ⏳ Wait 90 minutes OR use existing user account

**Workarounds**:
1. Use existing user credentials (see "Testing with Existing User" below)
2. Wait 90 minutes after registration
3. Migrate to Firestore (planned - see backend/auth/BIGQUERY_LIMITATIONS.md)

### Template CRUD Operations
Same limitation affects template updates:
- ✅ Create template - works immediately
- ❌ Update/delete template - requires 90-minute wait
- ✅ Read template - works immediately

---

## Testing with Existing User

To test the full workflow without waiting for BigQuery, use an existing user:

### Method 1: Set Environment Variable

```bash
# Get a valid token first
export TEST_TOKEN="your-jwt-token-here"

# Modify script to use existing token
# (See "Advanced Usage" below)
```

### Method 2: Create Admin User First

```bash
# Wait 90+ minutes after registration
cd "Q4 form scoring project/backend/auth"
python3 create_admin.py

# Use those credentials in tests
```

---

## Running Individual Tests

### Bash Script

```bash
# Run specific section
# Edit run_e2e_tests.sh and comment out unwanted tests

# Or use existing token
export ACCESS_TOKEN="your-token"
./run_e2e_tests.sh
```

### Python/Pytest

```bash
# Run specific test class
pytest test_complete_workflow.py::TestAuthenticationWorkflow -v

# Run specific test
pytest test_complete_workflow.py::TestResponseWorkflow::test_07_submit_response -v

# Run with markers
pytest test_complete_workflow.py -m "not auth" -v
```

---

## Test Results

### Expected Results (with BigQuery limitation)

```
================================================
Test Summary
================================================
Passed:  1   ✓ (Registration only)
Failed:  0
Skipped: 10  ⚠️ (Waiting for login to work)
================================================
```

### Expected Results (with existing token)

```
================================================
Test Summary
================================================
Passed:  11  ✓ (All tests)
Failed:  0
Skipped: 0
================================================
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install jq
        run: sudo apt-get install -y jq

      - name: Run E2E Tests
        env:
          TEST_TOKEN: ${{ secrets.E2E_TEST_TOKEN }}
        run: |
          cd "Q4 form scoring project/tests/e2e"
          ./run_e2e_tests.sh
```

---

## Advanced Usage

### Custom Configuration

Edit configuration in test files:

**Bash Script** (`run_e2e_tests.sh`):
```bash
# Line 12-15
BASE_URL="https://your-custom-url.com"
AUTH_API="$BASE_URL/auth-api"
FORM_BUILDER_API="$BASE_URL/form-builder-api"
RESPONSE_SCORER_API="$BASE_URL/response-scorer-api"
```

**Python** (`test_complete_workflow.py`):
```python
# Line 24-27
BASE_URL = "https://your-custom-url.com"
AUTH_API = f"{BASE_URL}/auth-api"
FORM_BUILDER_API = f"{BASE_URL}/form-builder-api"
RESPONSE_SCORER_API = f"{BASE_URL}/response-scorer-api"
```

### Testing Locally

Point tests to local development servers:

```bash
# In run_e2e_tests.sh
BASE_URL="http://localhost:8080"
```

### Debugging

**Bash Script**:
```bash
# Add -x for debug mode
bash -x run_e2e_tests.sh

# Check response bodies
# Uncomment echo statements in script
```

**Python**:
```bash
# Verbose output
pytest test_complete_workflow.py -v -s

# Debug mode
pytest test_complete_workflow.py --pdb

# Print response bodies
pytest test_complete_workflow.py -v -s --log-cli-level=DEBUG
```

---

## Test Data Cleanup

Both test scripts automatically clean up after themselves:
- Delete created templates
- Delete submitted responses
- No manual cleanup needed

If tests fail before cleanup:

```bash
# Manual cleanup via API
curl -X DELETE "https://.../templates/TEMPLATE_ID" \
  -H "Authorization: Bearer TOKEN"

curl -X DELETE "https://.../responses/RESPONSE_ID" \
  -H "Authorization: Bearer TOKEN"
```

Or via BigQuery:

```sql
-- Delete test data
DELETE FROM `opex-data-lake-k23k4y98m.form_builder.form_templates`
WHERE template_name LIKE '%E2E Test%';

DELETE FROM `opex-data-lake-k23k4y98m.scoring.responses`
WHERE submitter_email LIKE '%e2e-test%';
```

---

## Troubleshooting

### Tests Skip Due to Auth
**Problem**: Most tests skip due to missing auth token
**Solution**: Use existing user or wait 90 minutes after registration

### jq: command not found
**Problem**: jq not installed
**Solution**: `brew install jq` (macOS) or `sudo apt-get install jq` (Linux)

### Connection Refused
**Problem**: APIs not accessible
**Solution**: Check Cloud Functions are deployed and URLs are correct

### Template Creation Fails
**Problem**: Questions not found
**Solution**: Verify question database is migrated (1,041 questions should exist)

### Cleanup Errors
**Problem**: Can't delete template/response
**Solution**: BigQuery limitation - wait 90 minutes or ignore (data will be overwritten)

---

## Metrics & Reporting

### Bash Script Output
- Color-coded results
- Pass/Fail/Skip counts
- Execution time
- Exit code (0 = success, 1 = failure)

### Python/Pytest Output
```bash
# HTML Report
pytest test_complete_workflow.py --html=report.html

# JUnit XML (for CI)
pytest test_complete_workflow.py --junitxml=results.xml

# Code coverage
pytest test_complete_workflow.py --cov=. --cov-report=html
```

---

## Best Practices

1. **Run tests before deployment** - Catch issues early
2. **Use CI/CD integration** - Automate testing
3. **Monitor test results** - Track pass rates over time
4. **Keep tests updated** - Reflect latest API changes
5. **Clean up test data** - Prevent database pollution

---

## Next Steps

### Planned Enhancements
- [ ] Add performance benchmarks
- [ ] Add load testing (concurrent users)
- [ ] Add security testing (injection, XSS)
- [ ] Add visual regression testing (frontend)
- [ ] Add database state validation
- [ ] Add email notification testing
- [ ] Add file upload testing (when implemented)

### Integration Testing
- [ ] Test with real GitHub deployments
- [ ] Test email notifications (when implemented)
- [ ] Test webhooks (when implemented)
- [ ] Test SSO integration (when implemented)

---

## Support

**Issues**: Report to project team
**Documentation**: See [DEPLOYMENT.md](../../DEPLOYMENT.md)
**API Docs**: See backend/*/API_SPEC.md

---

**Version**: 1.0.0
**Last Updated**: November 5, 2025
**Maintainer**: Dayta Analytics

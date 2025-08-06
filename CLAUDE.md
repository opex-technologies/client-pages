# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Information

- **GitHub Repository**: https://github.com/landoncolvig/opex-technologies
- **Main Branch**: `main`

## Repository Overview

This is the Opex Technologies repository for web forms and data collection infrastructure. It contains:
- **Web Forms**: HTML forms for initial contact and network security surveys (SASE)
- **Backend Cloud Function**: Google Cloud Function for processing form submissions to BigQuery
- **Data Backloading**: Scripts for importing historical SASE RFI data into the same BigQuery tables

## Architecture

### Form Collection Pipeline
```
HTML Forms → Cloud Function (webhook) → BigQuery → Analytics
```

1. **HTML Forms** (`/Web/`) - Standalone forms with embedded JavaScript
2. **Cloud Function** (`/backend/main.py`) - Processes form submissions via webhook
3. **BigQuery Storage** - Data stored in `opex_dev` dataset with dynamic table creation
4. **Backloading** (`/backload-data/`) - Historical data integration scripts

### Key Components

- **Cloud Function**: `backend/main.py` - Webhook endpoint at `https://opex-form-webhook-4jypryamoq-uc.a.run.app`
- **Forms**: 
  - `Web/initialwebpage.html` - Contact form
  - `Web/networksurvey.html` - SASE network security survey
- **BigQuery Dataset**: `opex_dev` with dynamic table creation based on form structure
- **Static Assets**: Logo hosted at `https://storage.googleapis.com/opex-web-forms-20250716-145646/opex-logo.avif`

## Development Commands

### Backend (Google Cloud Function)
```bash
# Deploy Cloud Function
gcloud functions deploy opex-form-webhook \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-central1 \
  --source backend/

# View logs
gcloud functions logs read opex-form-webhook --region us-central1
```

### Data Backloading
```bash
cd backload-data/
pip install -r requirements.txt

# Run backload process
python3 backload_sase_rfi.py

# Verify data integrity
python3 verify_data.py
```

### Web Forms
Forms are static HTML files that can be opened directly in browsers or served via any web server. They submit to the deployed Cloud Function webhook.

## Data Schema

### Form Submission Format
All forms submit JSON to the webhook endpoint:
```json
{
  "formName": "form-identifier",
  "formData": {
    "field_name": "value",
    "timestamp": "2023-XX-XXTXX:XX:XX.XXXZ",
    "source": "form-source-identifier"
  }
}
```

### BigQuery Tables
- Tables are created dynamically based on form data structure
- Field names are sanitized (spaces → underscores, lowercase)
- Schema adapts automatically to new fields
- All tables include `inserted_at` timestamp field

## Key Features

### Dynamic Table Creation
The Cloud Function automatically:
- Creates BigQuery tables if they don't exist
- Adds new columns when forms introduce new fields
- Handles schema evolution gracefully
- Supports text, numeric, and timestamp field types

### Form Integration
- Both HTML forms use the same webhook endpoint
- Forms include progress tracking and validation
- Responsive design with Opex Technologies branding
- Error handling and success feedback

### Historical Data Integration
- SASE RFI backloading maintains data consistency
- Question mapping between CSV and form structure
- Response normalization for radio/text/number fields
- Comprehensive validation and error handling

## Working with Forms

When modifying forms:
1. Update the JavaScript question arrays to match your requirements
2. Ensure field naming follows the sanitization pattern: `question.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase()`
3. The Cloud Function will automatically adapt the BigQuery schema
4. Test submissions end-to-end including BigQuery data verification

## Working with the Backend

The Cloud Function handles:
- CORS for web form submissions
- Dynamic schema management
- Retry logic with exponential backoff
- Comprehensive error logging
- Input validation and sanitization

Key environment considerations:
- Runs in Google Cloud Functions Python 3.10 runtime
- Uses service account authentication for BigQuery access
- Processes both contact forms and survey data uniformly

## Data Analysis

Query the collected data:
```sql
-- View all form submissions
SELECT * FROM `opex-data-lake-k23k4y98m.opex_dev.contact_form`
SELECT * FROM `opex-data-lake-k23k4y98m.opex_dev.network_security_survey`

-- Compare historical vs new survey data
SELECT source, COUNT(*) as submissions
FROM `opex-data-lake-k23k4y98m.opex_dev.network_security_survey`
GROUP BY source
```
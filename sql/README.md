# BigQuery Survey Response View

## Overview

The `scoring.all_survey_responses` view automatically unpivots all survey data from the `opex_dev` dataset into a normalized format where each row represents a single question-answer pair.

## View Structure

The view transforms data from wide format (one column per question) to long format (one row per question):

| Column | Description |
|--------|-------------|
| timestamp | Submission timestamp (from timestamp or inserted_at) |
| source | Data source identifier |
| contact_name | Contact person's name |
| contact_email | Contact person's email |
| contact_company | Contact person's company |
| contact_phone | Contact person's phone |
| company_name | Company name |
| survey_type | Type of survey (table name) |
| question | Question identifier (column name) |
| answer | Answer value (converted to string) |
| inserted_at | BigQuery insertion timestamp |

## Automatic Updates

The view automatically includes new forms/tables without code changes:

1. **New Tables**: When a new form creates a table in `opex_dev`, run the refresh script
2. **New Questions**: When existing forms add new questions (columns), run the refresh script
3. **Dynamic Schema**: The view adapts to tables with different metadata columns

## Usage Examples

### Query all responses for a specific survey
```sql
SELECT * FROM `opex-data-lake-k23k4y98m.scoring.all_survey_responses`
WHERE survey_type = 'network_security_survey'
```

### Count responses by question across all surveys
```sql
SELECT question, COUNT(*) as response_count
FROM `opex-data-lake-k23k4y98m.scoring.all_survey_responses`
GROUP BY question
ORDER BY response_count DESC
```

### Find all responses from a specific contact
```sql
SELECT survey_type, question, answer, timestamp
FROM `opex-data-lake-k23k4y98m.scoring.all_survey_responses`
WHERE contact_email = 'user@example.com'
ORDER BY timestamp, survey_type, question
```

## Maintenance

To refresh the view when new tables are added:

```bash
cd /Users/landoncolvig/Documents/opex-technologies/sql
python3 generate_survey_view.py
```

Or deploy the Cloud Function for automatic updates:
```bash
gcloud functions deploy refresh-survey-view \
  --runtime python310 \
  --trigger-http \
  --allow-unauthenticated \
  --region us-central1 \
  --source ../backend/ \
  --entry-point refresh_survey_view
```

## Files

- `generate_survey_view.py` - Script to generate and update the view
- `create_all_survey_responses.sql` - Generated SQL for the view
- `../backend/refresh_survey_view.py` - Cloud Function for automatic updates
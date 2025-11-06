# Database Schemas & Deployment

This directory contains all BigQuery schema definitions and deployment scripts for the Q4 Form Scoring Project.

## Directory Structure

```
database/
├── schemas/          # SQL schema files for all tables
├── migrations/       # Data migration scripts
├── seed_data/        # Initial data seeding scripts
├── queries/          # Common SQL queries
├── backups/          # Database backups
├── deploy_schemas.py # Master deployment script
└── README.md         # This file
```

## Table Schemas

### Authentication (`auth` dataset)
- **users** - User accounts and authentication data
- **permission_groups** - Role-based access control (RBAC)
- **sessions** - Active user sessions and JWT tokens

### Form Builder (`form_builder` dataset)
- **form_templates** - Survey form templates
- **question_database** - Master question repository (1,042 questions)

### Scoring (`scoring` dataset)
- **scored_responses** - Completed scores (summary level)
- **question_scores** - Individual question scores (detail level)
- **audit_trail** - Comprehensive audit log

### Operational (`opex_dev` dataset)
- **providers** - Service providers (vendors)
- **clients** - Opex Technologies clients
- *(Existing survey response tables remain unchanged)*

## Quick Start

### Deploy All Schemas

```bash
# Install dependencies
pip install google-cloud-bigquery

# Set GCP credentials (if not already set)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/opex-data-lake-k23k4y98m-credentials.json"

# Run deployment
python deploy_schemas.py
```

### Dry Run (Test Without Deploying)

```bash
python deploy_schemas.py --dry-run
```

### Deploy Specific Tables Only

```bash
# Deploy just users and permissions tables
python deploy_schemas.py --tables users,permission_groups
```

### Skip Verification

```bash
# Deploy without post-deployment verification
python deploy_schemas.py --skip-verify
```

## Deployment Script Features

The `deploy_schemas.py` script automatically:

1. **Creates datasets** if they don't exist (`auth`, `form_builder`, `scoring`)
2. **Deploys all table schemas** from SQL files
3. **Handles existing tables** gracefully (skips if already exists)
4. **Verifies deployments** by checking table existence and schema
5. **Provides colored output** for easy reading
6. **Supports dry-run mode** for testing
7. **Allows selective deployment** of specific tables

## Schema Files

All schema files are in `schemas/` directory:

| File | Table | Description |
|------|-------|-------------|
| `auth_users.sql` | auth.users | User accounts |
| `auth_permission_groups.sql` | auth.permission_groups | Permissions |
| `auth_sessions.sql` | auth.sessions | Session tracking |
| `form_templates.sql` | form_builder.form_templates | Form templates |
| `question_database.sql` | form_builder.question_database | Question repo |
| `scored_responses.sql` | scoring.scored_responses | Score summaries |
| `question_scores.sql` | scoring.question_scores | Score details |
| `audit_trail.sql` | scoring.audit_trail | Audit log |
| `providers.sql` | opex_dev.providers | Provider list |
| `clients.sql` | opex_dev.clients | Client list |

## Data Migration

### Question Database Migration

The Question Database CSV (1,042 questions) will be migrated using:

```bash
python migrations/migrate_question_database.py
```

This script:
- Reads `Question Database(Sheet1).csv`
- Generates UUIDs for question_id
- Maps columns to BigQuery schema
- Loads data into `form_builder.question_database`
- Validates data integrity

*(Migration script will be created in Task 1.3)*

## Indexes

For optimal query performance, create indexes after initial deployment:

```sql
-- User email lookup
CREATE INDEX idx_users_email ON `opex-data-lake-k23k4y98m.auth.users`(email);

-- Permission filtering
CREATE INDEX idx_permissions_user ON `opex-data-lake-k23k4y98m.auth.permission_groups`(user_id);

-- Template filtering
CREATE INDEX idx_templates_status ON `opex-data-lake-k23k4y98m.form_builder.form_templates`(status);

-- Score lookups
CREATE INDEX idx_scores_company ON `opex-data-lake-k23k4y98m.scoring.scored_responses`(company_name);
CREATE INDEX idx_scores_survey ON `opex-data-lake-k23k4y98m.scoring.scored_responses`(survey_type);

-- Audit trail queries
CREATE INDEX idx_audit_entity ON `opex-data-lake-k23k4y98m.scoring.audit_trail`(entity_type, entity_id);
CREATE INDEX idx_audit_user ON `opex-data-lake-k23k4y98m.scoring.audit_trail`(changed_by);
```

Note: BigQuery creates indexes automatically based on usage patterns, but explicit indexes can improve performance for known query patterns.

## Backup & Restore

### Backup All Tables

```bash
# Export all tables to Cloud Storage
bq extract --destination_format=NEWLINE_DELIMITED_JSON \
  'opex-data-lake-k23k4y98m:auth.users' \
  'gs://opex-backups/auth_users_*.json'
```

### Restore from Backup

```bash
# Import from Cloud Storage
bq load --source_format=NEWLINE_DELIMITED_JSON \
  'opex-data-lake-k23k4y98m:auth.users' \
  'gs://opex-backups/auth_users_*.json'
```

## Rollback

If deployment fails or needs to be rolled back:

```sql
-- Drop individual table
DROP TABLE IF EXISTS `opex-data-lake-k23k4y98m.auth.users`;

-- Drop entire dataset (careful!)
DROP SCHEMA IF EXISTS `opex-data-lake-k23k4y98m.auth` CASCADE;
```

Then re-run deployment script.

## Common Queries

Save frequently-used queries in `queries/` directory for easy access.

Example: `queries/user_permissions.sql`
```sql
-- Get all permissions for a user
SELECT
  u.email,
  u.full_name,
  pg.permission_level,
  pg.company,
  pg.category,
  pg.granted_at
FROM `opex-data-lake-k23k4y98m.auth.users` u
JOIN `opex-data-lake-k23k4y98m.auth.permission_groups` pg
  ON u.user_id = pg.user_id
WHERE u.email = 'user@example.com'
  AND pg.is_active = TRUE
ORDER BY pg.granted_at DESC;
```

## Troubleshooting

### "Permission denied" Error

Ensure your service account has these IAM roles:
- `roles/bigquery.dataEditor`
- `roles/bigquery.jobUser`

### "Dataset not found" Error

Run the deployment script - it will create missing datasets automatically.

### "Table already exists" Error

This is normal - the script skips existing tables. Use `--dry-run` to see what would be created.

### Schema Propagation Delays

BigQuery may take 1-2 seconds to propagate new datasets/tables. The deployment script includes automatic wait periods.

## Testing

After deployment, verify all tables exist:

```bash
# List all datasets
bq ls --project_id=opex-data-lake-k23k4y98m

# List tables in auth dataset
bq ls --project_id=opex-data-lake-k23k4y98m auth

# Show table schema
bq show opex-data-lake-k23k4y98m:auth.users

# Count rows (should be 0 for new tables)
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`opex-data-lake-k23k4y98m.auth.users\`"
```

## Next Steps

After deploying schemas:

1. ✅ Deploy all table schemas (Task 1.2.4)
2. ⏭️ Migrate Question Database CSV (Task 1.3)
3. ⏭️ Set up backend Cloud Functions (Task 1.4)
4. ⏭️ Implement authentication API (Task 1.5)

## Support

For issues with deployment:
- Check Cloud Logging: https://console.cloud.google.com/logs
- Review BigQuery jobs: https://console.cloud.google.com/bigquery
- Contact: landon@daytanalytics.com

---

**Last Updated:** November 5, 2025
**Project:** Q4 Form Scoring Project
**GCP Project:** opex-data-lake-k23k4y98m

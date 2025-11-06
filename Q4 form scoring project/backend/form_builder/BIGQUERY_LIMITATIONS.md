# BigQuery Limitations - Form Builder API

**Created**: November 6, 2025
**Status**: Known Issue - Workarounds Available

## Overview

The Form Builder API uses BigQuery for storing form templates and template-question associations. BigQuery has a known limitation with its **streaming buffer** that affects UPDATE and DELETE operations on recently inserted rows.

## The Limitation

### What Happens

When you create a form template via the API:
1. Template data is inserted into `form_builder.form_templates` table
2. Template-question associations inserted into `form_builder.template_questions` table
3. Both insertions use BigQuery streaming inserts for immediate availability

**However:**
- You CANNOT update the template for ~90 minutes after creation
- You CANNOT delete the template for ~90 minutes after creation
- This is a BigQuery platform limitation, not an API bug

### Error Message

```json
{
  "success": false,
  "error": {
    "message": "Internal server error",
    "code": "INTERNAL_ERROR",
    "details": {
      "error": "UPDATE or DELETE statement over table would affect rows in the streaming buffer, which is not supported"
    }
  }
}
```

### Root Cause

From [BigQuery Documentation](https://cloud.google.com/bigquery/docs/streaming-data-into-bigquery#dataavailability):

> "Data in the streaming buffer has some important differences compared to data in BigQuery storage:
> - **Streaming buffer data cannot be modified or deleted** for approximately 90 minutes after it is written.
> - Updates and deletes in a table are blocked if any data in the table is in the streaming buffer, even if the affected row is not in the buffer."

## Impact on Form Builder

### Affected Operations

| Operation | Status within 90min | Status after 90min |
|-----------|--------------------|--------------------|
| **Create Template** | ✅ Works | ✅ Works |
| **List Templates** | ✅ Works | ✅ Works |
| **Get Template** | ✅ Works | ✅ Works |
| **Update Template** | ❌ Fails | ✅ Works |
| **Delete Template** | ❌ Fails | ✅ Works |
| **Query Questions** | ✅ Works | ✅ Works |
| **Preview Template** | ✅ Works | ✅ Works |

### User Experience Impact

**Typical Workflow:**
1. User creates a new template → ✅ Works immediately
2. User realizes they made a mistake → ❌ Cannot update for 90 minutes
3. User tries to delete template → ❌ Cannot delete for 90 minutes

**This creates a poor user experience** for draft template iteration.

## Workarounds

### Option 1: Wait 90 Minutes ⏰

The simplest workaround is to wait 90 minutes after template creation before attempting updates or deletes.

**Pros:**
- No code changes required
- No infrastructure changes

**Cons:**
- Poor user experience
- Blocks rapid prototyping workflow
- Users cannot quickly fix mistakes

### Option 2: Implement Draft-Versioning Pattern 📝

Instead of updating templates, create new versions:

```python
# Instead of UPDATE
UPDATE form_templates SET template_name = 'New Name' WHERE id = 'abc123'

# Do this
INSERT INTO form_templates (id, parent_id, template_name, version, ...)
VALUES ('xyz789', 'abc123', 'New Name', 2, ...)
```

**Pros:**
- No migration required
- Works within BigQuery constraints
- Provides version history

**Cons:**
- More complex queries
- Increased storage costs
- Still can't hard-delete

### Option 3: Migrate to Firestore 🔥 (RECOMMENDED)

Migrate form_templates and template_questions to Cloud Firestore.

**Pros:**
- **Immediate updates and deletes**
- Better suited for transactional workloads
- Real-time synchronization
- Better developer experience
- **Same solution needed for auth system**

**Cons:**
- Requires migration effort (~6-8 hours)
- Different query patterns
- Slightly higher costs for reads/writes

### Option 4: Hybrid Approach (Quick Fix) 🔀

Keep question database in BigQuery, move templates to Firestore:

```
BigQuery (read-heavy):
- question_database (1,041 questions)
- scored_responses (historical data)

Firestore (write-heavy):
- form_templates (draft/edit workflow)
- template_questions (frequent changes)
```

**Pros:**
- Best of both worlds
- Questions stay in BigQuery (perfect fit)
- Templates in Firestore (immediate updates)
- Can be done incrementally

**Cons:**
- Managing two databases
- Slightly more complex queries

## Recommended Solution

### Short Term (Immediate)

1. **Add Warning to UI**: "Templates cannot be edited or deleted for 90 minutes after creation"
2. **Implement Validation**: Warn users before creating templates
3. **Error Handling**: Show friendly error messages when BigQuery blocks operation

### Long Term (Within 2 weeks)

**Migrate to Firestore** for the following reasons:

1. **Consistent with Auth System**: Auth already needs Firestore migration for same reason
2. **Better User Experience**: Immediate updates/deletes
3. **Right Tool for Job**: Firestore designed for document-based transactional data
4. **Unified Solution**: Solves problem for both auth and form builder

## Migration Plan

See [FIRESTORE_MIGRATION.md](./FIRESTORE_MIGRATION.md) for detailed migration steps.

**Estimated Effort:**
- Form Builder Migration: 6-8 hours
- Testing: 2-4 hours
- **Total**: 1-2 days

**Migration Priority**: HIGH (blocks smooth user workflow)

## Testing the Limitation

Run the comprehensive test script to see the limitation in action:

```bash
cd backend/form_builder
./test_api.sh
```

Tests 7 (Update) and some delete operations will fail with streaming buffer errors.

## Related Issues

- **Auth System**: Same limitation prevents login for newly registered users
- **See**: `backend/auth/BIGQUERY_LIMITATIONS.md`

## Current Status

**As of November 6, 2025:**
- ✅ Core API functionality working
- ⚠️ Update/Delete blocked by streaming buffer (90-minute delay)
- 🔄 Firestore migration recommended for both auth and form_builder
- 📋 Migration plan documented but not yet implemented

## References

- [BigQuery Streaming Data Limitations](https://cloud.google.com/bigquery/docs/streaming-data-into-bigquery#dataavailability)
- [BigQuery DML Limitations](https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#limitations)
- [Cloud Firestore](https://cloud.google.com/firestore)

---

**Last Updated**: November 6, 2025
**Maintainer**: Dayta Analytics - Form Builder Team

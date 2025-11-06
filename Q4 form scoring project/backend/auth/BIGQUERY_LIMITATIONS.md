# BigQuery Limitations for Authentication Workloads

**Date**: November 5, 2025
**Status**: ⚠️ CRITICAL ARCHITECTURAL ISSUE
**Priority**: HIGH

## Problem Summary

The authentication API is deployed and functional, but encounters a critical limitation when using BigQuery for authentication data storage:

**BigQuery Streaming Buffer Restriction**: Rows inserted via streaming inserts (using `insert_rows_json()`) cannot be updated or deleted immediately. They must remain in the streaming buffer for up to 90 minutes before becoming mutable.

## Error Encountered

```
google.api_core.exceptions.BadRequest: 400 UPDATE or DELETE statement over table
opex-data-lake-k23k4y98m.auth.users would affect rows in the streaming buffer,
which is not supported
```

## Impact

### ✅ Working Endpoints
- **POST /auth/register** - Creates new users successfully
- **POST /auth/verify** - Token validation (read-only)
- **GET /auth/me** - User info retrieval (read-only)

### ❌ Affected Endpoints
- **POST /auth/login** - Fails because it needs to:
  - Reset `failed_login_attempts` counter
  - Update `last_login` timestamp
  - Clear `account_locked_until` field
- **Failed Login Tracking** - Cannot increment failed attempt counter
- **Account Lockout** - Cannot set lockout timestamp

## Root Cause

BigQuery is optimized for analytics workloads (OLAP), not transactional operations (OLTP). The streaming buffer is designed for high-throughput data ingestion, not immediate consistency.

### Why This Happens

1. **Registration** uses `insert_rows_json()` for streaming inserts
2. New row enters BigQuery streaming buffer (buffered for up to 90 minutes)
3. **Login attempt** tries to UPDATE the freshly inserted row
4. BigQuery rejects the UPDATE because row is still in streaming buffer

## Recommended Solutions

### Option 1: Migrate to Firestore (RECOMMENDED) ⭐

**Pros:**
- Designed for transactional workloads
- Sub-100ms latency for reads/writes
- Strong consistency
- Real-time updates
- Native GCP integration
- Automatic scaling

**Cons:**
- Different query patterns than BigQuery
- Some data duplication if also using BigQuery for analytics

**Implementation Effort**: 4-6 hours

**Code Changes**:
```python
from google.cloud import firestore

# Replace BigQuery client with Firestore
db = firestore.Client()

# Users collection
users_ref = db.collection('users')

# Create user
users_ref.document(user_id).set(user_data)

# Update user
users_ref.document(user_id).update({
    'last_login': datetime.utcnow(),
    'failed_login_attempts': 0
})
```

### Option 2: Use Cloud SQL (PostgreSQL/MySQL)

**Pros:**
- Full SQL capabilities
- ACID compliance
- Familiar relational model
- Supports transactions

**Cons:**
- Requires instance provisioning
- Higher cost than Firestore
- Requires connection pooling
- More operational overhead

**Implementation Effort**: 8-12 hours

### Option 3: Use Batch Loading Instead of Streaming (NOT RECOMMENDED)

**Pros:**
- Keeps BigQuery architecture
- No streaming buffer issues

**Cons:**
- Much slower (batch jobs take seconds to minutes)
- Poor user experience (users wait for batch to complete)
- Still fundamentally wrong database for this use case

## Architecture Recommendation

### Hybrid Approach (RECOMMENDED)

**Firestore for Auth (Hot Path)**:
- User credentials
- Sessions
- Login attempts
- Account status

**BigQuery for Analytics (Cold Path)**:
- Sync auth events for analytics
- Login patterns analysis
- Security auditing
- Compliance reporting

```
┌─────────────────┐
│   Auth API      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───────┐
│Firestore  BigQuery │
│(OLTP) │  │ (OLAP)   │
└───────┘  └──────────┘
    │         │
    └────┬────┘
         ▼
    Periodic Sync
    (Cloud Function)
```

## Migration Steps

### Phase 1: Create Firestore Schema (2 hours)
1. Create Firestore collections:
   - `users` - User accounts
   - `sessions` - Active sessions
   - `login_attempts` - Failed login tracking

2. Create indexes for common queries:
   - `users` by email
   - `sessions` by user_id
   - `sessions` by session_id

### Phase 2: Update Auth Code (3 hours)
1. Replace BigQuery client with Firestore in:
   - `main.py` (registration, login, logout)
   - `jwt_utils.py` (session management)

2. Update data models for Firestore document structure

3. Test all endpoints thoroughly

### Phase 3: Setup BigQuery Sync (1 hour)
1. Create Cloud Function to sync Firestore changes to BigQuery
2. Use Firestore triggers to capture auth events
3. Write to BigQuery for analytics (can use streaming inserts here)

### Phase 4: Deploy & Validate (1 hour)
1. Deploy updated auth API
2. Run comprehensive tests
3. Monitor error rates
4. Verify BigQuery sync working

## Temporary Workarounds

### For Development/Testing
1. Wait 90+ minutes after registration before attempting login
2. Use batch loading for initial user data (slow but works)
3. Pre-create test users using batch load jobs

### NOT Recommended
- Ignoring login tracking (security risk)
- Removing UPDATE statements (breaks core functionality)
- Using delays/retries (doesn't solve root cause)

## Testing Current Deployment

The current deployment at `https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api` has these limitations:

### Test Scenarios

✅ **Registration Works**:
```bash
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestP@ss123","full_name":"Test User"}'
```

❌ **Login Fails (within 90 minutes of registration)**:
```bash
curl -X POST https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestP@ss123"}'
```

## Decision Required

**Project Owner**: Please decide on migration approach:

1. **Migrate to Firestore** (RECOMMENDED)
   - Best for auth workloads
   - Lowest latency
   - Easy to implement

2. **Migrate to Cloud SQL**
   - More traditional approach
   - Full SQL capabilities
   - Higher operational cost

3. **Accept Limitations**
   - Keep BigQuery
   - Document restrictions
   - NOT recommended for production

## Timeline Impact

- **Current Phase 1 Progress**: 43% → Will remain at 43% until resolved
- **Estimated Resolution Time**: 1 day (Firestore) or 2 days (Cloud SQL)
- **Project Risk**: MEDIUM (auth is foundational for all features)

## Next Steps

1. Review this document
2. Choose migration approach
3. Schedule migration work
4. Update IMPLEMENTATION_PLAN.md with new tasks
5. Complete migration before proceeding to Phase 2

---

**Prepared by**: Claude Code
**Review Date**: November 5, 2025
**Next Review**: After migration decision

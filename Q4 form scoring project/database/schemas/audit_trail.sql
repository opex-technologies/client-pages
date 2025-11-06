-- scoring.audit_trail table schema
-- Comprehensive audit log for all system changes
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.scoring.audit_trail` (
  -- Primary identifier
  audit_id STRING NOT NULL,

  -- Entity being changed
  entity_type STRING NOT NULL,  -- user, permission, template, score, question, etc.
  entity_id STRING NOT NULL,  -- ID of the entity that changed

  -- Action performed
  action STRING NOT NULL,  -- created, updated, deleted, deployed, submitted, approved, etc.

  -- Actor
  changed_by STRING NOT NULL,  -- user_id from auth.users
  changed_at TIMESTAMP NOT NULL,  -- Set by application to CURRENT_TIMESTAMP()

  -- Change details
  field_name STRING,  -- Which field changed (for updates)
  previous_value STRING,  -- Old value (JSON string if complex)
  new_value STRING,  -- New value (JSON string if complex)

  -- Context
  change_reason STRING,  -- Optional: Why the change was made
  change_description STRING,  -- Human-readable description of the change

  -- Request metadata
  ip_address STRING,
  user_agent STRING,
  request_id STRING,  -- Links to application logs

  -- Categorization
  severity STRING,  -- info, warning, critical (for security-relevant changes)
  category STRING  -- auth, scoring, template, permission, etc.
)
OPTIONS(
  description="Comprehensive audit trail for all system changes"
);

-- Indexes (create separately):
-- CREATE INDEX idx_audit_entity ON scoring.audit_trail(entity_type, entity_id);
-- CREATE INDEX idx_audit_user ON scoring.audit_trail(changed_by);
-- CREATE INDEX idx_audit_date ON scoring.audit_trail(changed_at);
-- CREATE INDEX idx_audit_action ON scoring.audit_trail(action);

-- Partitioning (for performance with large audit logs):
-- Table can be partitioned by changed_at (monthly or quarterly partitions)
-- Old partitions can be archived to cold storage

-- Common Entity Types:
-- - user: Changes to auth.users
-- - permission: Changes to auth.permission_groups
-- - session: Login/logout events
-- - template: Form template changes
-- - score: Score creation/updates
-- - question: Question database changes
-- - deployment: Form deployments

-- Common Actions:
-- - created: New entity created
-- - updated: Entity modified
-- - deleted: Entity deleted (soft or hard)
-- - deployed: Template deployed to GitHub
-- - submitted: Score submitted for approval
-- - approved: Score approved
-- - rejected: Score rejected
-- - logged_in: User login
-- - logged_out: User logout
-- - permission_granted: Permission added
-- - permission_revoked: Permission removed

-- Example Audit Records:

-- Score Creation:
-- {
--   "entity_type": "score",
--   "entity_id": "score_abc123",
--   "action": "created",
--   "changed_by": "user_xyz",
--   "change_description": "Created new score for Acme Corp SASE assessment"
-- }

-- Permission Grant:
-- {
--   "entity_type": "permission",
--   "entity_id": "perm_def456",
--   "action": "permission_granted",
--   "changed_by": "user_admin",
--   "new_value": "{\"user\": \"user_xyz\", \"level\": \"edit\", \"company\": \"Acme\"}",
--   "change_reason": "New scorer added to team"
-- }

-- Score Update:
-- {
--   "entity_type": "score",
--   "entity_id": "score_abc123",
--   "action": "updated",
--   "field_name": "total_score",
--   "previous_value": "75",
--   "new_value": "82",
--   "changed_by": "user_xyz",
--   "change_description": "Adjusted scoring for question 15"
-- }

-- Retention Policy:
-- Audit logs should be retained for minimum 2 years for compliance
-- Older logs can be archived to Cloud Storage for long-term retention

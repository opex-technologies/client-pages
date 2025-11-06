-- auth.permission_groups table schema
-- Stores role-based access control (RBAC) permissions for users
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.auth.permission_groups` (
  -- Primary identifier
  permission_id STRING NOT NULL,

  -- User reference
  user_id STRING NOT NULL,  -- Foreign key to auth.users

  -- Permission scope
  company STRING,  -- NULL = all companies, specific value = that company only
  category STRING,  -- NULL = all categories, specific value = that category only

  -- Permission level
  permission_level STRING NOT NULL,  -- view, edit, admin

  -- Grant details
  granted_by STRING NOT NULL,  -- user_id of the admin who granted this permission
  granted_at TIMESTAMP NOT NULL,  -- Set by application to CURRENT_TIMESTAMP()

  -- Expiration (optional)
  expires_at TIMESTAMP,  -- NULL = never expires

  -- Status
  is_active BOOLEAN NOT NULL,  -- Default TRUE, set in application

  -- Audit fields
  revoked_by STRING,
  revoked_at TIMESTAMP,
  notes STRING  -- Admin notes about why permission was granted/revoked
)
OPTIONS(
  description="User permissions and role-based access control"
);

-- Indexes (create separately):
-- CREATE INDEX idx_permissions_user ON auth.permission_groups(user_id);
-- CREATE INDEX idx_permissions_level ON auth.permission_groups(permission_level);

-- Permission Level Hierarchy (enforced in application code):
-- admin > edit > view
-- admin: Can grant/revoke permissions, full CRUD access
-- edit: Can create, read, update, delete data within scope
-- view: Can only read data within scope

-- Scope Rules:
-- company=NULL, category=NULL: Access to ALL data (super admin)
-- company='Acme', category=NULL: Access to all categories for Acme
-- company='Acme', category='SASE': Access only to SASE data for Acme

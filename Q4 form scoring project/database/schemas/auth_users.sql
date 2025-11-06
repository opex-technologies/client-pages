-- auth.users table schema
-- Stores user authentication data for Form Builder and Response Scorer applications
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.auth.users` (
  -- Primary identifier
  user_id STRING NOT NULL,

  -- Authentication credentials
  email STRING NOT NULL,
  password_hash STRING NOT NULL,  -- bcrypt hash with 12 rounds

  -- User profile
  full_name STRING,

  -- Security features
  mfa_secret STRING,  -- For future MFA implementation
  failed_login_attempts INT64,  -- Default 0, set in application
  account_locked_until TIMESTAMP,

  -- Timestamps
  created_at TIMESTAMP NOT NULL,  -- Set by application to CURRENT_TIMESTAMP()
  last_login TIMESTAMP,
  password_changed_at TIMESTAMP,

  -- Status
  status STRING NOT NULL,  -- Default 'active', set in application (active, inactive, locked, deleted)

  -- Audit fields
  created_by STRING,
  updated_at TIMESTAMP,
  updated_by STRING
)
OPTIONS(
  description="User authentication and profile data"
);

-- Create unique index on email
-- Note: Actual index creation requires separate DDL in BigQuery
-- CREATE INDEX idx_users_email ON auth.users(email);

-- Comments for important fields:
-- user_id: UUID v4 generated on user creation
-- email: Primary login identifier, must be unique
-- password_hash: bcrypt hash with minimum 12 rounds for security
-- failed_login_attempts: Counter for brute force protection (lock after 5 attempts)
-- account_locked_until: NULL if not locked, future timestamp if temporarily locked
-- status: Controls account access (only 'active' users can login)

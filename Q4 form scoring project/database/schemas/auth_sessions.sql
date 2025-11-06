-- auth.sessions table schema
-- Tracks active user sessions and JWT tokens
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.auth.sessions` (
  -- Primary identifier
  session_id STRING NOT NULL,

  -- User reference
  user_id STRING NOT NULL,  -- Foreign key to auth.users

  -- Token information
  jwt_token_hash STRING NOT NULL,  -- SHA-256 hash of the JWT (not the actual token)

  -- Session lifecycle
  created_at TIMESTAMP NOT NULL,  -- Set by application to CURRENT_TIMESTAMP()
  expires_at TIMESTAMP NOT NULL,  -- Based on JWT expiration (24 hours from creation)
  last_activity_at TIMESTAMP,  -- Updated on each API call using this token

  -- Session metadata
  ip_address STRING,
  user_agent STRING,
  device_info STRING,  -- Browser, OS, device type

  -- Status
  is_active BOOLEAN NOT NULL,  -- Default TRUE, set in application

  -- Termination details
  logged_out_at TIMESTAMP,
  logout_reason STRING  -- user_logout, token_expired, admin_revoked, suspicious_activity
)
OPTIONS(
  description="Active user sessions and JWT token tracking"
);

-- Indexes (create separately):
-- CREATE INDEX idx_sessions_user ON auth.sessions(user_id);
-- CREATE INDEX idx_sessions_token_hash ON auth.sessions(jwt_token_hash);
-- CREATE INDEX idx_sessions_active ON auth.sessions(is_active);

-- Usage Notes:
-- jwt_token_hash: We store hash, not the actual JWT, for security
-- is_active: Set to FALSE on logout or token revocation
-- expires_at: Sessions auto-expire after 24 hours (token expiration)
-- last_activity_at: Can be used to implement idle timeout (optional future feature)

-- Session Cleanup:
-- Inactive sessions (is_active=FALSE) can be deleted after 30 days
-- Expired sessions (expires_at < CURRENT_TIMESTAMP) can be archived/deleted

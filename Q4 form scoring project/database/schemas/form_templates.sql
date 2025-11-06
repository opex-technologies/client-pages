-- form_builder.form_templates table schema
-- Stores survey form templates created via Form Builder
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.form_builder.form_templates` (
  -- Primary identifier
  template_id STRING NOT NULL,

  -- Template metadata
  template_name STRING NOT NULL,
  opportunity_type STRING NOT NULL,  -- Managed Service Provider, Network, Security, etc.
  opportunity_subtype STRING,  -- SASE, SD-WAN, MDR, etc. (NULL = All)
  description STRING,

  -- Questions configuration
  -- ARRAY of STRUCT containing question details
  questions ARRAY<STRUCT<
    question_id STRING,  -- Reference to form_builder.question_database
    question_text STRING,  -- Denormalized for faster access
    weight NUMERIC,  -- Scoring weight (can override default_weight)
    is_required BOOLEAN,
    input_type STRING,  -- text, textarea, number, radio, select, checkbox
    validation_rules STRING,  -- JSON string with validation config
    help_text STRING,
    display_order INT64
  >>,

  -- Deployment details
  deployed_url STRING,  -- GitHub Pages URL after deployment
  github_repo_path STRING,  -- Path in GitHub repo (e.g., forms/sase/vendor-assessment.html)
  github_commit_sha STRING,  -- Git commit SHA of last deployment

  -- Version control
  version INT64 NOT NULL,  -- Default 1, set in application
  parent_template_id STRING,  -- If this is a copy/fork of another template

  -- Status
  status STRING NOT NULL,  -- Default 'draft', set in application (draft, published, archived, deleted)

  -- Timestamps
  created_at TIMESTAMP NOT NULL,  -- Set by application to CURRENT_TIMESTAMP()
  created_by STRING NOT NULL,  -- user_id from auth.users
  updated_at TIMESTAMP,
  updated_by STRING,
  deployed_at TIMESTAMP,
  deployed_by STRING,

  -- Usage statistics (updated by triggers or scheduled job)
  submission_count INT64,  -- Default 0, set in application
  last_submission_at TIMESTAMP
)
OPTIONS(
  description="Form templates created via Form Builder application"
);

-- Indexes (create separately):
-- CREATE INDEX idx_templates_name ON form_builder.form_templates(template_name);
-- CREATE INDEX idx_templates_type ON form_builder.form_templates(opportunity_type);
-- CREATE INDEX idx_templates_status ON form_builder.form_templates(status);
-- CREATE INDEX idx_templates_created_by ON form_builder.form_templates(created_by);

-- Status Flow:
-- draft → published (on first deployment)
-- published → archived (when no longer in use)
-- archived → published (can be re-activated)
-- * → deleted (soft delete, recoverable)

-- Questions Array Example:
-- [
--   {
--     "question_id": "q_abc123",
--     "question_text": "Company Name",
--     "weight": 0,  -- Info field (not scored)
--     "is_required": true,
--     "input_type": "text",
--     "validation_rules": "{\"maxLength\": 100}",
--     "help_text": null,
--     "display_order": 1
--   },
--   ...
-- ]

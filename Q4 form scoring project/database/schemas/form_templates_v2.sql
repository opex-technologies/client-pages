-- Form Builder: Form Templates Table (v2 - Junction Table Approach)
-- Stores form template metadata
-- Questions stored separately in template_questions junction table
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.form_builder.form_templates` (
  -- Primary identifier
  template_id STRING NOT NULL,

  -- Template metadata
  template_name STRING NOT NULL,
  opportunity_type STRING NOT NULL,  -- Security, Network, Cloud, etc.
  opportunity_subtype STRING NOT NULL,  -- SASE, SD-WAN, MDR, etc.
  status STRING NOT NULL,  -- draft, published, archived, deleted
  description STRING,

  -- Audit and versioning
  created_by STRING NOT NULL,  -- user_id from auth.users
  created_by_email STRING,  -- Denormalized for convenience
  created_at TIMESTAMP NOT NULL,
  updated_by STRING,
  updated_by_email STRING,
  updated_at TIMESTAMP,

  -- Deployment tracking
  deployed_url STRING,  -- GitHub Pages URL
  deployed_at TIMESTAMP,
  deployed_by STRING,
  version INT64 NOT NULL
)
PARTITION BY DATE(created_at)
OPTIONS(
  description="Form templates created via Form Builder (v2 with junction table)",
  labels=[("project", "form_builder"), ("phase", "2"), ("version", "2")]
);

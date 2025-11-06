-- opex_dev.providers table schema
-- Master list of service providers (vendors being evaluated)
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.opex_dev.providers` (
  -- Primary identifier
  provider_id STRING NOT NULL,

  -- Provider information
  name STRING NOT NULL,
  category STRING,  -- MSP, Network, Security, Cloud, etc.

  -- Branding
  logo_url STRING,  -- URL to provider's logo (for reports/dashboards)
  website STRING,

  -- Description
  description STRING,
  service_offerings ARRAY<STRING>,  -- ["SASE", "SD-WAN", "MDR", etc.]

  -- Contact information
  primary_contact_name STRING,
  primary_contact_email STRING,
  primary_contact_phone STRING,

  -- Geographic coverage
  headquarters_location STRING,
  service_regions ARRAY<STRING>,  -- ["North America", "EMEA", "APAC", etc.]

  -- Metadata
  created_at TIMESTAMP NOT NULL,  -- Set by application to CURRENT_TIMESTAMP()
  updated_at TIMESTAMP,

  -- Status
  is_active BOOLEAN NOT NULL,  -- Default TRUE, set in application (can be deactivated without deletion)

  -- Statistics (can be populated by analytics)
  survey_count INT64,  -- Default 0, set in application (how many surveys has this provider completed)
  average_score NUMERIC,  -- Average score across all surveys
  last_survey_date TIMESTAMP
)
OPTIONS(
  description="Master list of service providers (vendors)"
);

-- Indexes (create separately):
-- CREATE INDEX idx_providers_name ON opex_dev.providers(name);
-- CREATE INDEX idx_providers_category ON opex_dev.providers(category);
-- CREATE INDEX idx_providers_active ON opex_dev.providers(is_active);

-- Usage:
-- This table can be used to:
-- 1. Normalize provider data across multiple survey responses
-- 2. Maintain consistent provider names and branding
-- 3. Generate provider comparison reports
-- 4. Track provider engagement over time

-- Provider vs Company:
-- "Provider" = Vendor being evaluated (e.g., AT&T, Verizon, Palo Alto Networks)
-- "Client" = Opex Technologies customer requesting evaluations

-- Future Enhancements:
-- - Provider tier (enterprise, mid-market, SMB)
-- - Partnership status (partner, prospect, competitor)
-- - Contract information (if applicable)
-- - Compliance certifications (SOC 2, ISO 27001, etc.)

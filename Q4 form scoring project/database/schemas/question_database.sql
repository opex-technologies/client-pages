-- form_builder.question_database table schema
-- Master repository of all survey questions (migrated from CSV)
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.form_builder.question_database` (
  -- Primary identifier
  question_id STRING NOT NULL,

  -- Question content
  question_text STRING NOT NULL,

  -- Scoring
  default_weight STRING,  -- "Info" for non-scored, numeric string for scored questions

  -- Classification
  category STRING NOT NULL,  -- Overview, Help Desk, Security Features, Network Features, etc.
  opportunity_type STRING,  -- All, Managed Service Provider, Network, Security, Cloud, etc.
  opportunity_subtypes STRING,  -- Comma-separated: "All", "SASE,SD-WAN", "MDR,Pen Test", etc.

  -- Form rendering
  input_type STRING NOT NULL,  -- Default 'text', set in application (text, textarea, number, radio, select, checkbox)
  input_options STRING,  -- JSON array of options for select/radio/checkbox: ["Yes", "No", "Partial"]
  placeholder_text STRING,
  help_text STRING,

  -- Validation
  validation_rules STRING,  -- JSON object with validation config
  -- Example: {"required": true, "minLength": 10, "maxLength": 500, "pattern": "^[A-Za-z]+$"}

  -- Tags for searchability
  tags ARRAY<STRING>,  -- ["compliance", "security", "encryption", etc.]

  -- Version control
  version INT64 NOT NULL,  -- Default 1, set in application

  -- Timestamps
  created_at TIMESTAMP NOT NULL,  -- Set by application to CURRENT_TIMESTAMP()
  updated_at TIMESTAMP,

  -- Status
  is_active BOOLEAN NOT NULL,  -- Default TRUE, set in application (can be deactivated without deletion)

  -- Usage tracking (can be populated by analytics)
  usage_count INT64,  -- Default 0, set in application  -- How many templates use this question
  last_used_at TIMESTAMP
)
OPTIONS(
  description="Master question repository for form building"
);

-- Indexes (create separately):
-- CREATE INDEX idx_questions_category ON form_builder.question_database(category);
-- CREATE INDEX idx_questions_type ON form_builder.question_database(opportunity_type);
-- CREATE INDEX idx_questions_active ON form_builder.question_database(is_active);

-- Question Filtering Logic:
-- Forms should query questions WHERE:
--   is_active = TRUE
--   AND (opportunity_type = 'All' OR opportunity_type = '{form_type}')
--   AND (opportunity_subtypes LIKE '%All%' OR opportunity_subtypes LIKE '%{form_subtype}%')

-- Weight Field:
-- "Info" = informational field, not scored
-- "10" = numeric weight for scoring (can be 0-100)

-- Input Type Mapping:
-- text: Single-line text input (<input type="text">)
-- textarea: Multi-line text area (<textarea>)
-- number: Numeric input (<input type="number">)
-- radio: Radio buttons (Yes/No/Partial, or custom options from input_options)
-- select: Dropdown (<select>)
-- checkbox: Multiple selection checkboxes

-- Migration Notes:
-- This table is populated from Question Database(Sheet1).csv (1,042 questions)
-- Migration script: database/migrations/migrate_question_database.py

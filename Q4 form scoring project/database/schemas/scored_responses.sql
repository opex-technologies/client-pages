-- scoring.scored_responses table schema
-- Stores completed scores for survey responses
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.scoring.scored_responses` (
  -- Primary identifier
  score_id STRING NOT NULL,

  -- Response reference
  response_id STRING,  -- Link to source response (company_name + timestamp combination)
  survey_type STRING NOT NULL,  -- Which survey was scored (network_security_survey, etc.)
  source_table STRING NOT NULL,  -- BigQuery table name (opex_dev.network_security_survey)

  -- Company information (denormalized for faster queries)
  company_name STRING NOT NULL,
  contact_email STRING,
  contact_name STRING,

  -- Scoring results
  total_score NUMERIC NOT NULL,  -- Sum of all points awarded
  max_score NUMERIC NOT NULL,  -- Sum of all maximum possible points
  percentage NUMERIC,  -- (total_score / max_score) * 100
  letter_grade STRING,  -- A, B, C, D, F based on percentage

  -- Question-level details stored in scoring.question_scores (separate table)
  question_count INT64,  -- Total questions scored
  questions_answered INT64,  -- Questions with non-empty answers

  -- Scorer information
  scored_by STRING NOT NULL,  -- user_id from auth.users
  scored_at TIMESTAMP NOT NULL,  -- Set by application to CURRENT_TIMESTAMP()

  -- Timestamps
  updated_at TIMESTAMP,
  updated_by STRING,
  submitted_at TIMESTAMP,  -- When status changed to 'submitted'
  approved_at TIMESTAMP,  -- When status changed to 'approved'
  approved_by STRING,

  -- Notes and comments
  notes STRING,  -- Overall scoring notes from scorer
  internal_notes STRING,  -- Private notes not shown to client

  -- Status
  status STRING NOT NULL,  -- Default 'draft', set in application (draft, in_progress, submitted, approved, rejected, deleted)

  -- Version control
  version INT64 NOT NULL,  -- Default 1, set in application
  previous_score_id STRING  -- If this is an updated version of a previous score
)
OPTIONS(
  description="Scored survey responses with overall score summary"
);

-- Indexes (create separately):
-- CREATE INDEX idx_scores_company ON scoring.scored_responses(company_name);
-- CREATE INDEX idx_scores_survey ON scoring.scored_responses(survey_type);
-- CREATE INDEX idx_scores_status ON scoring.scored_responses(status);
-- CREATE INDEX idx_scores_scorer ON scoring.scored_responses(scored_by);
-- CREATE INDEX idx_scores_date ON scoring.scored_responses(scored_at);

-- Status Flow:
-- draft → in_progress → submitted → approved
-- Any status → rejected (with notes)
-- Any status → deleted (soft delete)

-- Letter Grade Calculation:
-- A: 90-100%
-- B: 80-89%
-- C: 70-79%
-- D: 60-69%
-- F: 0-59%

-- Response ID Format:
-- Can be composed of company_name + timestamp or unique identifier from source table
-- Used to link score back to original response data

-- Relationship to question_scores:
-- One scored_response has many question_scores (one per question)
-- Join: scoring.question_scores.score_id = scoring.scored_responses.score_id

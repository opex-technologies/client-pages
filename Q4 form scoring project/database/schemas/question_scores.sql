-- scoring.question_scores table schema
-- Stores individual question scores (detail level)
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.scoring.question_scores` (
  -- Primary identifier
  question_score_id STRING NOT NULL,

  -- Parent score reference
  score_id STRING NOT NULL,  -- Foreign key to scoring.scored_responses

  -- Question details
  question STRING NOT NULL,  -- Full question text
  question_id STRING,  -- Reference to form_builder.question_database (if available)
  category STRING,  -- Question category (for grouping in reports)

  -- Answer from response
  answer STRING,  -- The vendor/respondent's answer
  answer_type STRING,  -- text, number, radio (for rendering in UI)

  -- Scoring
  weight NUMERIC NOT NULL,  -- Weight assigned to this question
  points_awarded NUMERIC NOT NULL,  -- Actual points given (0 to weight)
  max_points NUMERIC NOT NULL,  -- Maximum possible points (usually = weight)
  percentage NUMERIC,  -- (points_awarded / max_points) * 100 for this question

  -- Scoring details
  scoring_method STRING,  -- auto, manual, partial
  -- auto: Automatically scored (Yes=full points, No=0, Partial=half)
  -- manual: Manually entered by scorer
  -- partial: Auto-scored but manually adjusted

  -- Scorer notes
  comments STRING,  -- Scorer's notes about why points were awarded/deducted

  -- Metadata
  scored_at TIMESTAMP NOT NULL,  -- Set by application to CURRENT_TIMESTAMP()
  scored_by STRING NOT NULL,  -- user_id from auth.users

  -- Display order (for consistent rendering)
  display_order INT64
)
OPTIONS(
  description="Individual question scores for each scored response"
);

-- Indexes (create separately):
-- CREATE INDEX idx_question_scores_score_id ON scoring.question_scores(score_id);
-- CREATE INDEX idx_question_scores_category ON scoring.question_scores(category);

-- Points Awarded Logic:
-- For Yes/No questions:
--   Yes = weight (full points)
--   No = 0 points
--   Partial = weight / 2 (half points)
-- For text/numeric questions:
--   Scorer manually assigns points (0 to weight)
-- For Info questions (weight = 0):
--   points_awarded = 0, max_points = 0 (not included in total score)

-- Example Record:
-- {
--   "question_score_id": "qs_xyz789",
--   "score_id": "score_abc123",
--   "question": "Do you offer 24/7 support?",
--   "answer": "yes",
--   "weight": 10,
--   "points_awarded": 10,
--   "max_points": 10,
--   "percentage": 100,
--   "scoring_method": "auto",
--   "comments": null
-- }

-- Usage in Queries:
-- To get all question scores for a response:
-- SELECT * FROM scoring.question_scores WHERE score_id = '{score_id}' ORDER BY display_order

-- To calculate total score:
-- SELECT SUM(points_awarded) as total, SUM(max_points) as max
-- FROM scoring.question_scores WHERE score_id = '{score_id}'

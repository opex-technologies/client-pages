-- Form Builder: Template Questions Junction Table
-- Links form templates to questions from the Question Database
-- Created: November 5, 2025

CREATE TABLE IF NOT EXISTS `opex-data-lake-k23k4y98m.form_builder.template_questions` (
  -- Composite primary key
  template_id STRING NOT NULL,
  question_id STRING NOT NULL,

  -- Question configuration in template
  weight FLOAT64,  -- Can be numeric weight or NULL for "Info"
  is_required BOOLEAN NOT NULL,
  sort_order INT64 NOT NULL,

  -- Audit metadata
  added_at TIMESTAMP NOT NULL,
  added_by STRING NOT NULL
)
PARTITION BY DATE(added_at)
OPTIONS(
  description="Junction table linking form templates to questions with per-template configuration",
  labels=[("project", "form_builder"), ("phase", "2")]
);

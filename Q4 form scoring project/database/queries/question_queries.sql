-- Common queries for the Question Database
-- form_builder.question_database table
-- Created: November 5, 2025

-- Query 1: Get total count by category
SELECT
  category,
  COUNT(*) as question_count
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE
GROUP BY category
ORDER BY question_count DESC;

-- Query 2: Find questions by opportunity type and subtype
-- Example: Get all SASE questions
SELECT
  question_id,
  question_text,
  default_weight,
  category,
  input_type
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE
  AND (opportunity_type = 'All' OR opportunity_type = 'Security')
  AND (opportunity_subtypes LIKE '%All%' OR opportunity_subtypes LIKE '%SASE%')
ORDER BY category, question_text;

-- Query 3: Get all scored questions (exclude Info questions)
SELECT
  question_id,
  question_text,
  default_weight,
  category,
  opportunity_type
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE
  AND default_weight != 'Info'
ORDER BY CAST(default_weight AS INT64) DESC, category;

-- Query 4: Search questions by keyword
-- Example: Find all security-related questions
SELECT
  question_id,
  question_text,
  category,
  opportunity_type,
  default_weight
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE
  AND LOWER(question_text) LIKE '%security%'
ORDER BY category, question_text;

-- Query 5: Get questions by input type
SELECT
  input_type,
  COUNT(*) as count
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE
GROUP BY input_type
ORDER BY count DESC;

-- Query 6: Get all "universal" questions (All opportunity types)
SELECT
  question_id,
  question_text,
  category,
  default_weight
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE
  AND opportunity_type = 'All'
  AND opportunity_subtypes = 'All'
ORDER BY category, question_text;

-- Query 7: Find questions for Managed Service Provider opportunities
SELECT
  category,
  COUNT(*) as question_count,
  SUM(CASE WHEN default_weight = 'Info' THEN 1 ELSE 0 END) as info_count,
  SUM(CASE WHEN default_weight != 'Info' THEN 1 ELSE 0 END) as scored_count
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE
  AND (opportunity_type = 'All' OR opportunity_type = 'Managed Service Provider')
GROUP BY category
ORDER BY question_count DESC;

-- Query 8: Get question statistics by category
SELECT
  category,
  COUNT(*) as total_questions,
  COUNT(DISTINCT opportunity_type) as opp_types,
  AVG(CASE WHEN default_weight != 'Info' THEN CAST(default_weight AS INT64) ELSE NULL END) as avg_weight,
  MIN(created_at) as earliest_created,
  MAX(created_at) as latest_created
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE
GROUP BY category
ORDER BY total_questions DESC;

-- Query 9: Sample questions with full details
SELECT
  question_id,
  question_text,
  default_weight,
  category,
  opportunity_type,
  opportunity_subtypes,
  input_type,
  created_at
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE
LIMIT 20;

-- Query 10: Question distribution summary
SELECT
  'Total Questions' as metric,
  CAST(COUNT(*) AS STRING) as value
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE

UNION ALL

SELECT
  'Info Questions' as metric,
  CAST(SUM(CASE WHEN default_weight = 'Info' THEN 1 ELSE 0 END) AS STRING) as value
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE

UNION ALL

SELECT
  'Scored Questions' as metric,
  CAST(SUM(CASE WHEN default_weight != 'Info' THEN 1 ELSE 0 END) AS STRING) as value
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE

UNION ALL

SELECT
  'Unique Categories' as metric,
  CAST(COUNT(DISTINCT category) AS STRING) as value
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE

UNION ALL

SELECT
  'Unique Opp Types' as metric,
  CAST(COUNT(DISTINCT opportunity_type) AS STRING) as value
FROM `opex-data-lake-k23k4y98m.form_builder.question_database`
WHERE is_active = TRUE;

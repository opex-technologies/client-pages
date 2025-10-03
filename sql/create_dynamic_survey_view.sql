-- Create a dynamic view that unpivots all survey tables using JSON functions
-- This approach converts each row to JSON and then extracts key-value pairs

CREATE OR REPLACE VIEW `opex-data-lake-k23k4y98m.scoring.all_survey_responses` AS
WITH 
-- Get all tables from the opex_dev dataset
all_tables AS (
  SELECT table_name
  FROM `opex-data-lake-k23k4y98m.opex_dev.INFORMATION_SCHEMA.TABLES`
  WHERE table_type = 'BASE TABLE'
),

-- Define metadata columns to preserve
metadata_columns AS (
  SELECT column_name
  FROM UNNEST(['timestamp', 'source', 'contact_name', 'contact_email', 
               'contact_company', 'contact_phone', 'company_name', 'inserted_at']) as column_name
),

-- Generate dynamic SQL for each table
table_queries AS (
  SELECT 
    table_name,
    FORMAT("""
      SELECT
        IFNULL(SAFE_CAST(JSON_VALUE(row_json, '$.timestamp') AS STRING), 
               SAFE_CAST(JSON_VALUE(row_json, '$.inserted_at') AS STRING)) as timestamp,
        IFNULL(JSON_VALUE(row_json, '$.source'), '%s') as source,
        IFNULL(JSON_VALUE(row_json, '$.contact_name'), '') as contact_name,
        IFNULL(JSON_VALUE(row_json, '$.contact_email'), '') as contact_email,
        IFNULL(JSON_VALUE(row_json, '$.contact_company'), '') as contact_company,
        IFNULL(JSON_VALUE(row_json, '$.contact_phone'), '') as contact_phone,
        IFNULL(JSON_VALUE(row_json, '$.company_name'), '') as company_name,
        '%s' as survey_type,
        kv.key as question,
        kv.value as answer,
        SAFE_CAST(JSON_VALUE(row_json, '$.inserted_at') AS TIMESTAMP) as inserted_at
      FROM (
        SELECT TO_JSON_STRING(t) as row_json
        FROM `opex-data-lake-k23k4y98m.opex_dev.%s` t
      ),
      UNNEST(JSON_EXTRACT_ARRAY(row_json, '$')) as json_element,
      UNNEST([STRUCT(
        JSON_EXTRACT_SCALAR(json_element, '$.key') as key,
        JSON_EXTRACT_SCALAR(json_element, '$.value') as value
      )]) as kv
      WHERE kv.key NOT IN (
        'timestamp', 'source', 'contact_name', 'contact_email', 
        'contact_company', 'contact_phone', 'company_name', 'inserted_at'
      )
    """, table_name, table_name, table_name) as query_text
  FROM all_tables
)

-- For now, we'll create a simpler version that handles known tables
-- This can be extended as new tables are added
SELECT * FROM (
  -- Contact Form
  SELECT 
    COALESCE(timestamp, CAST(inserted_at AS STRING)) as timestamp,
    COALESCE(source, 'contact_form') as source,
    IFNULL(contact_name, '') as contact_name,
    IFNULL(contact_email, '') as contact_email,
    IFNULL(contact_company, '') as contact_company,
    IFNULL(contact_phone, '') as contact_phone,
    IFNULL(company_name, '') as company_name,
    'contact_form' as survey_type,
    'message' as question,
    message as answer,
    inserted_at
  FROM `opex-data-lake-k23k4y98m.opex_dev.contact_form`
  WHERE message IS NOT NULL
  
  UNION ALL
  
  -- Add more survey tables as they are created
  -- This section will be populated by querying INFORMATION_SCHEMA
  SELECT 
    COALESCE(timestamp, CAST(inserted_at AS STRING)) as timestamp,
    COALESCE(source, 'network_security_survey') as source,
    IFNULL(contact_name, '') as contact_name,
    IFNULL(contact_email, '') as contact_email,
    IFNULL(contact_company, '') as contact_company,
    IFNULL(contact_phone, '') as contact_phone,
    IFNULL(company_name, '') as company_name,
    'network_security_survey' as survey_type,
    question,
    answer,
    inserted_at
  FROM (
    SELECT * FROM `opex-data-lake-k23k4y98m.opex_dev.network_security_survey`
  ) t,
  UNNEST([
    -- This is where we would dynamically generate the question list
    -- For now, using a placeholder that will be replaced by the procedure
    STRUCT('placeholder' as question, 'placeholder' as answer)
  ])
  WHERE FALSE -- This ensures no rows until properly configured
);
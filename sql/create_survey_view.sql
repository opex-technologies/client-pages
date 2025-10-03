-- Create a view that dynamically combines all survey responses
-- This approach uses a stored procedure to build the view dynamically

-- First, create the stored procedure that generates the dynamic SQL
CREATE OR REPLACE PROCEDURE `opex-data-lake-k23k4y98m.scoring.refresh_survey_responses_view`()
BEGIN
  DECLARE view_sql STRING DEFAULT '';
  DECLARE table_queries ARRAY<STRING> DEFAULT [];
  DECLARE metadata_cols STRING DEFAULT "'timestamp', 'source', 'contact_name', 'contact_email', 'contact_company', 'contact_phone', 'company_name', 'inserted_at'";
  
  -- For each table in opex_dev, generate a query that unpivots the data
  FOR record IN (
    SELECT 
      table_name,
      -- Get all non-metadata columns as an array
      ARRAY_TO_STRING(
        ARRAY(
          SELECT column_name 
          FROM `opex-data-lake-k23k4y98m.opex_dev.INFORMATION_SCHEMA.COLUMNS` c
          WHERE c.table_name = t.table_name
            AND c.column_name NOT IN ('timestamp', 'source', 'contact_name', 'contact_email', 
                                     'contact_company', 'contact_phone', 'company_name', 'inserted_at')
          ORDER BY ordinal_position
        ), ', '
      ) as question_columns
    FROM `opex-data-lake-k23k4y98m.opex_dev.INFORMATION_SCHEMA.TABLES` t
    WHERE table_type = 'BASE TABLE'
  )
  DO
    -- Only process if there are question columns
    IF record.question_columns != '' THEN
      -- Build query for this table
      SET table_queries = ARRAY_CONCAT(table_queries, [FORMAT("""
        SELECT 
          COALESCE(timestamp, CAST(inserted_at AS STRING)) as timestamp,
          COALESCE(source, '%s') as source,
          IFNULL(contact_name, '') as contact_name,
          IFNULL(contact_email, '') as contact_email,
          IFNULL(contact_company, '') as contact_company,
          IFNULL(contact_phone, '') as contact_phone,
          IFNULL(company_name, '') as company_name,
          '%s' as survey_type,
          question,
          answer,
          inserted_at
        FROM `opex-data-lake-k23k4y98m.opex_dev.%s`
        UNPIVOT(answer FOR question IN (%s))
      """, 
      record.table_name, -- source default
      record.table_name, -- survey_type
      record.table_name, -- table name
      record.question_columns -- columns to unpivot
      )]);
    END IF;
  END FOR;
  
  -- Combine all queries
  IF ARRAY_LENGTH(table_queries) > 0 THEN
    SET view_sql = ARRAY_TO_STRING(table_queries, '\nUNION ALL\n');
    
    -- Create or replace the view
    EXECUTE IMMEDIATE FORMAT("""
      CREATE OR REPLACE VIEW `opex-data-lake-k23k4y98m.scoring.all_survey_responses` AS
      %s
    """, view_sql);
  END IF;
END;

-- Execute the procedure to create the initial view
CALL `opex-data-lake-k23k4y98m.scoring.refresh_survey_responses_view`();
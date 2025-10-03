-- Create a stored procedure that dynamically generates UNPIVOT SQL for all survey tables
CREATE OR REPLACE PROCEDURE `opex-data-lake-k23k4y98m.scoring.generate_survey_unpivot_sql`()
BEGIN
  DECLARE sql_query STRING DEFAULT '';
  DECLARE table_union_queries ARRAY<STRING> DEFAULT [];
  DECLARE current_table_query STRING;
  
  -- Common metadata columns that should be preserved (not unpivoted)
  DECLARE metadata_columns ARRAY<STRING> DEFAULT [
    'timestamp', 'source', 'contact_name', 'contact_email', 
    'contact_company', 'contact_phone', 'company_name', 'inserted_at'
  ];
  
  -- Loop through all tables in opex_dev dataset
  FOR record IN (
    SELECT table_name
    FROM `opex-data-lake-k23k4y98m.opex_dev.INFORMATION_SCHEMA.TABLES`
    WHERE table_type = 'BASE TABLE'
  )
  DO
    -- Build the UNPIVOT query for each table
    SET current_table_query = FORMAT("""
      SELECT 
        COALESCE(timestamp, inserted_at) as timestamp,
        COALESCE(source, '%s') as source,
        IFNULL(contact_name, '') as contact_name,
        IFNULL(contact_email, '') as contact_email,
        IFNULL(contact_company, '') as contact_company,
        IFNULL(contact_phone, '') as contact_phone,
        IFNULL(company_name, '') as company_name,
        '%s' as survey_type,
        question,
        CAST(answer AS STRING) as answer,
        inserted_at
      FROM (
        SELECT * FROM `opex-data-lake-k23k4y98m.opex_dev.%s`
      ) UNPIVOT(
        answer FOR question IN (
          SELECT column_name
          FROM `opex-data-lake-k23k4y98m.opex_dev.INFORMATION_SCHEMA.COLUMNS`
          WHERE table_name = '%s'
            AND column_name NOT IN UNNEST(@metadata_columns)
        )
      )
    """, 
    record.table_name, -- source fallback
    record.table_name, -- survey_type
    record.table_name, -- table to query
    record.table_name  -- for column lookup
    );
    
    -- Add to array of queries
    SET table_union_queries = ARRAY_CONCAT(table_union_queries, [current_table_query]);
  END FOR;
  
  -- Combine all queries with UNION ALL
  SET sql_query = ARRAY_TO_STRING(table_union_queries, '\nUNION ALL\n');
  
  -- Execute the dynamic SQL to create/replace the view
  EXECUTE IMMEDIATE FORMAT("""
    CREATE OR REPLACE VIEW `opex-data-lake-k23k4y98m.scoring.all_survey_responses` AS
    %s
  """, sql_query);
  
END;
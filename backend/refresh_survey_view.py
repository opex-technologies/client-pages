"""
Cloud Function to refresh the survey view when new tables are added.
This can be triggered by Pub/Sub, Cloud Scheduler, or manually.
"""

import functions_framework
from google.cloud import bigquery
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "opex-data-lake-k23k4y98m"
SOURCE_DATASET = "opex_dev"
TARGET_DATASET = "scoring"
VIEW_NAME = "all_survey_responses"

# Metadata columns that should be preserved (not unpivoted)
METADATA_COLUMNS = {
    'timestamp', 'source', 'contact_name', 'contact_email', 
    'contact_company', 'contact_phone', 'company_name', 'inserted_at'
}

def get_tables_and_columns(client):
    """Get all tables and their columns from the source dataset."""
    query = f"""
    SELECT 
        t.table_name,
        ARRAY_AGG(
            STRUCT(c.column_name, c.data_type)
            ORDER BY c.ordinal_position
        ) as columns
    FROM `{PROJECT_ID}.{SOURCE_DATASET}.INFORMATION_SCHEMA.TABLES` t
    JOIN `{PROJECT_ID}.{SOURCE_DATASET}.INFORMATION_SCHEMA.COLUMNS` c
        ON t.table_name = c.table_name
    WHERE t.table_type = 'BASE TABLE'
    GROUP BY t.table_name
    ORDER BY t.table_name
    """
    
    return list(client.query(query))

def generate_unpivot_query(table_name, columns):
    """Generate UNPIVOT query for a single table."""
    # Get column names
    column_names = {col['column_name'] for col in columns}
    
    # Filter out metadata columns to get question columns
    question_columns = [
        col['column_name'] for col in columns 
        if col['column_name'] not in METADATA_COLUMNS
    ]
    
    if not question_columns:
        return None
    
    # Build the UNPIVOT query
    unpivot_columns = ', '.join(f"`{col}`" for col in question_columns)
    
    # Build SELECT clause based on which columns exist
    select_clauses = []
    
    # Timestamp handling
    if 'timestamp' in column_names:
        select_clauses.append("COALESCE(CAST(timestamp AS STRING), CAST(inserted_at AS STRING)) as timestamp")
    else:
        select_clauses.append("CAST(inserted_at AS STRING) as timestamp")
    
    # Source handling
    if 'source' in column_names:
        select_clauses.append(f"COALESCE(source, '{table_name}') as source")
    else:
        select_clauses.append(f"'{table_name}' as source")
    
    # Contact fields - use IFNULL only if column exists
    for field in ['contact_name', 'contact_email', 'contact_company', 'contact_phone', 'company_name']:
        if field in column_names:
            select_clauses.append(f"IFNULL({field}, '') as {field}")
        else:
            select_clauses.append(f"'' as {field}")
    
    # Add remaining fields
    select_clauses.extend([
        f"'{table_name}' as survey_type",
        "question",
        "CAST(answer AS STRING) as answer",
        "inserted_at"
    ])
    
    select_clause = ',\n        '.join(select_clauses)
    query = f"""
    SELECT 
        {select_clause}
    FROM `{PROJECT_ID}.{SOURCE_DATASET}.{table_name}`
    UNPIVOT(answer FOR question IN ({unpivot_columns}))"""
    
    return query

def refresh_view(client):
    """Generate and execute the view refresh SQL."""
    tables_data = get_tables_and_columns(client)
    
    if not tables_data:
        logger.warning("No tables found in the source dataset.")
        return False
    
    # Generate UNPIVOT queries for each table
    table_queries = []
    for table_data in tables_data:
        table_name = table_data.table_name
        columns = table_data.columns
        
        query = generate_unpivot_query(table_name, columns)
        if query:
            table_queries.append(query)
            logger.info(f"Generated query for table: {table_name}")
    
    if not table_queries:
        logger.warning("No tables with question columns found.")
        return False
    
    # Combine all queries with UNION ALL
    combined_query = '\nUNION ALL\n'.join(table_queries)
    
    # Create the final view SQL
    view_sql = f"""
CREATE OR REPLACE VIEW `{PROJECT_ID}.{TARGET_DATASET}.{VIEW_NAME}` AS
{combined_query}
"""
    
    # Execute the view creation
    try:
        client.query(view_sql).result()
        logger.info(f"View refreshed successfully: {PROJECT_ID}.{TARGET_DATASET}.{VIEW_NAME}")
        return True
    except Exception as e:
        logger.error(f"Error refreshing view: {e}")
        return False

@functions_framework.http
def refresh_survey_view(request):
    """
    HTTP Cloud Function to refresh the survey view.
    
    Can be triggered by:
    - HTTP request (direct invocation)
    - Cloud Scheduler (for periodic updates)
    - Pub/Sub (when new tables are created)
    """
    
    # Initialize BigQuery client
    client = bigquery.Client()
    
    try:
        # Refresh the view
        success = refresh_view(client)
        
        if success:
            response = {
                "status": "success",
                "message": f"View {PROJECT_ID}.{TARGET_DATASET}.{VIEW_NAME} refreshed successfully"
            }
            return json.dumps(response), 200
        else:
            response = {
                "status": "error",
                "message": "Failed to refresh view - check logs for details"
            }
            return json.dumps(response), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in refresh_survey_view: {str(e)}", exc_info=True)
        response = {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }
        return json.dumps(response), 500
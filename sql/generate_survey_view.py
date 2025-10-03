#!/usr/bin/env python3
"""
Generate BigQuery view SQL that unpivots all survey tables dynamically.
This script queries the INFORMATION_SCHEMA to build a comprehensive UNION ALL query.
"""

from google.cloud import bigquery
import os

# Initialize BigQuery client
client = bigquery.Client()

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

def get_tables_and_columns():
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

def generate_view_sql():
    """Generate the complete view SQL."""
    tables_data = get_tables_and_columns()
    
    if not tables_data:
        print("No tables found in the source dataset.")
        return None
    
    # Generate UNPIVOT queries for each table
    table_queries = []
    for table_data in tables_data:
        table_name = table_data.table_name
        columns = table_data.columns
        
        query = generate_unpivot_query(table_name, columns)
        if query:
            table_queries.append(query)
            print(f"Generated query for table: {table_name}")
    
    if not table_queries:
        print("No tables with question columns found.")
        return None
    
    # Combine all queries with UNION ALL
    combined_query = '\nUNION ALL\n'.join(table_queries)
    
    # Create the final view SQL
    view_sql = f"""
CREATE OR REPLACE VIEW `{PROJECT_ID}.{TARGET_DATASET}.{VIEW_NAME}` AS
{combined_query}
"""
    
    return view_sql

def main():
    """Main function to generate and optionally execute the view creation."""
    print(f"Generating view SQL for {PROJECT_ID}.{TARGET_DATASET}.{VIEW_NAME}")
    
    view_sql = generate_view_sql()
    
    if view_sql:
        # Save to file
        output_file = f"create_{VIEW_NAME}.sql"
        with open(output_file, 'w') as f:
            f.write(view_sql)
        print(f"\nView SQL saved to: {output_file}")
        
        # Create the view
        print("\nCreating the view...")
        try:
            client.query(view_sql).result()
            print(f"View created successfully: {PROJECT_ID}.{TARGET_DATASET}.{VIEW_NAME}")
        except Exception as e:
            print(f"Error creating view: {e}")
    else:
        print("Failed to generate view SQL.")

if __name__ == "__main__":
    main()
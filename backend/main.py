import json
import logging
import time
from datetime import datetime
from typing import Dict, Any

import functions_framework
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
from flask import Request

# Initialize BigQuery client
client = bigquery.Client()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_table_if_not_exists(dataset_id: str, table_id: str, form_data: Dict[str, Any]) -> bool:
    """Create BigQuery table if it doesn't exist with dynamic schema based on form data.
    
    Returns:
        bool: True if table was created, False if it already existed
    """
    
    table_ref = client.dataset(dataset_id).table(table_id)
    
    try:
        # Check if table exists
        table = client.get_table(table_ref)
        logger.info(f"Table {dataset_id}.{table_id} already exists")
        
        # Check if we need to add new fields
        existing_fields = {field.name for field in table.schema}
        new_fields = []
        
        for key in form_data.keys():
            if key not in existing_fields and key != "inserted_at":
                # Determine field type based on value
                field_type = "STRING"
                if key == "timestamp":
                    field_type = "TIMESTAMP"
                elif isinstance(form_data.get(key), (int, float)):
                    field_type = "NUMERIC"
                
                new_fields.append(SchemaField(key, field_type, mode="NULLABLE"))
        
        if new_fields:
            # Add new fields to existing table
            new_schema = table.schema + new_fields
            table.schema = new_schema
            table = client.update_table(table, ["schema"])
            logger.info(f"Added {len(new_fields)} new fields to table {dataset_id}.{table_id}")
            # Give a moment for schema update to propagate
            time.sleep(1)
        
        return False
        
    except Exception as e:
        # Table doesn't exist, create it
        logger.info(f"Table not found, creating table {dataset_id}.{table_id}")
        
        try:
            # Create dynamic schema based on form data
            schema = []
            
            for key, value in form_data.items():
                # Determine field type based on value
                field_type = "STRING"
                if key == "timestamp":
                    field_type = "TIMESTAMP"
                elif isinstance(value, (int, float)):
                    field_type = "NUMERIC"
                
                schema.append(SchemaField(key, field_type, mode="NULLABLE"))
            
            # Always add inserted_at field
            schema.append(SchemaField("inserted_at", "TIMESTAMP", mode="REQUIRED"))
            
            table = bigquery.Table(table_ref, schema=schema)
            table = client.create_table(table)
            logger.info(f"Successfully created table {table.project}.{table.dataset_id}.{table.table_id} with {len(schema)} fields")
            
            # Wait a moment for table creation to fully propagate
            time.sleep(2)
            
            return True
            
        except Exception as create_error:
            logger.error(f"Failed to create table {dataset_id}.{table_id}: {str(create_error)}")
            raise create_error


def insert_data_to_bigquery(dataset_id: str, table_id: str, form_data: Dict[str, Any], retry_count: int = 3) -> None:
    """Insert form data into BigQuery table with retry logic."""
    
    # Prepare the row for insertion
    row_to_insert = form_data.copy()
    
    # Add insertion timestamp
    row_to_insert["inserted_at"] = datetime.utcnow().isoformat()
    
    # Convert timestamp string to proper format if it exists
    if "timestamp" in row_to_insert and row_to_insert["timestamp"]:
        try:
            # Parse ISO format timestamp
            ts = datetime.fromisoformat(row_to_insert["timestamp"].replace('Z', '+00:00'))
            row_to_insert["timestamp"] = ts.isoformat()
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid timestamp format: {row_to_insert['timestamp']}, error: {e}")
            row_to_insert["timestamp"] = None
    
    # Retry insertion with backoff
    for attempt in range(retry_count):
        try:
            # Get table reference
            table_ref = client.dataset(dataset_id).table(table_id)
            table = client.get_table(table_ref)
            
            # Insert the row
            errors = client.insert_rows_json(table, [row_to_insert])
            
            if errors:
                logger.warning(f"BigQuery insertion errors (attempt {attempt + 1}): {errors}")
                if attempt == retry_count - 1:  # Last attempt
                    raise Exception(f"Failed to insert data after {retry_count} attempts: {errors}")
                time.sleep(1)  # Wait before retry
                continue
            
            logger.info(f"Successfully inserted data into {dataset_id}.{table_id}")
            return
            
        except Exception as e:
            logger.warning(f"Insert attempt {attempt + 1} failed: {str(e)}")
            if attempt == retry_count - 1:  # Last attempt
                raise e
            time.sleep(2)  # Wait before retry


@functions_framework.http
def webhook_to_bigquery(request: Request) -> tuple[str, int]:
    """
    Google Cloud Function to process webhook data and insert into BigQuery.
    
    Args:
        request: HTTP request object containing the webhook payload
        
    Returns:
        Tuple of response message and HTTP status code
    """
    
    # Set CORS headers for preflight requests
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    try:
        # Validate request method
        if request.method != 'POST':
            return json.dumps({"error": "Only POST method allowed"}), 405
        
        # Parse JSON payload
        request_json = request.get_json(silent=True)
        if not request_json:
            return json.dumps({"error": "Invalid JSON payload"}), 400
        
        # Validate required fields
        if "formName" not in request_json:
            return json.dumps({"error": "Missing 'formName' field"}), 400
        
        if "formData" not in request_json:
            return json.dumps({"error": "Missing 'formData' field"}), 400
        
        form_name = request_json["formName"]
        form_data = request_json["formData"]
        
        # Validate form_name (table name should be valid BigQuery identifier)
        if not form_name or not isinstance(form_name, str):
            return json.dumps({"error": "Invalid 'formName'"}), 400
        
        # Replace any invalid characters in table name
        table_name = form_name.replace("-", "_").replace(" ", "_").lower()
        
        # Constants
        dataset_id = "opex_dev"
        
        logger.info(f"Processing webhook for form: {form_name}, target table: {table_name}")
        
        # Create table if it doesn't exist
        table_was_created = create_table_if_not_exists(dataset_id, table_name, form_data)
        
        # Insert data into BigQuery with more retries if table was just created
        retry_count = 5 if table_was_created else 3
        insert_data_to_bigquery(dataset_id, table_name, form_data, retry_count)
        
        # Return success response
        response = {
            "status": "success",
            "message": f"Data successfully inserted into {dataset_id}.{table_name}",
            "formName": form_name,
            "recordsInserted": 1,
            "tableCreated": table_was_created
        }
        
        headers = {'Access-Control-Allow-Origin': '*'}
        return json.dumps(response), 200, headers
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        
        # Check if this is a BigQuery-related error that might be transient
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ['table', 'schema', 'not found', 'creation']):
            logger.warning(f"BigQuery-related error, this might be transient: {str(e)}")
            
        error_response = {
            "status": "error", 
            "message": f"Failed to process webhook: {str(e)}",
            "error_type": "processing_error"
        }
        
        headers = {'Access-Control-Allow-Origin': '*'}
        return json.dumps(error_response), 500, headers
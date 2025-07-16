import json
import logging
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


def create_table_if_not_exists(dataset_id: str, table_id: str) -> None:
    """Create BigQuery table if it doesn't exist with the appropriate schema."""
    
    table_ref = client.dataset(dataset_id).table(table_id)
    
    try:
        # Check if table exists
        client.get_table(table_ref)
        logger.info(f"Table {dataset_id}.{table_id} already exists")
        return
    except Exception:
        # Table doesn't exist, create it
        logger.info(f"Creating table {dataset_id}.{table_id}")
        
        # Define schema based on the contact form structure
        schema = [
            SchemaField("name", "STRING", mode="NULLABLE"),
            SchemaField("email", "STRING", mode="NULLABLE"),
            SchemaField("company", "STRING", mode="NULLABLE"),
            SchemaField("phone", "STRING", mode="NULLABLE"),
            SchemaField("subject", "STRING", mode="NULLABLE"),
            SchemaField("message", "STRING", mode="NULLABLE"),
            SchemaField("priority", "STRING", mode="NULLABLE"),
            SchemaField("contactMethod", "STRING", mode="NULLABLE"),
            SchemaField("timestamp", "TIMESTAMP", mode="NULLABLE"),
            SchemaField("source", "STRING", mode="NULLABLE"),
            SchemaField("inserted_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        table = bigquery.Table(table_ref, schema=schema)
        table = client.create_table(table)
        logger.info(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")


def insert_data_to_bigquery(dataset_id: str, table_id: str, form_data: Dict[str, Any]) -> None:
    """Insert form data into BigQuery table."""
    
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
    
    # Get table reference
    table_ref = client.dataset(dataset_id).table(table_id)
    table = client.get_table(table_ref)
    
    # Insert the row
    errors = client.insert_rows_json(table, [row_to_insert])
    
    if errors:
        raise Exception(f"Failed to insert data: {errors}")
    
    logger.info(f"Successfully inserted data into {dataset_id}.{table_id}")


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
        create_table_if_not_exists(dataset_id, table_name)
        
        # Insert data into BigQuery
        insert_data_to_bigquery(dataset_id, table_name, form_data)
        
        # Return success response
        response = {
            "status": "success",
            "message": f"Data successfully inserted into {dataset_id}.{table_name}",
            "formName": form_name,
            "recordsInserted": 1
        }
        
        headers = {'Access-Control-Allow-Origin': '*'}
        return json.dumps(response), 200, headers
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        
        error_response = {
            "status": "error",
            "message": f"Failed to process webhook: {str(e)}"
        }
        
        headers = {'Access-Control-Allow-Origin': '*'}
        return json.dumps(error_response), 500, headers
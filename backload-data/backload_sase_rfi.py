#!/usr/bin/env python3
"""
SASE RFI Data Backload Script

This script backloads the SASE RFI scorecard data from CSV to BigQuery.
It processes vendor responses and inserts them into the opex_dev.network_security_survey table.
"""

import csv
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

from google.cloud import bigquery
from google.cloud.bigquery import SchemaField

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize BigQuery client
client = bigquery.Client()

# Constants
DATASET_ID = "opex_dev"
TABLE_ID = "network_security_survey"
CSV_FILE_PATH = "SASE RFI.csv"

# Survey questions mapping from the web form
SURVEY_QUESTIONS = [
    {"question": "Company Name", "data_type": "Company Information", "input_type": "text", "field_id": "field_1"},
    {"question": "Year founded", "data_type": "Company Information", "input_type": "number", "field_id": "field_2"},
    {"question": "Headquarters", "data_type": "Company Information", "input_type": "text", "field_id": "field_3"},
    {"question": "Parent Company", "data_type": "Company Information", "input_type": "text", "field_id": "field_4"},
    {"question": "Year SD WAN Launched", "data_type": "Platform History", "input_type": "number", "field_id": "field_5"},
    {"question": "Year SASE Platform launched", "data_type": "Platform History", "input_type": "number", "field_id": "field_6"},
    {"question": "Do you offer circuit procurement", "data_type": "Circuit Management", "input_type": "radio", "field_id": "field_7"},
    {"question": "Do you hold direct contracts with the circuit providers, or do you leverage an aggregator?", "data_type": "Circuit Management", "input_type": "radio", "field_id": "field_8"},
    {"question": "Do you offer circuit management", "data_type": "Circuit Management", "input_type": "radio", "field_id": "field_9"},
    {"question": "Do you actively monitor and proactively open tickets for circuit issues", "data_type": "Circuit Management", "input_type": "radio", "field_id": "field_10"},
    {"question": "Is onsite hardware replacement included", "data_type": "Support Services", "input_type": "radio", "field_id": "field_11"},
    {"question": "What is your SLA for onsite replacement", "data_type": "Support Services", "input_type": "textarea", "field_id": "field_12"},
    {"question": "What is your SLA for P1 incident response", "data_type": "Support Services", "input_type": "textarea", "field_id": "field_13"},
    {"question": "Do you provide an uptime SLA if both hardware and circuits are procured through you? What is the SLA?", "data_type": "SLA Management", "input_type": "textarea", "field_id": "field_14"},
    {"question": "Do you provide client access to the SD-WAN portal (co-management)", "data_type": "Portal Access", "input_type": "radio", "field_id": "field_15"},
    {"question": "Can you shift traffic mid-session", "data_type": "SD-WAN Features", "input_type": "radio", "field_id": "field_16"},
    {"question": "Do you support throughput monitoring", "data_type": "SD-WAN Features", "input_type": "radio", "field_id": "field_17"},
    {"question": "Do you support full mesh? If so, what is the maximum number of sites in a full mesh?", "data_type": "Network Topology", "input_type": "textarea", "field_id": "field_18"},
    {"question": "How do you connect into AWS and Azure?", "data_type": "Cloud Integration", "input_type": "textarea", "field_id": "field_19"},
    {"question": "How do you license HA?", "data_type": "Licensing", "input_type": "textarea", "field_id": "field_20"},
    {"question": "Do you have a middle mile network?", "data_type": "Network Infrastructure", "input_type": "radio", "field_id": "field_21"},
    {"question": "Do you support packet duplication", "data_type": "Advanced Features", "input_type": "radio", "field_id": "field_22"},
    {"question": "Do you support forward error correction", "data_type": "Advanced Features", "input_type": "radio", "field_id": "field_23"},
    {"question": "What is your historical reporting retention period", "data_type": "Reporting", "input_type": "textarea", "field_id": "field_24"},
    {"question": "Do you provide real-time traffic visibility and analytics", "data_type": "Analytics", "input_type": "radio", "field_id": "field_25"},
    {"question": "What is your speed to failover between circuits", "data_type": "Performance", "input_type": "textarea", "field_id": "field_26"},
    {"question": "Can you handle inbound traffic for hosted systems", "data_type": "Cloud Firewall", "input_type": "radio", "field_id": "field_27"},
    {"question": "Do you offer client specific static IPs", "data_type": "IP Management", "input_type": "radio", "field_id": "field_28"},
    {"question": "Do you have unified ruleset across all locations/POPs", "data_type": "Security Management", "input_type": "radio", "field_id": "field_29"},
    {"question": "Do you provide content filtering", "data_type": "Security Features", "input_type": "radio", "field_id": "field_30"},
    {"question": "Do you tie back to endpoint context", "data_type": "Security Features", "input_type": "radio", "field_id": "field_31"},
    {"question": "Do you provide anti-malware (signature based)", "data_type": "Security Features", "input_type": "radio", "field_id": "field_32"},
    {"question": "Do you provide next gen anti-malware (ML Based)", "data_type": "Security Features", "input_type": "radio", "field_id": "field_33"},
    {"question": "Do you provide IPS/IDS", "data_type": "Security Features", "input_type": "radio", "field_id": "field_34"},
    {"question": "Do you provide CASB", "data_type": "Security Features", "input_type": "radio", "field_id": "field_35"},
    {"question": "Do you provide DLP", "data_type": "Security Features", "input_type": "radio", "field_id": "field_36"},
    {"question": "Can you export logs in near real time to MDR provider - SPLUNK", "data_type": "Integration", "input_type": "radio", "field_id": "field_37"},
    {"question": "Do you support multiple WAN segments (Multiple VRFs)", "data_type": "Network Segmentation", "input_type": "radio", "field_id": "field_38"},
    {"question": "Is remote access always on", "data_type": "Remote Access", "input_type": "radio", "field_id": "field_39"},
    {"question": "Do all cloud firewall services apply to remote access clients", "data_type": "Remote Access", "input_type": "radio", "field_id": "field_40"},
    {"question": "Do you auto-select nearest POP", "data_type": "Remote Access", "input_type": "radio", "field_id": "field_41"},
    {"question": "How many POPs do you have", "data_type": "Infrastructure", "input_type": "number", "field_id": "field_42"},
    {"question": "Do you have access to middle mile network for optimal egress", "data_type": "Network Optimization", "input_type": "radio", "field_id": "field_43"},
    {"question": "What is your maximum throughput", "data_type": "Performance", "input_type": "textarea", "field_id": "field_44"}
]


def sanitize_field_name(question: str) -> str:
    """
    Convert question text to sanitized field name matching web form convention.
    
    Args:
        question: The question text
        
    Returns:
        Sanitized field name
    """
    return re.sub(r'[^a-zA-Z0-9]', '_', question).lower()


def create_table_if_not_exists(dataset_id: str, table_id: str, form_data: Dict[str, Any]) -> bool:
    """
    Create BigQuery table if it doesn't exist with dynamic schema based on form data.
    This replicates the logic from the existing Cloud Function.
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
            time.sleep(1)  # Give a moment for schema update to propagate
        
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
            
            time.sleep(2)  # Wait for table creation to fully propagate
            return True
            
        except Exception as create_error:
            logger.error(f"Failed to create table {dataset_id}.{table_id}: {str(create_error)}")
            raise create_error


def insert_data_to_bigquery(dataset_id: str, table_id: str, form_data: Dict[str, Any], retry_count: int = 3) -> None:
    """
    Insert form data into BigQuery table with retry logic.
    This replicates the logic from the existing Cloud Function.
    """
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
            
            logger.info(f"Successfully inserted data into {dataset_id}.{table_id} for vendor: {form_data.get('company_name', 'Unknown')}")
            return
            
        except Exception as e:
            logger.warning(f"Insert attempt {attempt + 1} failed: {str(e)}")
            if attempt == retry_count - 1:  # Last attempt
                raise e
            time.sleep(2)  # Wait before retry


def validate_vendor_data(vendor_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate vendor data before insertion.
    
    Args:
        vendor_data: Dictionary containing vendor data
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = ["company_name", "timestamp", "source"]
    for field in required_fields:
        if field not in vendor_data or not vendor_data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate company name is not empty
    if "company_name" in vendor_data and not vendor_data["company_name"].strip():
        errors.append("Company name cannot be empty")
    
    # Validate timestamp format
    if "timestamp" in vendor_data and vendor_data["timestamp"]:
        try:
            datetime.fromisoformat(vendor_data["timestamp"].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            errors.append(f"Invalid timestamp format: {vendor_data['timestamp']}")
    
    # Validate field names (should not contain spaces or special chars except underscore)
    for field_name in vendor_data.keys():
        if not re.match(r'^[a-zA-Z0-9_]+$', field_name):
            errors.append(f"Invalid field name format: {field_name}")
    
    # Check for minimum number of survey responses
    survey_fields = [k for k in vendor_data.keys() if k not in ["timestamp", "source", "contact_name", "contact_email", "contact_company", "contact_phone", "inserted_at"]]
    if len(survey_fields) < 5:
        errors.append(f"Too few survey responses: {len(survey_fields)} (minimum 5 expected)")
    
    return len(errors) == 0, errors


def normalize_response(response: str, input_type: str) -> str:
    """
    Normalize vendor responses to match web form conventions.
    
    Args:
        response: Raw response from CSV
        input_type: Type of input (radio, text, textarea, number)
        
    Returns:
        Normalized response
    """
    if not response or response.strip() == "":
        return ""
    
    response = response.strip()
    
    # Handle radio button responses
    if input_type == "radio":
        response_lower = response.lower()
        if any(word in response_lower for word in ["yes", "true", "supported", "available", "included"]):
            return "yes"
        elif any(word in response_lower for word in ["no", "false", "not supported", "not available", "not included"]):
            return "no"
        elif any(word in response_lower for word in ["partial", "limited", "some", "depends"]):
            return "partial"
        else:
            # Default complex responses to partial for radio fields
            return "partial" if len(response) > 10 else "yes"
    
    # For text, textarea, and number fields, return as-is
    return response


def create_csv_to_survey_mapping() -> Dict[str, Dict]:
    """
    Create a mapping from CSV question text to survey question metadata.
    
    Returns:
        Dictionary mapping CSV questions to survey question info
    """
    # Manual mapping of CSV questions to survey questions
    csv_mappings = {
        "Company Name": {"question": "Company Name", "input_type": "text"},
        "Year founded": {"question": "Year founded", "input_type": "number"},
        "Headquarters": {"question": "Headquarters", "input_type": "text"},
        "Ownership": {"question": "Parent Company", "input_type": "text"}, # Map Ownership to Parent Company
        "Parent Company": {"question": "Parent Company", "input_type": "text"},
        "Year SD WAN Launched": {"question": "Year SD WAN Launched", "input_type": "number"},
        "Year SASE Platform launched": {"question": "Year SASE Platform launched", "input_type": "number"},
        "Do you offer circuit procurement": {"question": "Do you offer circuit procurement", "input_type": "radio"},
        "Do you hold direct contracts with the circuit providers, or do you leverage an aggregator?": {"question": "Do you hold direct contracts with the circuit providers, or do you leverage an aggregator?", "input_type": "radio"},
        "Do you offer circuit management": {"question": "Do you offer circuit management", "input_type": "radio"},
        "Do you actively monitor and proactively open tickets for circuit issues": {"question": "Do you actively monitor and proactively open tickets for circuit issues", "input_type": "radio"},
        "Is onsite hardware replacement included": {"question": "Is onsite hardware replacement included", "input_type": "radio"},
        "What is your SLA for onsite replacement": {"question": "What is your SLA for onsite replacement", "input_type": "textarea"},
        "What is your SLA for P1 incident response": {"question": "What is your SLA for P1 incident response", "input_type": "textarea"},
        "Do you provide an uptime SLA if both hardware and circuits are procured through you? What is the SLA?": {"question": "Do you provide an uptime SLA if both hardware and circuits are procured through you? What is the SLA?", "input_type": "textarea"},
        "Do you provide client access to the SD-WAN portal (co-management)": {"question": "Do you provide client access to the SD-WAN portal (co-management)", "input_type": "radio"},
        "Can you shift traffic mid-session": {"question": "Can you shift traffic mid-session", "input_type": "radio"},
        "Throughput monitoring": {"question": "Do you support throughput monitoring", "input_type": "radio"},
        "Do you support full mesh? If so, what is the maximum number of sites in a full mesh?": {"question": "Do you support full mesh? If so, what is the maximum number of sites in a full mesh?", "input_type": "textarea"},
        "How do you connect into AWS and Azure?": {"question": "How do you connect into AWS and Azure?", "input_type": "textarea"},
        "How do you license HA?": {"question": "How do you license HA?", "input_type": "textarea"},
        "Do you have a middle mile network?": {"question": "Do you have a middle mile network?", "input_type": "radio"},
        "Support packet duplication": {"question": "Do you support packet duplication", "input_type": "radio"},
        "Support forward error correction": {"question": "Do you support forward error correction", "input_type": "radio"},
        "Historical Reporting (retention period)": {"question": "What is your historical reporting retention period", "input_type": "textarea"},
        "Real-time Traffic visibility and analytics": {"question": "Do you provide real-time traffic visibility and analytics", "input_type": "radio"},
        "Speed to failover between circuits": {"question": "What is your speed to failover between circuits", "input_type": "textarea"},
        "Can you handle inbound traffic for hosted systems": {"question": "Can you handle inbound traffic for hosted systems", "input_type": "radio"},
        "Do you offer client specific static IPs": {"question": "Do you offer client specific static IPs", "input_type": "radio"},
        "Unified ruleset across all locations/POPs": {"question": "Do you have unified ruleset across all locations/POPs", "input_type": "radio"},
        "Content filtering": {"question": "Do you provide content filtering", "input_type": "radio"},
        "Tie back to endpoint context": {"question": "Do you tie back to endpoint context", "input_type": "radio"},
        "Anti-malware (signature based)": {"question": "Do you provide anti-malware (signature based)", "input_type": "radio"},
        "Next Gen Anti-malware (ML Based)": {"question": "Do you provide next gen anti-malware (ML Based)", "input_type": "radio"},
        "IPS/IDS": {"question": "Do you provide IPS/IDS", "input_type": "radio"},
        "CASB": {"question": "Do you provide CASB", "input_type": "radio"},
        "DLP": {"question": "Do you provide DLP", "input_type": "radio"},
        "Ability to export logs in near real time to MDR provider - SPLUNK": {"question": "Can you export logs in near real time to MDR provider - SPLUNK", "input_type": "radio"},
        "Do you support multiple WAN segments (Multiple VRFs)": {"question": "Do you support multiple WAN segments (Multiple VRFs)", "input_type": "radio"},
        "Always on": {"question": "Is remote access always on", "input_type": "radio"},
        "Do all cloud firewall services apply to remote access clients": {"question": "Do all cloud firewall services apply to remote access clients", "input_type": "radio"},
        "Auto-select nearest POP": {"question": "Do you auto-select nearest POP", "input_type": "radio"},
        "Number of POPs": {"question": "How many POPs do you have", "input_type": "number"},
        "Access to middle mile network for optimal egress": {"question": "Do you have access to middle mile network for optimal egress", "input_type": "radio"},
        "Maximum throughput": {"question": "What is your maximum throughput", "input_type": "textarea"}
    }
    
    # Convert to field name mappings
    mapping = {}
    for csv_question, survey_info in csv_mappings.items():
        survey_question = survey_info["question"]
        field_name = sanitize_field_name(survey_question)
        mapping[csv_question] = {
            "field_name": field_name,
            "input_type": survey_info["input_type"],
            "survey_question": survey_question
        }
    
    return mapping


def parse_csv_and_extract_vendors(csv_file_path: str) -> List[Dict[str, Any]]:
    """
    Parse the CSV file and extract vendor data.
    
    Args:
        csv_file_path: Path to the SASE RFI CSV file
        
    Returns:
        List of vendor data dictionaries
    """
    vendors = []
    question_mapping = create_csv_to_survey_mapping()
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)
    
    # Find vendor names row (row 3, contains company names)
    vendor_names = []
    if len(rows) > 3:
        vendor_row = rows[3]  # Row 4 (0-indexed) contains "Company Name" data
        for i, cell in enumerate(vendor_row):
            if i >= 2 and cell.strip():  # Skip first two columns (Question and Weighting)
                vendor_names.append(cell.strip())
    
    logger.info(f"Found {len(vendor_names)} vendors: {vendor_names}")
    
    # Process each vendor
    for vendor_idx, vendor_name in enumerate(vendor_names):
        vendor_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "sase-rfi-backload",
            "contact_name": "SASE RFI Assessment",
            "contact_email": "backload@opextech.com",
            "contact_company": vendor_name,
            "contact_phone": ""
        }
        
        # Map vendor name to company_name field
        vendor_data["company_name"] = vendor_name
        
        # Process each question row
        for row_idx, row in enumerate(rows):
            if len(row) < 3:
                continue
                
            question_text = row[0].strip() if row[0] else ""
            
            # Skip header rows and non-question rows
            if not question_text or question_text in ["Question", "Project Scorecard - SASE", "Company Information", "Management", "SD WAN Requirements", "Cloud Firewall", "Remote Access", "TOTALS"]:
                continue
                
            # Skip scoring and empty rows
            if question_text in ["SCORING", "Binary", "Subjective", "Meets expectation", "Does not meet expectation", "Exceeds expectation", "No capability/offering"] or question_text == "":
                continue
            
            # Look for exact match in our mapping
            if question_text in question_mapping:
                mapping_info = question_mapping[question_text]
                field_name = mapping_info["field_name"]
                input_type = mapping_info["input_type"]
                
                # Get vendor response (skip question and weighting columns, then find vendor column)
                vendor_col_idx = 2 + (vendor_idx * 3)  # Each vendor has 3 columns (Response, Points, Weighted Total)
                
                if vendor_col_idx < len(row):
                    raw_response = row[vendor_col_idx].strip() if row[vendor_col_idx] else ""
                    normalized_response = normalize_response(raw_response, input_type)
                    
                    if normalized_response:
                        vendor_data[field_name] = normalized_response
                        logger.debug(f"Mapped '{question_text}' -> '{field_name}' = '{normalized_response}' for {vendor_name}")
            else:
                logger.debug(f"No mapping found for question: '{question_text}'")
        
        vendors.append(vendor_data)
    
    return vendors


def main():
    """Main function to execute the backload process."""
    logger.info("Starting SASE RFI data backload process...")
    
    try:
        # Parse CSV and extract vendor data
        vendors = parse_csv_and_extract_vendors(CSV_FILE_PATH)
        logger.info(f"Extracted data for {len(vendors)} vendors")
        
        # Process each vendor
        successful_inserts = 0
        failed_inserts = 0
        
        for vendor_data in vendors:
            vendor_name = vendor_data.get("company_name", "Unknown")
            logger.info(f"Processing vendor: {vendor_name}")
            
            # Validate vendor data
            is_valid, validation_errors = validate_vendor_data(vendor_data)
            if not is_valid:
                logger.error(f"Validation failed for {vendor_name}: {', '.join(validation_errors)}")
                failed_inserts += 1
                continue
            
            try:
                # Create table if it doesn't exist (using first vendor's data to define schema)
                if vendor_data == vendors[0]:
                    create_table_if_not_exists(DATASET_ID, TABLE_ID, vendor_data)
                
                # Insert vendor data
                insert_data_to_bigquery(DATASET_ID, TABLE_ID, vendor_data)
                successful_inserts += 1
                
            except Exception as e:
                logger.error(f"Failed to insert data for {vendor_name}: {str(e)}")
                failed_inserts += 1
                continue
        
        # Summary
        logger.info(f"Backload process completed!")
        logger.info(f"Successfully inserted: {successful_inserts} vendors")
        logger.info(f"Failed insertions: {failed_inserts} vendors")
        
        if failed_inserts > 0:
            logger.warning(f"Some vendors failed to be inserted. Check logs above for details.")
        
        if successful_inserts == 0:
            raise Exception("No vendors were successfully inserted!")
            
    except Exception as e:
        logger.error(f"Error during backload process: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
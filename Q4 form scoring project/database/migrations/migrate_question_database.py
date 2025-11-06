#!/usr/bin/env python3
"""
Question Database Migration Script
Migrates questions from CSV to BigQuery form_builder.question_database table

Reads: Question Database(Sheet1).csv (1,042 questions)
Loads: form_builder.question_database table in BigQuery

Usage:
    python migrate_question_database.py [--dry-run] [--skip-validation]

Created: November 5, 2025
"""

import os
import sys
import csv
import uuid
import re
from pathlib import Path
from datetime import datetime
from google.cloud import bigquery
from google.api_core import exceptions

# Project configuration
PROJECT_ID = "opex-data-lake-k23k4y98m"
DATASET_ID = "form_builder"
TABLE_ID = "question_database"
CSV_FILE = "Question Database(Sheet1).csv"

# CSV column mapping
CSV_COLUMNS = {
    'question': 'Question',
    'default_weight': 'Default Weight',
    'category': 'Category',
    'opportunity_type': 'Opportunity Type',
    'opportunity_subtypes': 'Opportunity Subtypes'
}


class bcolors:
    """Terminal colors"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def log_info(message):
    print(f"{bcolors.OKBLUE}ℹ {message}{bcolors.ENDC}")


def log_success(message):
    print(f"{bcolors.OKGREEN}✓ {message}{bcolors.ENDC}")


def log_warning(message):
    print(f"{bcolors.WARNING}⚠ {message}{bcolors.ENDC}")


def log_error(message):
    print(f"{bcolors.FAIL}✗ {message}{bcolors.ENDC}")


def log_header(message):
    print(f"\n{bcolors.HEADER}{bcolors.BOLD}{'=' * 80}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{message}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{'=' * 80}{bcolors.ENDC}\n")


def determine_input_type(question_text):
    """
    Determine the appropriate input type based on question text patterns

    Args:
        question_text: The question text

    Returns:
        str: Input type (text, textarea, number, radio)
    """
    question_lower = question_text.lower()

    # Radio buttons for yes/no questions
    if any(pattern in question_lower for pattern in [
        'do you', 'can you', 'will you', 'are you', 'is', 'does', 'have you'
    ]):
        return 'radio'

    # Number input for numeric questions
    if any(pattern in question_lower for pattern in [
        'how many', 'number of', 'count', 'ratio', 'percentage', '%'
    ]):
        return 'number'

    # Textarea for descriptive questions
    if any(pattern in question_lower for pattern in [
        'describe', 'list', 'explain', 'detail', 'provide', 'what are'
    ]):
        return 'textarea'

    # Default to text input
    return 'text'


def sanitize_weight(weight_str):
    """
    Sanitize weight value

    Args:
        weight_str: Raw weight from CSV

    Returns:
        str: Sanitized weight ("Info" or numeric string)
    """
    if not weight_str or weight_str.strip() == '':
        return "Info"  # Default for empty weights

    weight_str = weight_str.strip()

    # Already "Info"
    if weight_str.lower() == 'info':
        return "Info"

    # Try to parse as number
    try:
        weight_num = float(weight_str)
        return str(int(weight_num))  # Convert to integer string
    except ValueError:
        log_warning(f"Invalid weight value '{weight_str}', defaulting to 'Info'")
        return "Info"


def validate_question(question_data, row_num):
    """
    Validate a single question record

    Args:
        question_data: Dictionary with question fields
        row_num: Row number in CSV (for error reporting)

    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []

    # Required fields
    if not question_data.get('question_text'):
        errors.append(f"Row {row_num}: Missing question text")

    if not question_data.get('category'):
        errors.append(f"Row {row_num}: Missing category")

    # Question text length
    if question_data.get('question_text') and len(question_data['question_text']) > 1000:
        errors.append(f"Row {row_num}: Question text too long (max 1000 chars)")

    # Valid weight
    weight = question_data.get('default_weight', '')
    if weight and weight != 'Info':
        try:
            weight_num = int(weight)
            if weight_num < 0 or weight_num > 100:
                errors.append(f"Row {row_num}: Weight {weight_num} out of range (0-100)")
        except ValueError:
            errors.append(f"Row {row_num}: Invalid weight '{weight}'")

    return (len(errors) == 0, errors)


def read_csv_file(csv_path):
    """
    Read and parse CSV file

    Args:
        csv_path: Path to CSV file

    Returns:
        list: List of question dictionaries
    """
    log_header("Reading CSV File")

    questions = []
    validation_errors = []

    try:
        # Try multiple encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        csv_data = None
        used_encoding = None

        for encoding in encodings:
            try:
                with open(csv_path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    csv_data = list(reader)
                    used_encoding = encoding
                    log_info(f"Successfully read CSV with {encoding} encoding")
                    break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if csv_data is None:
            log_error("Could not read CSV with any supported encoding")
            return [], []

        for row_num, row in enumerate(csv_data, start=2):  # Start at 2 (header is row 1)
            # Generate UUID
            question_id = str(uuid.uuid4())

            # Map CSV columns to BigQuery schema
            question_data = {
                'question_id': question_id,
                'question_text': row[CSV_COLUMNS['question']].strip(),
                'default_weight': sanitize_weight(row[CSV_COLUMNS['default_weight']]),
                'category': row[CSV_COLUMNS['category']].strip() if row[CSV_COLUMNS['category']] else 'Uncategorized',
                'opportunity_type': row[CSV_COLUMNS['opportunity_type']].strip() if row[CSV_COLUMNS['opportunity_type']] else 'All',
                'opportunity_subtypes': row[CSV_COLUMNS['opportunity_subtypes']].strip() if row[CSV_COLUMNS['opportunity_subtypes']] else 'All',
                'input_type': determine_input_type(row[CSV_COLUMNS['question']]),
                'input_options': '["Yes", "No", "Partial"]',  # Default for radio questions
                'placeholder_text': None,
                'help_text': None,
                'validation_rules': None,
                'tags': [],
                'version': 1,
                'created_at': datetime.utcnow(),
                'updated_at': None,
                'is_active': True,
                'usage_count': 0,
                'last_used_at': None
            }

            # Validate question
            is_valid, errors = validate_question(question_data, row_num)
            if not is_valid:
                validation_errors.extend(errors)
                continue

            questions.append(question_data)

        log_success(f"Read {len(questions)} questions from CSV")

        if validation_errors:
            log_warning(f"Found {len(validation_errors)} validation errors:")
            for error in validation_errors[:10]:  # Show first 10 errors
                log_error(f"  {error}")
            if len(validation_errors) > 10:
                log_warning(f"  ... and {len(validation_errors) - 10} more errors")

        return questions, validation_errors

    except FileNotFoundError:
        log_error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Error reading CSV: {str(e)}")
        sys.exit(1)


def load_to_bigquery(client, questions, dry_run=False):
    """
    Load questions to BigQuery

    Args:
        client: BigQuery client
        questions: List of question dictionaries
        dry_run: If True, don't actually insert data

    Returns:
        bool: Success status
    """
    log_header("Loading to BigQuery")

    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    if dry_run:
        log_info(f"[DRY RUN] Would load {len(questions)} questions to {table_ref}")
        log_info(f"[DRY RUN] Sample question: {questions[0]['question_text']}")
        return True

    try:
        # Check if table exists and is empty
        table = client.get_table(table_ref)

        # Query current row count
        query = f"SELECT COUNT(*) as count FROM `{table_ref}`"
        result = list(client.query(query).result())[0]
        current_count = result.count

        if current_count > 0:
            log_warning(f"Table already contains {current_count} rows")
            response = input("Do you want to DELETE existing data and reload? (yes/no): ")
            if response.lower() != 'yes':
                log_info("Migration cancelled")
                return False

            # Delete existing data
            log_info("Deleting existing data...")
            delete_query = f"DELETE FROM `{table_ref}` WHERE TRUE"
            client.query(delete_query).result()
            log_success("Existing data deleted")

        # Insert questions in batches
        batch_size = 100
        total_inserted = 0

        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]

            # Convert datetime objects to strings for BigQuery
            for q in batch:
                q['created_at'] = q['created_at'].isoformat()
                if q['updated_at']:
                    q['updated_at'] = q['updated_at'].isoformat()
                if q['last_used_at']:
                    q['last_used_at'] = q['last_used_at'].isoformat()

            errors = client.insert_rows_json(table_ref, batch)

            if errors:
                log_error(f"Errors inserting batch {i // batch_size + 1}: {errors}")
                return False

            total_inserted += len(batch)
            log_info(f"Inserted {total_inserted}/{len(questions)} questions...")

        log_success(f"Successfully loaded {total_inserted} questions to BigQuery")
        return True

    except exceptions.NotFound:
        log_error(f"Table {table_ref} not found. Run deploy_schemas.py first.")
        return False
    except Exception as e:
        log_error(f"Error loading to BigQuery: {str(e)}")
        return False


def generate_statistics(questions):
    """
    Generate statistics about the questions

    Args:
        questions: List of question dictionaries
    """
    log_header("Question Statistics")

    # Count by category
    categories = {}
    for q in questions:
        cat = q['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("Questions by Category:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")

    # Count by opportunity type
    opp_types = {}
    for q in questions:
        ot = q['opportunity_type']
        opp_types[ot] = opp_types.get(ot, 0) + 1

    print("\nQuestions by Opportunity Type:")
    for ot, count in sorted(opp_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ot}: {count}")

    # Count by input type
    input_types = {}
    for q in questions:
        it = q['input_type']
        input_types[it] = input_types.get(it, 0) + 1

    print("\nQuestions by Input Type:")
    for it, count in sorted(input_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {it}: {count}")

    # Count by weight
    info_count = sum(1 for q in questions if q['default_weight'] == 'Info')
    scored_count = len(questions) - info_count

    print(f"\nScoring:")
    print(f"  Info (not scored): {info_count}")
    print(f"  Scored: {scored_count}")


def main():
    """Main migration function"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate Question Database to BigQuery")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without migrating")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation checks")
    parser.add_argument("--csv-path", type=str, help="Path to CSV file (default: auto-detect)")
    args = parser.parse_args()

    # Find CSV file
    if args.csv_path:
        csv_path = Path(args.csv_path)
    else:
        # Try multiple locations
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent.parent.parent  # Go up 3 levels to repo root

        possible_paths = [
            repo_root / CSV_FILE,
            Path.cwd() / CSV_FILE,
            Path.cwd().parent / CSV_FILE
        ]

        csv_path = None
        for path in possible_paths:
            if path.exists():
                csv_path = path
                break

        if not csv_path:
            log_error(f"CSV file '{CSV_FILE}' not found in any of these locations:")
            for path in possible_paths:
                log_error(f"  {path}")
            sys.exit(1)

    log_info(f"Using CSV file: {csv_path}")

    # Read CSV
    questions, validation_errors = read_csv_file(csv_path)

    if validation_errors and not args.skip_validation:
        log_error(f"Validation failed with {len(validation_errors)} errors. Fix errors or use --skip-validation")
        sys.exit(1)

    # Generate statistics
    generate_statistics(questions)

    if args.dry_run:
        log_header("Dry Run Complete")
        log_info(f"Would migrate {len(questions)} questions to BigQuery")
        return

    # Initialize BigQuery client
    log_header("Initializing BigQuery Client")
    try:
        client = bigquery.Client(project=PROJECT_ID)
        log_success(f"Connected to project {PROJECT_ID}")
    except Exception as e:
        log_error(f"Failed to initialize BigQuery client: {str(e)}")
        sys.exit(1)

    # Load to BigQuery
    success = load_to_bigquery(client, questions, dry_run=args.dry_run)

    if success:
        log_header("Migration Complete")
        log_success(f"Successfully migrated {len(questions)} questions!")
        log_info(f"Table: {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}")

        # Verify
        log_info("Verifying data...")
        query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`"
        result = list(client.query(query).result())[0]
        log_success(f"Verified: {result.count} rows in BigQuery")

        sys.exit(0)
    else:
        log_error("Migration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

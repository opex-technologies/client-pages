#!/usr/bin/env python3
"""
BigQuery Schema Deployment Script
Deploys all table schemas for the Opex Form Builder & Response Scorer project

Usage:
    python deploy_schemas.py [--dry-run] [--tables TABLE1,TABLE2,...]

Options:
    --dry-run: Show what would be deployed without actually deploying
    --tables: Comma-separated list of specific tables to deploy (default: all)

Created: November 5, 2025
"""

import os
import sys
from pathlib import Path
from google.cloud import bigquery
from google.api_core import exceptions
import argparse
import time

# Project configuration
PROJECT_ID = "opex-data-lake-k23k4y98m"
LOCATION = "US"

# Schema files mapping: (dataset, table_name) -> schema_file
SCHEMA_FILES = {
    ("auth", "users"): "auth_users.sql",
    ("auth", "permission_groups"): "auth_permission_groups.sql",
    ("auth", "sessions"): "auth_sessions.sql",
    ("form_builder", "form_templates"): "form_templates.sql",
    ("form_builder", "question_database"): "question_database.sql",
    ("scoring", "scored_responses"): "scored_responses.sql",
    ("scoring", "question_scores"): "question_scores.sql",
    ("scoring", "audit_trail"): "audit_trail.sql",
    ("opex_dev", "providers"): "providers.sql",
    ("opex_dev", "clients"): "clients.sql",
}

# Datasets to create (if they don't exist)
DATASETS = {
    "auth": "Authentication and user management data",
    "form_builder": "Form Builder application data",
    "scoring": "Response scoring and audit data",
    "opex_dev": "Survey responses and operational data (existing)"
}


class bcolors:
    """Terminal colors for pretty output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def log_info(message):
    """Print info message"""
    print(f"{bcolors.OKBLUE}ℹ {message}{bcolors.ENDC}")


def log_success(message):
    """Print success message"""
    print(f"{bcolors.OKGREEN}✓ {message}{bcolors.ENDC}")


def log_warning(message):
    """Print warning message"""
    print(f"{bcolors.WARNING}⚠ {message}{bcolors.ENDC}")


def log_error(message):
    """Print error message"""
    print(f"{bcolors.FAIL}✗ {message}{bcolors.ENDC}")


def log_header(message):
    """Print header message"""
    print(f"\n{bcolors.HEADER}{bcolors.BOLD}{'=' * 80}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{message}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{'=' * 80}{bcolors.ENDC}\n")


def create_dataset_if_not_exists(client, dataset_id, description, location=LOCATION):
    """
    Create BigQuery dataset if it doesn't exist

    Args:
        client: BigQuery client
        dataset_id: Dataset ID (without project prefix)
        description: Dataset description
        location: Dataset location

    Returns:
        bool: True if created, False if already existed
    """
    dataset_ref = f"{PROJECT_ID}.{dataset_id}"

    try:
        client.get_dataset(dataset_ref)
        log_info(f"Dataset {dataset_id} already exists")
        return False
    except exceptions.NotFound:
        # Dataset doesn't exist, create it
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        dataset.description = description

        dataset = client.create_dataset(dataset, timeout=30)
        log_success(f"Created dataset {dataset_id}")
        return True


def read_schema_file(schema_file):
    """
    Read SQL schema file

    Args:
        schema_file: Path to schema file

    Returns:
        str: SQL content
    """
    with open(schema_file, 'r') as f:
        return f.read()


def deploy_table(client, dataset_id, table_name, schema_file, dry_run=False):
    """
    Deploy a single table schema

    Args:
        client: BigQuery client
        dataset_id: Dataset ID
        table_name: Table name
        schema_file: Path to schema SQL file
        dry_run: If True, don't actually deploy

    Returns:
        bool: True if successful, False otherwise
    """
    table_ref = f"{PROJECT_ID}.{dataset_id}.{table_name}"

    try:
        # Read schema file
        sql = read_schema_file(schema_file)

        if dry_run:
            log_info(f"[DRY RUN] Would deploy {table_ref}")
            return True

        # Execute CREATE TABLE statement
        query_job = client.query(sql)
        query_job.result()  # Wait for completion

        log_success(f"Deployed table {dataset_id}.{table_name}")
        return True

    except exceptions.Conflict:
        log_warning(f"Table {table_ref} already exists (skipped)")
        return True

    except Exception as e:
        log_error(f"Failed to deploy {table_ref}: {str(e)}")
        return False


def verify_deployment(client, dataset_id, table_name):
    """
    Verify table was deployed successfully

    Args:
        client: BigQuery client
        dataset_id: Dataset ID
        table_name: Table name

    Returns:
        bool: True if table exists and is accessible
    """
    table_ref = f"{PROJECT_ID}.{dataset_id}.{table_name}"

    try:
        table = client.get_table(table_ref)
        log_success(f"Verified {dataset_id}.{table_name} ({table.num_rows} rows, {len(table.schema)} columns)")
        return True
    except exceptions.NotFound:
        log_error(f"Table {table_ref} not found after deployment")
        return False
    except Exception as e:
        log_error(f"Failed to verify {table_ref}: {str(e)}")
        return False


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy BigQuery schemas")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deployed without deploying")
    parser.add_argument("--tables", type=str, help="Comma-separated list of tables to deploy (e.g., users,permissions)")
    parser.add_argument("--skip-verify", action="store_true", help="Skip post-deployment verification")
    args = parser.parse_args()

    # Parse table filter if provided
    table_filter = None
    if args.tables:
        table_filter = [t.strip() for t in args.tables.split(",")]
        log_info(f"Deploying only tables: {', '.join(table_filter)}")

    # Initialize BigQuery client
    log_header("Initializing BigQuery Client")
    try:
        client = bigquery.Client(project=PROJECT_ID)
        log_success(f"Connected to project {PROJECT_ID}")
    except Exception as e:
        log_error(f"Failed to initialize BigQuery client: {str(e)}")
        sys.exit(1)

    # Step 1: Create datasets
    log_header("Step 1: Creating Datasets")
    dataset_results = {}
    for dataset_id, description in DATASETS.items():
        if not args.dry_run:
            dataset_results[dataset_id] = create_dataset_if_not_exists(client, dataset_id, description)
        else:
            log_info(f"[DRY RUN] Would ensure dataset {dataset_id} exists")

    # Give BigQuery a moment to propagate dataset creation
    if not args.dry_run and any(dataset_results.values()):
        log_info("Waiting for dataset propagation...")
        time.sleep(2)

    # Step 2: Deploy tables
    log_header("Step 2: Deploying Table Schemas")

    # Get schema directory
    script_dir = Path(__file__).parent
    schema_dir = script_dir / "schemas"

    if not schema_dir.exists():
        log_error(f"Schema directory not found: {schema_dir}")
        sys.exit(1)

    deployment_results = {}
    for (dataset_id, table_name), schema_filename in SCHEMA_FILES.items():
        # Apply table filter if specified
        if table_filter and table_name not in table_filter:
            log_info(f"Skipping {table_name} (not in filter)")
            continue

        schema_file = schema_dir / schema_filename

        if not schema_file.exists():
            log_error(f"Schema file not found: {schema_file}")
            deployment_results[(dataset_id, table_name)] = False
            continue

        deployment_results[(dataset_id, table_name)] = deploy_table(
            client, dataset_id, table_name, schema_file, dry_run=args.dry_run
        )

    # Give BigQuery a moment to propagate table creation
    if not args.dry_run:
        log_info("Waiting for table propagation...")
        time.sleep(2)

    # Step 3: Verify deployments
    if not args.dry_run and not args.skip_verify:
        log_header("Step 3: Verifying Deployments")
        verification_results = {}
        for (dataset_id, table_name), deployed in deployment_results.items():
            if deployed:
                verification_results[(dataset_id, table_name)] = verify_deployment(
                    client, dataset_id, table_name
                )

    # Summary
    log_header("Deployment Summary")

    total_tables = len(deployment_results)
    successful = sum(1 for success in deployment_results.values() if success)
    failed = total_tables - successful

    print(f"Total tables: {total_tables}")
    print(f"{bcolors.OKGREEN}Successful: {successful}{bcolors.ENDC}")
    if failed > 0:
        print(f"{bcolors.FAIL}Failed: {failed}{bcolors.ENDC}")

    if args.dry_run:
        log_warning("DRY RUN MODE - No changes were made")

    # Exit with error code if any deployments failed
    if failed > 0:
        sys.exit(1)
    else:
        log_success("All schemas deployed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()

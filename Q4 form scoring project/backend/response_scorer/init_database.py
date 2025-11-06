"""
Initialize BigQuery tables for Response Scorer.

This script creates the necessary tables in the scoring dataset:
- responses: Stores form response metadata and scores
- response_answers: Stores individual answer details

Run this script once before deploying the Response Scorer API.

Usage:
    python3 init_database.py
"""

from google.cloud import bigquery

PROJECT_ID = "opex-data-lake-k23k4y98m"
DATASET_ID = "scoring"

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID)


def create_dataset():
    """Create the scoring dataset if it doesn't exist."""
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"

    try:
        client.get_dataset(dataset_id)
        print(f"✓ Dataset {dataset_id} already exists")
    except Exception:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        dataset.description = "Response scoring and analytics data"

        dataset = client.create_dataset(dataset, timeout=30)
        print(f"✓ Created dataset {dataset_id}")


def create_responses_table():
    """Create the responses table."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.responses"

    schema = [
        bigquery.SchemaField("response_id", "STRING", mode="REQUIRED",
                             description="Unique response identifier (UUID)"),
        bigquery.SchemaField("template_id", "STRING", mode="REQUIRED",
                             description="Template ID used for this response"),
        bigquery.SchemaField("template_name", "STRING", mode="REQUIRED",
                             description="Template name"),
        bigquery.SchemaField("opportunity_type", "STRING", mode="REQUIRED",
                             description="Opportunity type (e.g., Security, Network)"),
        bigquery.SchemaField("opportunity_subtype", "STRING", mode="REQUIRED",
                             description="Opportunity subtype (e.g., SASE, SD-WAN)"),
        bigquery.SchemaField("submitter_email", "STRING", mode="NULLABLE",
                             description="Email of person who submitted response"),
        bigquery.SchemaField("submitter_name", "STRING", mode="NULLABLE",
                             description="Name of person who submitted response"),
        bigquery.SchemaField("total_score", "FLOAT", mode="REQUIRED",
                             description="Total points earned"),
        bigquery.SchemaField("max_possible_score", "FLOAT", mode="REQUIRED",
                             description="Maximum possible points"),
        bigquery.SchemaField("score_percentage", "FLOAT", mode="REQUIRED",
                             description="Score as percentage (0-100)"),
        bigquery.SchemaField("total_questions", "INTEGER", mode="REQUIRED",
                             description="Total number of questions in template"),
        bigquery.SchemaField("answered_questions", "INTEGER", mode="REQUIRED",
                             description="Number of questions answered"),
        bigquery.SchemaField("completion_percentage", "FLOAT", mode="REQUIRED",
                             description="Completion percentage (0-100)"),
        bigquery.SchemaField("submitted_at", "TIMESTAMP", mode="REQUIRED",
                             description="When response was submitted"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED",
                             description="When record was created"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    table.description = "Form responses with scoring information"

    try:
        client.get_table(table_id)
        print(f"✓ Table {table_id} already exists")
    except Exception:
        table = client.create_table(table, timeout=30)
        print(f"✓ Created table {table_id}")


def create_response_answers_table():
    """Create the response_answers table."""
    table_id = f"{PROJECT_ID}.{DATASET_ID}.response_answers"

    schema = [
        bigquery.SchemaField("answer_id", "STRING", mode="REQUIRED",
                             description="Unique answer identifier (UUID)"),
        bigquery.SchemaField("response_id", "STRING", mode="REQUIRED",
                             description="Response this answer belongs to"),
        bigquery.SchemaField("question_id", "STRING", mode="REQUIRED",
                             description="Question identifier"),
        bigquery.SchemaField("question_text", "STRING", mode="REQUIRED",
                             description="Full question text"),
        bigquery.SchemaField("answer_value", "STRING", mode="NULLABLE",
                             description="Answer provided by submitter"),
        bigquery.SchemaField("points_earned", "FLOAT", mode="REQUIRED",
                             description="Points earned for this answer"),
        bigquery.SchemaField("points_possible", "FLOAT", mode="REQUIRED",
                             description="Maximum points possible for this question"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED",
                             description="When record was created"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    table.description = "Individual answers for each response"

    try:
        client.get_table(table_id)
        print(f"✓ Table {table_id} already exists")
    except Exception:
        table = client.create_table(table, timeout=30)
        print(f"✓ Created table {table_id}")


def main():
    """Initialize all database tables."""
    print("Initializing Response Scorer database...")
    print()

    create_dataset()
    create_responses_table()
    create_response_answers_table()

    print()
    print("✅ Database initialization complete!")
    print()
    print("Next steps:")
    print("1. Deploy the Response Scorer API to Google Cloud Functions")
    print("2. Test the /responses/submit endpoint")
    print("3. Verify data in BigQuery")


if __name__ == "__main__":
    main()

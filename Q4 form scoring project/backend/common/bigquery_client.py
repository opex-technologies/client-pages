"""
BigQuery client management for backend services
Provides connection pooling and common query operations
Created: November 5, 2025
"""

from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.api_core import exceptions
from .config import config
from .logger import get_logger

logger = get_logger('bigquery_client')

# Global BigQuery client (reused across invocations in Cloud Functions)
_client: Optional[bigquery.Client] = None


def get_bigquery_client() -> bigquery.Client:
    """
    Get or create BigQuery client instance

    Returns:
        bigquery.Client: Initialized BigQuery client

    Usage:
        client = get_bigquery_client()
        query = "SELECT * FROM table"
        results = client.query(query).result()
    """
    global _client

    if _client is None:
        logger.info('Initializing BigQuery client', project_id=config.PROJECT_ID)
        _client = bigquery.Client(project=config.PROJECT_ID)
        logger.info('BigQuery client initialized successfully')

    return _client


def execute_query(
    query: str,
    params: Optional[List[bigquery.ScalarQueryParameter]] = None,
    timeout: int = 30
) -> List[Dict[str, Any]]:
    """
    Execute a BigQuery SQL query and return results as list of dictionaries

    Args:
        query: SQL query to execute
        params: Optional query parameters for parameterized queries
        timeout: Query timeout in seconds (default: 30)

    Returns:
        List[Dict[str, Any]]: Query results as list of dictionaries

    Raises:
        exceptions.GoogleAPIError: If query fails

    Usage:
        results = execute_query(
            "SELECT * FROM `project.dataset.table` WHERE user_id = @user_id",
            params=[bigquery.ScalarQueryParameter("user_id", "STRING", "123")]
        )
    """
    client = get_bigquery_client()

    logger.debug('Executing BigQuery query', query=query[:100])

    try:
        # Configure query job
        job_config = bigquery.QueryJobConfig()
        if params:
            job_config.query_parameters = params

        # Execute query
        query_job = client.query(query, job_config=job_config, timeout=timeout)
        results = query_job.result()

        # Convert to list of dictionaries
        rows = [dict(row) for row in results]

        logger.debug('Query executed successfully', row_count=len(rows))
        return rows

    except exceptions.GoogleAPIError as e:
        logger.error('BigQuery query failed', error=str(e), query=query[:100])
        raise


def execute_query_single(
    query: str,
    params: Optional[List[bigquery.ScalarQueryParameter]] = None,
    timeout: int = 30
) -> Optional[Dict[str, Any]]:
    """
    Execute query and return single row result

    Args:
        query: SQL query to execute
        params: Optional query parameters
        timeout: Query timeout in seconds

    Returns:
        Optional[Dict[str, Any]]: First row as dictionary, or None if no results

    Usage:
        user = execute_query_single(
            "SELECT * FROM `project.dataset.users` WHERE user_id = @user_id LIMIT 1",
            params=[bigquery.ScalarQueryParameter("user_id", "STRING", "123")]
        )
    """
    results = execute_query(query, params, timeout)
    return results[0] if results else None


def insert_rows(
    table_ref: str,
    rows: List[Dict[str, Any]],
    batch_size: int = 100
) -> bool:
    """
    Insert rows into BigQuery table in batches

    Args:
        table_ref: Fully qualified table reference (project.dataset.table)
        rows: List of dictionaries representing rows to insert
        batch_size: Number of rows per batch (default: 100)

    Returns:
        bool: True if all inserts successful

    Raises:
        exceptions.GoogleAPIError: If insert fails

    Usage:
        rows = [
            {'user_id': '123', 'email': 'user@example.com'},
            {'user_id': '456', 'email': 'user2@example.com'}
        ]
        insert_rows('opex-data-lake-k23k4y98m.auth.users', rows)
    """
    client = get_bigquery_client()

    logger.info('Inserting rows to BigQuery', table=table_ref, row_count=len(rows))

    try:
        total_inserted = 0

        # Insert in batches
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]

            errors = client.insert_rows_json(table_ref, batch)

            if errors:
                logger.error('Insert batch failed', errors=errors, batch_number=i // batch_size + 1)
                raise exceptions.GoogleAPIError(f"Insert errors: {errors}")

            total_inserted += len(batch)
            logger.debug('Batch inserted', batch_number=i // batch_size + 1, rows_inserted=len(batch))

        logger.info('All rows inserted successfully', total_rows=total_inserted)
        return True

    except exceptions.GoogleAPIError as e:
        logger.error('BigQuery insert failed', error=str(e), table=table_ref)
        raise


def table_exists(dataset_id: str, table_id: str) -> bool:
    """
    Check if a BigQuery table exists

    Args:
        dataset_id: Dataset ID
        table_id: Table ID

    Returns:
        bool: True if table exists, False otherwise

    Usage:
        if table_exists('auth', 'users'):
            print('Users table exists')
    """
    client = get_bigquery_client()
    table_ref = f"{config.PROJECT_ID}.{dataset_id}.{table_id}"

    try:
        client.get_table(table_ref)
        return True
    except exceptions.NotFound:
        return False


def get_table_schema(dataset_id: str, table_id: str) -> Optional[List[bigquery.SchemaField]]:
    """
    Get schema for a BigQuery table

    Args:
        dataset_id: Dataset ID
        table_id: Table ID

    Returns:
        Optional[List[bigquery.SchemaField]]: Table schema, or None if table doesn't exist

    Usage:
        schema = get_table_schema('auth', 'users')
        for field in schema:
            print(f'{field.name}: {field.field_type}')
    """
    client = get_bigquery_client()
    table_ref = f"{config.PROJECT_ID}.{dataset_id}.{table_id}"

    try:
        table = client.get_table(table_ref)
        return table.schema
    except exceptions.NotFound:
        logger.warning('Table not found', dataset=dataset_id, table=table_id)
        return None


def count_rows(dataset_id: str, table_id: str, where_clause: str = "") -> int:
    """
    Count rows in a BigQuery table

    Args:
        dataset_id: Dataset ID
        table_id: Table ID
        where_clause: Optional WHERE clause (without 'WHERE' keyword)

    Returns:
        int: Row count

    Usage:
        total_users = count_rows('auth', 'users')
        active_users = count_rows('auth', 'users', "status = 'active'")
    """
    table_ref = f"{config.PROJECT_ID}.{dataset_id}.{table_id}"
    where_sql = f"WHERE {where_clause}" if where_clause else ""

    query = f"SELECT COUNT(*) as count FROM `{table_ref}` {where_sql}"
    result = execute_query_single(query)

    return result['count'] if result else 0


def delete_rows(dataset_id: str, table_id: str, where_clause: str) -> int:
    """
    Delete rows from BigQuery table

    Args:
        dataset_id: Dataset ID
        table_id: Table ID
        where_clause: WHERE clause (without 'WHERE' keyword)

    Returns:
        int: Number of rows deleted

    Usage:
        deleted = delete_rows('auth', 'sessions', "expires_at < CURRENT_TIMESTAMP()")
    """
    table_ref = f"{config.PROJECT_ID}.{dataset_id}.{table_id}"
    query = f"DELETE FROM `{table_ref}` WHERE {where_clause}"

    client = get_bigquery_client()

    logger.info('Deleting rows from BigQuery', table=table_ref, where=where_clause)

    try:
        query_job = client.query(query)
        result = query_job.result()

        rows_deleted = query_job.num_dml_affected_rows
        logger.info('Rows deleted successfully', rows_deleted=rows_deleted)

        return rows_deleted

    except exceptions.GoogleAPIError as e:
        logger.error('Delete operation failed', error=str(e), table=table_ref)
        raise

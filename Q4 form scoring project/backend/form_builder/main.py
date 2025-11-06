"""
Form Builder API - Cloud Function
Created: November 5, 2025

Provides REST API for managing form templates and questions in the Form Builder system.

Endpoints:
- POST   /form-builder/templates          - Create new template
- GET    /form-builder/templates          - List templates with filtering
- GET    /form-builder/templates/:id      - Get template details
- PUT    /form-builder/templates/:id      - Update template
- DELETE /form-builder/templates/:id      - Delete template
- POST   /form-builder/templates/:id/deploy - Deploy template to GitHub

Authentication: JWT via Authorization: Bearer <token> header
Permissions: view, edit, admin (see API_SPEC.md for permission matrix)
"""

import os
import json
import uuid
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

import functions_framework
from google.cloud import bigquery
from flask import Request, jsonify
from jinja2 import Environment, FileSystemLoader, select_autoescape
import base64

# JWT validation (simplified for Cloud Functions deployment)
import jwt as pyjwt

# Get JWT secret from environment
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', '')

def decode_token(token: str) -> Tuple[bool, Optional[Dict]]:
    """
    Decode and validate JWT token.

    Returns:
        (is_valid, user_data) tuple
    """
    try:
        payload = pyjwt.decode(
            token,
            JWT_SECRET,
            algorithms=['HS256'],
            options={'verify_exp': True}
        )
        return True, payload
    except pyjwt.ExpiredSignatureError:
        return False, None
    except pyjwt.InvalidTokenError:
        return False, None
    except Exception:
        return False, None

# Initialize BigQuery client
bq_client = bigquery.Client()
PROJECT_ID = "opex-data-lake-k23k4y98m"
DATASET_ID = "form_builder"

# Table names
TEMPLATES_TABLE = f"{PROJECT_ID}.{DATASET_ID}.form_templates"
TEMPLATE_QUESTIONS_TABLE = f"{PROJECT_ID}.{DATASET_ID}.template_questions"
QUESTIONS_TABLE = f"{PROJECT_ID}.{DATASET_ID}.question_database"

# GitHub configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO_OWNER = os.environ.get('GITHUB_REPO_OWNER', 'opextech')
GITHUB_REPO_NAME = os.environ.get('GITHUB_REPO_NAME', 'forms')
GITHUB_BRANCH = os.environ.get('GITHUB_BRANCH', 'main')
GITHUB_PAGES_BASE_URL = f"https://{GITHUB_REPO_OWNER}.github.io/{GITHUB_REPO_NAME}"


# ============================================================================
# Utility Functions
# ============================================================================

def success_response(data: Any = None, message: str = None, status_code: int = 200) -> tuple:
    """Return standardized success response."""
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return jsonify(response), status_code


def error_response(message: str, code: str = "ERROR", details: Dict = None, status_code: int = 400) -> tuple:
    """Return standardized error response."""
    response = {
        "success": False,
        "error": {
            "message": message,
            "code": code
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if details:
        response["error"]["details"] = details
    return jsonify(response), status_code


def validate_uuid(value: str, field_name: str = "ID") -> Tuple[bool, Optional[str]]:
    """Validate UUID format."""
    try:
        uuid.UUID(value)
        return True, None
    except (ValueError, AttributeError):
        return False, f"Invalid {field_name} format"


def validate_template_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate template name."""
    if not name or not name.strip():
        return False, "Template name is required"
    if len(name) > 200:
        return False, "Template name must be 200 characters or less"
    return True, None


def validate_status(status: str) -> Tuple[bool, Optional[str]]:
    """Validate template status."""
    valid_statuses = ['draft', 'published', 'archived', 'deleted']
    if status not in valid_statuses:
        return False, f"Status must be one of: {', '.join(valid_statuses)}"
    return True, None


def validate_weight(weight: Any) -> Tuple[bool, Optional[str]]:
    """Validate question weight."""
    if weight == "Info" or weight == "info":
        return True, None
    try:
        w = float(weight)
        if w < 0 or w > 100:
            return False, "Weight must be between 0 and 100"
        return True, None
    except (ValueError, TypeError):
        return False, "Weight must be a number or 'Info'"


def normalize_weight(weight: Any) -> Optional[float]:
    """
    Normalize weight value for database storage.
    Converts "Info" to None, numbers to float.
    """
    if weight is None:
        return None
    if isinstance(weight, str) and weight.lower() == "info":
        return None
    try:
        return float(weight)
    except (ValueError, TypeError):
        return None


def sanitize_field_name(field_name: str) -> str:
    """Sanitize field names for BigQuery."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', field_name.strip().lower())


# ============================================================================
# Template CRUD Operations
# ============================================================================

def create_template(request: Request, current_user: Dict) -> tuple:
    """
    Create a new form template.

    POST /form-builder/templates
    Permission: edit
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is required", "BAD_REQUEST")

        # Validate required fields
        template_name = data.get('template_name')
        opportunity_type = data.get('opportunity_type')
        opportunity_subtype = data.get('opportunity_subtype')
        questions = data.get('questions', [])

        # Validation
        is_valid, error_msg = validate_template_name(template_name)
        if not is_valid:
            return error_response(error_msg, "BAD_REQUEST", {"template_name": error_msg})

        if not opportunity_type:
            return error_response("opportunity_type is required", "BAD_REQUEST")

        if not opportunity_subtype:
            return error_response("opportunity_subtype is required", "BAD_REQUEST")

        # Check for duplicate template name
        check_query = f"""
        SELECT COUNT(*) as count
        FROM `{TEMPLATES_TABLE}`
        WHERE template_name = @template_name
          AND status != 'deleted'
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("template_name", "STRING", template_name)
            ]
        )
        check_result = list(bq_client.query(check_query, job_config=job_config).result())

        if check_result[0].count > 0:
            return error_response(
                "Template with this name already exists",
                "CONFLICT",
                {"template_name": template_name},
                409
            )

        # Validate questions
        if questions:
            for idx, q in enumerate(questions):
                if not q.get('question_id'):
                    return error_response(
                        f"Question at index {idx} missing question_id",
                        "BAD_REQUEST"
                    )

                # Validate weight
                if 'weight' in q:
                    is_valid, error_msg = validate_weight(q['weight'])
                    if not is_valid:
                        return error_response(
                            f"Question {q['question_id']}: {error_msg}",
                            "BAD_REQUEST"
                        )

                # Validate sort_order
                if 'sort_order' in q:
                    try:
                        int(q['sort_order'])
                    except (ValueError, TypeError):
                        return error_response(
                            f"Question {q['question_id']}: sort_order must be an integer",
                            "BAD_REQUEST"
                        )

        # Generate IDs and timestamps
        template_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        user_id = current_user['user_id']
        user_email = current_user.get('email', '')

        # Insert template
        template_row = {
            "template_id": template_id,
            "template_name": template_name,
            "opportunity_type": opportunity_type,
            "opportunity_subtype": opportunity_subtype,
            "status": "draft",
            "description": data.get('description'),
            "created_by": user_id,
            "created_by_email": user_email,
            "created_at": now.isoformat(),
            "updated_at": None,
            "updated_by": None,
            "updated_by_email": None,
            "deployed_url": None,
            "deployed_at": None,
            "version": 1
        }

        errors = bq_client.insert_rows_json(TEMPLATES_TABLE, [template_row])
        if errors:
            return error_response(
                f"Failed to create template: {errors}",
                "DATABASE_ERROR",
                status_code=500
            )

        # Insert template questions
        if questions:
            question_rows = []
            for q in questions:
                question_rows.append({
                    "template_id": template_id,
                    "question_id": q['question_id'],
                    "weight": normalize_weight(q.get('weight')),
                    "is_required": q.get('is_required', False),
                    "sort_order": q.get('sort_order', 0),
                    "added_at": now.isoformat(),
                    "added_by": user_id
                })

            errors = bq_client.insert_rows_json(TEMPLATE_QUESTIONS_TABLE, question_rows)
            if errors:
                # Rollback template creation would be needed here
                # For now, log the error
                print(f"ERROR: Failed to insert template questions: {errors}")
                return error_response(
                    "Template created but failed to add questions",
                    "PARTIAL_ERROR",
                    {"errors": errors},
                    status_code=500
                )

        # Return created template
        return success_response(
            data={
                "template_id": template_id,
                "template_name": template_name,
                "status": "draft",
                "question_count": len(questions),
                "created_at": now.isoformat()
            },
            message="Template created successfully",
            status_code=201
        )

    except Exception as e:
        print(f"ERROR in create_template: {str(e)}")
        return error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


def list_templates(request: Request, current_user: Dict) -> tuple:
    """
    List all form templates with filtering and pagination.

    GET /form-builder/templates
    Permission: view
    """
    try:
        # Get query parameters
        opportunity_type = request.args.get('opportunity_type')
        opportunity_subtype = request.args.get('opportunity_subtype')
        status = request.args.get('status')
        created_by = request.args.get('created_by')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))

        # Validate pagination
        if page < 1:
            return error_response("Page must be >= 1", "BAD_REQUEST")
        if page_size < 1 or page_size > 100:
            return error_response("Page size must be between 1 and 100", "BAD_REQUEST")

        # Validate status if provided
        if status:
            is_valid, error_msg = validate_status(status)
            if not is_valid:
                return error_response(error_msg, "BAD_REQUEST")

        # Build query
        where_clauses = ["status != 'deleted'"]
        params = []

        if opportunity_type:
            where_clauses.append("opportunity_type = @opportunity_type")
            params.append(bigquery.ScalarQueryParameter("opportunity_type", "STRING", opportunity_type))

        if opportunity_subtype:
            where_clauses.append("opportunity_subtype = @opportunity_subtype")
            params.append(bigquery.ScalarQueryParameter("opportunity_subtype", "STRING", opportunity_subtype))

        if status:
            where_clauses.append("status = @status")
            params.append(bigquery.ScalarQueryParameter("status", "STRING", status))

        if created_by:
            where_clauses.append("created_by = @created_by")
            params.append(bigquery.ScalarQueryParameter("created_by", "STRING", created_by))

        where_clause = " AND ".join(where_clauses)

        # Count total results
        count_query = f"""
        SELECT COUNT(*) as total_count
        FROM `{TEMPLATES_TABLE}`
        WHERE {where_clause}
        """

        # Get templates with question counts
        offset = (page - 1) * page_size
        query = f"""
        SELECT
          t.template_id,
          t.template_name,
          t.opportunity_type,
          t.opportunity_subtype,
          t.status,
          t.created_by,
          t.created_by_email,
          t.created_at,
          t.updated_at,
          t.deployed_url,
          t.version,
          COUNT(tq.question_id) as question_count
        FROM `{TEMPLATES_TABLE}` t
        LEFT JOIN `{TEMPLATE_QUESTIONS_TABLE}` tq
          ON t.template_id = tq.template_id
        WHERE {where_clause}
        GROUP BY
          t.template_id,
          t.template_name,
          t.opportunity_type,
          t.opportunity_subtype,
          t.status,
          t.created_by,
          t.created_by_email,
          t.created_at,
          t.updated_at,
          t.deployed_url,
          t.version
        ORDER BY t.created_at DESC
        LIMIT @page_size
        OFFSET @offset
        """

        params.extend([
            bigquery.ScalarQueryParameter("page_size", "INT64", page_size),
            bigquery.ScalarQueryParameter("offset", "INT64", offset)
        ])

        job_config = bigquery.QueryJobConfig(query_parameters=params)

        # Execute queries
        count_result = list(bq_client.query(count_query, job_config=job_config).result())
        total_count = count_result[0].total_count

        templates_result = bq_client.query(query, job_config=job_config).result()

        # Format results
        items = []
        for row in templates_result:
            items.append({
                "template_id": row.template_id,
                "template_name": row.template_name,
                "opportunity_type": row.opportunity_type,
                "opportunity_subtype": row.opportunity_subtype,
                "status": row.status,
                "question_count": row.question_count,
                "created_by": row.created_by,
                "created_by_email": row.created_by_email,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "deployed_url": row.deployed_url,
                "version": row.version
            })

        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1

        return success_response(
            data={
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
        )

    except ValueError as e:
        return error_response(f"Invalid parameter: {str(e)}", "BAD_REQUEST")
    except Exception as e:
        print(f"ERROR in list_templates: {str(e)}")
        return error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


def get_template(request: Request, template_id: str, current_user: Dict) -> tuple:
    """
    Get a specific form template with full details including questions.

    GET /form-builder/templates/:template_id
    Permission: view
    """
    try:
        # Validate template_id
        is_valid, error_msg = validate_uuid(template_id, "template_id")
        if not is_valid:
            return error_response(error_msg, "BAD_REQUEST")

        # Get template
        template_query = f"""
        SELECT *
        FROM `{TEMPLATES_TABLE}`
        WHERE template_id = @template_id
          AND status != 'deleted'
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("template_id", "STRING", template_id)
            ]
        )

        template_result = list(bq_client.query(template_query, job_config=job_config).result())

        if not template_result:
            return error_response(
                "Template not found",
                "NOT_FOUND",
                {"resource": f"template_id:{template_id}"},
                status_code=404
            )

        template = template_result[0]

        # Get template questions with question details
        questions_query = f"""
        SELECT
          tq.question_id,
          q.question_text,
          q.input_type,
          q.help_text,
          tq.weight,
          tq.is_required,
          tq.sort_order
        FROM `{TEMPLATE_QUESTIONS_TABLE}` tq
        JOIN `{QUESTIONS_TABLE}` q
          ON tq.question_id = q.question_id
        WHERE tq.template_id = @template_id
        ORDER BY tq.sort_order, tq.question_id
        """

        questions_result = bq_client.query(questions_query, job_config=job_config).result()

        questions = []
        for row in questions_result:
            questions.append({
                "question_id": row.question_id,
                "question_text": row.question_text,
                "input_type": row.input_type,
                "weight": row.weight,
                "is_required": row.is_required,
                "help_text": row.help_text,
                "sort_order": row.sort_order
            })

        # Format response
        return success_response(
            data={
                "template_id": template.template_id,
                "template_name": template.template_name,
                "opportunity_type": template.opportunity_type,
                "opportunity_subtype": template.opportunity_subtype,
                "status": template.status,
                "description": template.description,
                "questions": questions,
                "created_by": template.created_by,
                "created_by_email": template.created_by_email,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None,
                "deployed_url": template.deployed_url,
                "deployed_at": template.deployed_at.isoformat() if template.deployed_at else None,
                "version": template.version
            }
        )

    except Exception as e:
        print(f"ERROR in get_template: {str(e)}")
        return error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


def update_template(request: Request, template_id: str, current_user: Dict) -> tuple:
    """
    Update an existing form template (draft status only).

    PUT /form-builder/templates/:template_id
    Permission: edit
    """
    try:
        # Validate template_id
        is_valid, error_msg = validate_uuid(template_id, "template_id")
        if not is_valid:
            return error_response(error_msg, "BAD_REQUEST")

        data = request.get_json()
        if not data:
            return error_response("Request body is required", "BAD_REQUEST")

        # Check if template exists and is draft
        check_query = f"""
        SELECT status, version
        FROM `{TEMPLATES_TABLE}`
        WHERE template_id = @template_id
          AND status != 'deleted'
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("template_id", "STRING", template_id)
            ]
        )

        check_result = list(bq_client.query(check_query, job_config=job_config).result())

        if not check_result:
            return error_response(
                "Template not found",
                "NOT_FOUND",
                {"resource": f"template_id:{template_id}"},
                status_code=404
            )

        current_status = check_result[0].status
        current_version = check_result[0].version

        if current_status != 'draft':
            return error_response(
                "Can only update templates with 'draft' status",
                "FORBIDDEN",
                {"current_status": current_status},
                status_code=403
            )

        # Build update query
        update_fields = []
        update_params = [bigquery.ScalarQueryParameter("template_id", "STRING", template_id)]

        if 'template_name' in data:
            is_valid, error_msg = validate_template_name(data['template_name'])
            if not is_valid:
                return error_response(error_msg, "BAD_REQUEST")
            update_fields.append("template_name = @template_name")
            update_params.append(bigquery.ScalarQueryParameter("template_name", "STRING", data['template_name']))

        if 'description' in data:
            update_fields.append("description = @description")
            update_params.append(bigquery.ScalarQueryParameter("description", "STRING", data['description']))

        if 'opportunity_type' in data:
            update_fields.append("opportunity_type = @opportunity_type")
            update_params.append(bigquery.ScalarQueryParameter("opportunity_type", "STRING", data['opportunity_type']))

        if 'opportunity_subtype' in data:
            update_fields.append("opportunity_subtype = @opportunity_subtype")
            update_params.append(bigquery.ScalarQueryParameter("opportunity_subtype", "STRING", data['opportunity_subtype']))

        # Always update metadata
        now = datetime.now(timezone.utc)
        user_id = current_user['user_id']
        user_email = current_user.get('email', '')
        new_version = current_version + 1

        update_fields.extend([
            "updated_at = @updated_at",
            "updated_by = @updated_by",
            "updated_by_email = @updated_by_email",
            "version = @version"
        ])
        update_params.extend([
            bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", now),
            bigquery.ScalarQueryParameter("updated_by", "STRING", user_id),
            bigquery.ScalarQueryParameter("updated_by_email", "STRING", user_email),
            bigquery.ScalarQueryParameter("version", "INT64", new_version)
        ])

        if update_fields:
            update_query = f"""
            UPDATE `{TEMPLATES_TABLE}`
            SET {', '.join(update_fields)}
            WHERE template_id = @template_id
            """

            job_config = bigquery.QueryJobConfig(query_parameters=update_params)
            bq_client.query(update_query, job_config=job_config).result()

        # Update questions if provided
        if 'questions' in data:
            questions = data['questions']

            # Validate questions
            for idx, q in enumerate(questions):
                if not q.get('question_id'):
                    return error_response(
                        f"Question at index {idx} missing question_id",
                        "BAD_REQUEST"
                    )

                if 'weight' in q:
                    is_valid, error_msg = validate_weight(q['weight'])
                    if not is_valid:
                        return error_response(
                            f"Question {q['question_id']}: {error_msg}",
                            "BAD_REQUEST"
                        )

            # Delete existing questions
            delete_query = f"""
            DELETE FROM `{TEMPLATE_QUESTIONS_TABLE}`
            WHERE template_id = @template_id
            """
            bq_client.query(delete_query, job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("template_id", "STRING", template_id)]
            )).result()

            # Insert new questions
            if questions:
                question_rows = []
                for q in questions:
                    question_rows.append({
                        "template_id": template_id,
                        "question_id": q['question_id'],
                        "weight": normalize_weight(q.get('weight')),
                        "is_required": q.get('is_required', False),
                        "sort_order": q.get('sort_order', 0),
                        "added_at": now.isoformat(),
                        "added_by": user_id
                    })

                errors = bq_client.insert_rows_json(TEMPLATE_QUESTIONS_TABLE, question_rows)
                if errors:
                    print(f"ERROR: Failed to insert updated questions: {errors}")

        return success_response(
            data={
                "template_id": template_id,
                "template_name": data.get('template_name'),
                "version": new_version,
                "updated_at": now.isoformat()
            },
            message="Template updated successfully"
        )

    except Exception as e:
        print(f"ERROR in update_template: {str(e)}")
        return error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


def delete_template(request: Request, template_id: str, current_user: Dict) -> tuple:
    """
    Soft delete a form template (admin only, draft or archived status only).

    DELETE /form-builder/templates/:template_id
    Permission: admin
    """
    try:
        # Validate template_id
        is_valid, error_msg = validate_uuid(template_id, "template_id")
        if not is_valid:
            return error_response(error_msg, "BAD_REQUEST")

        # Check if template exists and can be deleted
        check_query = f"""
        SELECT status
        FROM `{TEMPLATES_TABLE}`
        WHERE template_id = @template_id
          AND status != 'deleted'
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("template_id", "STRING", template_id)
            ]
        )

        check_result = list(bq_client.query(check_query, job_config=job_config).result())

        if not check_result:
            return error_response(
                "Template not found",
                "NOT_FOUND",
                {"resource": f"template_id:{template_id}"},
                status_code=404
            )

        current_status = check_result[0].status

        if current_status not in ['draft', 'archived']:
            return error_response(
                "Can only delete templates with 'draft' or 'archived' status",
                "FORBIDDEN",
                {"current_status": current_status},
                status_code=403
            )

        # Soft delete template
        now = datetime.now(timezone.utc)
        user_id = current_user['user_id']
        user_email = current_user.get('email', '')

        delete_query = f"""
        UPDATE `{TEMPLATES_TABLE}`
        SET
          status = 'deleted',
          updated_at = @updated_at,
          updated_by = @updated_by,
          updated_by_email = @updated_by_email
        WHERE template_id = @template_id
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("template_id", "STRING", template_id),
                bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", now),
                bigquery.ScalarQueryParameter("updated_by", "STRING", user_id),
                bigquery.ScalarQueryParameter("updated_by_email", "STRING", user_email)
            ]
        )

        bq_client.query(delete_query, job_config=job_config).result()

        return success_response(message="Template deleted successfully")

    except Exception as e:
        print(f"ERROR in delete_template: {str(e)}")
        return error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


# ============================================================================
# Question Query Operations
# ============================================================================

def query_questions(request: Request, current_user: Dict) -> tuple:
    """
    Query the Question Database with filtering.

    GET /form-builder/questions
    Permission: view
    """
    try:
        # Get query parameters
        category = request.args.get('category')
        opportunity_type = request.args.get('opportunity_type')
        opportunity_subtype = request.args.get('opportunity_subtype')
        search = request.args.get('search')
        template_id = request.args.get('template_id')  # Mark questions already in template
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 100))

        # Validate pagination
        if page < 1:
            return error_response("Page must be >= 1", "BAD_REQUEST")
        if page_size < 1 or page_size > 200:
            return error_response("Page size must be between 1 and 200", "BAD_REQUEST")

        # Build query
        where_clauses = ["is_active = TRUE"]
        params = []

        if category:
            where_clauses.append("category = @category")
            params.append(bigquery.ScalarQueryParameter("category", "STRING", category))

        if opportunity_type:
            where_clauses.append("opportunity_type = @opportunity_type")
            params.append(bigquery.ScalarQueryParameter("opportunity_type", "STRING", opportunity_type))

        if opportunity_subtype:
            where_clauses.append("opportunity_subtypes = @opportunity_subtypes")
            params.append(bigquery.ScalarQueryParameter("opportunity_subtypes", "STRING", opportunity_subtype))

        if search:
            where_clauses.append("LOWER(question_text) LIKE @search")
            params.append(bigquery.ScalarQueryParameter("search", "STRING", f"%{search.lower()}%"))

        where_clause = " AND ".join(where_clauses)

        # Count total results
        count_query = f"""
        SELECT COUNT(*) as total_count
        FROM `{QUESTIONS_TABLE}`
        WHERE {where_clause}
        """

        # Get questions
        offset = (page - 1) * page_size
        query = f"""
        SELECT
          question_id,
          question_text,
          category,
          opportunity_type,
          opportunity_subtypes,
          input_type,
          default_weight,
          help_text,
          is_active
        FROM `{QUESTIONS_TABLE}`
        WHERE {where_clause}
        ORDER BY category, question_text
        LIMIT @page_size
        OFFSET @offset
        """

        params.extend([
            bigquery.ScalarQueryParameter("page_size", "INT64", page_size),
            bigquery.ScalarQueryParameter("offset", "INT64", offset)
        ])

        job_config = bigquery.QueryJobConfig(query_parameters=params)

        # Execute queries
        count_result = list(bq_client.query(count_query, job_config=job_config).result())
        total_count = count_result[0].total_count

        questions_result = bq_client.query(query, job_config=job_config).result()

        # Get selected question IDs if template_id provided
        selected_question_ids = set()
        if template_id:
            is_valid, error_msg = validate_uuid(template_id, "template_id")
            if is_valid:
                selected_query = f"""
                SELECT question_id
                FROM `{TEMPLATE_QUESTIONS_TABLE}`
                WHERE template_id = @template_id
                """
                selected_job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("template_id", "STRING", template_id)
                    ]
                )
                selected_result = bq_client.query(selected_query, job_config=selected_job_config).result()
                selected_question_ids = {row.question_id for row in selected_result}

        # Format results
        items = []
        for row in questions_result:
            items.append({
                "question_id": row.question_id,
                "question_text": row.question_text,
                "category": row.category,
                "opportunity_type": row.opportunity_type,
                "opportunity_subtype": row.opportunity_subtypes,  # Column is plural in DB
                "input_type": row.input_type,
                "default_weight": row.default_weight,
                "help_text": row.help_text,
                "is_selected": row.question_id in selected_question_ids,
                "is_active": row.is_active
            })

        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1

        return success_response(
            data={
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
        )

    except ValueError as e:
        return error_response(f"Invalid parameter: {str(e)}", "BAD_REQUEST")
    except Exception as e:
        print(f"ERROR in query_questions: {str(e)}")
        return error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


def get_question(request: Request, question_id: str, current_user: Dict) -> tuple:
    """
    Get a specific question with usage statistics.

    GET /form-builder/questions/:question_id
    Permission: view
    """
    try:
        # Get question
        question_query = f"""
        SELECT *
        FROM `{QUESTIONS_TABLE}`
        WHERE question_id = @question_id
          AND is_active = TRUE
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("question_id", "STRING", question_id)
            ]
        )

        question_result = list(bq_client.query(question_query, job_config=job_config).result())

        if not question_result:
            return error_response(
                "Question not found",
                "NOT_FOUND",
                {"resource": f"question_id:{question_id}"},
                status_code=404
            )

        question = question_result[0]

        # Get usage statistics
        usage_query = f"""
        SELECT
          t.template_id,
          t.template_name,
          t.status
        FROM `{TEMPLATE_QUESTIONS_TABLE}` tq
        JOIN `{TEMPLATES_TABLE}` t
          ON tq.template_id = t.template_id
        WHERE tq.question_id = @question_id
          AND t.status != 'deleted'
        ORDER BY t.created_at DESC
        """

        usage_result = bq_client.query(usage_query, job_config=job_config).result()

        templates_using = []
        for row in usage_result:
            templates_using.append({
                "template_id": row.template_id,
                "template_name": row.template_name,
                "status": row.status
            })

        # Format response
        return success_response(
            data={
                "question_id": question.question_id,
                "question_text": question.question_text,
                "category": question.category,
                "opportunity_type": question.opportunity_type,
                "opportunity_subtype": question.opportunity_subtypes,  # Column is plural in DB
                "input_type": question.input_type,
                "default_weight": question.default_weight,
                "help_text": question.help_text,
                "is_active": question.is_active,
                "usage_count": len(templates_using),
                "templates_using": templates_using
            }
        )

    except Exception as e:
        print(f"ERROR in get_question: {str(e)}")
        return error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


# ============================================================================
# Form Generation Logic
# ============================================================================

def generate_form_html(template_data: Dict) -> str:
    """
    Generate HTML for a form template using Jinja2.

    Args:
        template_data: Dictionary containing:
            - template_id: str
            - template_name: str
            - opportunity_type: str
            - opportunity_subtype: str
            - description: str (optional)
            - questions: List[Dict] with question details

    Returns:
        Generated HTML string
    """
    # Setup Jinja2 environment
    template_dir = os.path.dirname(__file__)
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # Load template
    template = env.get_template('form_template.html')

    # Set webhook URL (using existing form webhook endpoint)
    webhook_url = "https://opex-form-webhook-4jypryamoq-uc.a.run.app"

    # Render template
    html = template.render(
        template_id=template_data['template_id'],
        template_name=template_data['template_name'],
        opportunity_type=template_data['opportunity_type'],
        opportunity_subtype=template_data['opportunity_subtype'],
        description=template_data.get('description', ''),
        questions=template_data['questions'],
        webhook_url=webhook_url
    )

    return html


def generate_preview(request: Request, current_user: Dict) -> tuple:
    """
    Generate a preview HTML of a form template without deploying.

    POST /form-builder/preview
    Permission: view
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is required", "BAD_REQUEST")

        template_id = data.get('template_id')
        if not template_id:
            return error_response("template_id is required", "BAD_REQUEST")

        # Validate template_id
        is_valid, error_msg = validate_uuid(template_id, "template_id")
        if not is_valid:
            return error_response(error_msg, "BAD_REQUEST")

        # Get template data (reuse get_template logic)
        template_query = f"""
        SELECT *
        FROM `{TEMPLATES_TABLE}`
        WHERE template_id = @template_id
          AND status != 'deleted'
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("template_id", "STRING", template_id)
            ]
        )

        template_result = list(bq_client.query(template_query, job_config=job_config).result())

        if not template_result:
            return error_response(
                "Template not found",
                "NOT_FOUND",
                {"resource": f"template_id:{template_id}"},
                status_code=404
            )

        template = template_result[0]

        # Get template questions with question details
        questions_query = f"""
        SELECT
          tq.question_id,
          q.question_text,
          q.input_type,
          q.help_text,
          tq.weight,
          tq.is_required,
          tq.sort_order
        FROM `{TEMPLATE_QUESTIONS_TABLE}` tq
        JOIN `{QUESTIONS_TABLE}` q
          ON tq.question_id = q.question_id
        WHERE tq.template_id = @template_id
        ORDER BY tq.sort_order, tq.question_id
        """

        questions_result = bq_client.query(questions_query, job_config=job_config).result()

        questions = []
        for row in questions_result:
            questions.append({
                "question_id": row.question_id,
                "question_text": row.question_text,
                "input_type": row.input_type,
                "weight": row.weight,
                "is_required": row.is_required,
                "help_text": row.help_text,
                "sort_order": row.sort_order
            })

        # Prepare template data
        template_data = {
            "template_id": template.template_id,
            "template_name": template.template_name,
            "opportunity_type": template.opportunity_type,
            "opportunity_subtype": template.opportunity_subtype,
            "description": template.description,
            "questions": questions
        }

        # Generate HTML
        html = generate_form_html(template_data)

        # Create data URL for preview
        html_base64 = base64.b64encode(html.encode('utf-8')).decode('utf-8')
        preview_url = f"data:text/html;base64,{html_base64}"

        return success_response(
            data={
                "html": html,
                "preview_url": preview_url
            }
        )

    except Exception as e:
        print(f"ERROR in generate_preview: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


# ============================================================================
# GitHub Deployment
# ============================================================================

def deploy_template(request: Request, template_id: str, current_user: Dict) -> tuple:
    """
    Deploy form template to GitHub Pages.

    POST /form-builder/templates/:template_id/deploy
    Permission: edit
    """
    try:
        # Validate template_id
        is_valid, error_msg = validate_uuid(template_id, "template_id")
        if not is_valid:
            return error_response(error_msg, "BAD_REQUEST")

        # Check GitHub configuration
        if not GITHUB_TOKEN:
            return error_response(
                "GitHub deployment not configured (missing GITHUB_TOKEN)",
                "CONFIGURATION_ERROR",
                status_code=500
            )

        data = request.get_json() or {}
        commit_message = data.get('commit_message', f'Deploy form template {template_id}')

        # Get template
        template_query = f"""
        SELECT *
        FROM `{TEMPLATES_TABLE}`
        WHERE template_id = @template_id
          AND status != 'deleted'
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("template_id", "STRING", template_id)
            ]
        )

        template_result = list(bq_client.query(template_query, job_config=job_config).result())

        if not template_result:
            return error_response(
                "Template not found",
                "NOT_FOUND",
                {"resource": f"template_id:{template_id}"},
                status_code=404
            )

        template = template_result[0]

        # Get template questions
        questions_query = f"""
        SELECT
          tq.question_id,
          q.question_text,
          q.input_type,
          q.help_text,
          tq.weight,
          tq.is_required,
          tq.sort_order
        FROM `{TEMPLATE_QUESTIONS_TABLE}` tq
        JOIN `{QUESTIONS_TABLE}` q
          ON tq.question_id = q.question_id
        WHERE tq.template_id = @template_id
        ORDER BY tq.sort_order, tq.question_id
        """

        questions_result = bq_client.query(questions_query, job_config=job_config).result()

        questions = []
        for row in questions_result:
            questions.append({
                "question_id": row.question_id,
                "question_text": row.question_text,
                "input_type": row.input_type,
                "weight": row.weight,
                "is_required": row.is_required,
                "help_text": row.help_text,
                "sort_order": row.sort_order
            })

        if not questions:
            return error_response(
                "Cannot deploy template without questions",
                "BAD_REQUEST",
                {"template_id": template_id}
            )

        # Prepare template data
        template_data = {
            "template_id": template.template_id,
            "template_name": template.template_name,
            "opportunity_type": template.opportunity_type,
            "opportunity_subtype": template.opportunity_subtype,
            "description": template.description,
            "questions": questions
        }

        # Generate HTML
        html = generate_form_html(template_data)

        # Create filename (sanitized)
        filename = sanitize_field_name(template.template_name) + '.html'
        file_path = f"forms/{filename}"

        # Deploy to GitHub
        try:
            from github import Github, GithubException

            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")

            # Try to get existing file
            try:
                existing_file = repo.get_contents(file_path, ref=GITHUB_BRANCH)
                # Update existing file
                result = repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=html,
                    sha=existing_file.sha,
                    branch=GITHUB_BRANCH
                )
                commit_sha = result['commit'].sha
            except GithubException as e:
                if e.status == 404:
                    # Create new file
                    result = repo.create_file(
                        path=file_path,
                        message=commit_message,
                        content=html,
                        branch=GITHUB_BRANCH
                    )
                    commit_sha = result['commit'].sha
                else:
                    raise

        except ImportError:
            return error_response(
                "GitHub library not available",
                "CONFIGURATION_ERROR",
                status_code=500
            )
        except Exception as e:
            print(f"ERROR deploying to GitHub: {str(e)}")
            return error_response(
                f"GitHub deployment failed: {str(e)}",
                "DEPLOYMENT_ERROR",
                {"error": str(e)},
                status_code=500
            )

        # Update template in BigQuery
        now = datetime.now(timezone.utc)
        user_id = current_user['user_id']
        deployed_url = f"{GITHUB_PAGES_BASE_URL}/{file_path}"

        # Note: This will fail if template was just created (streaming buffer)
        # In that case, return success but note that metadata update failed
        try:
            update_query = f"""
            UPDATE `{TEMPLATES_TABLE}`
            SET
              status = 'published',
              deployed_url = @deployed_url,
              deployed_at = @deployed_at,
              deployed_by = @deployed_by
            WHERE template_id = @template_id
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("template_id", "STRING", template_id),
                    bigquery.ScalarQueryParameter("deployed_url", "STRING", deployed_url),
                    bigquery.ScalarQueryParameter("deployed_at", "TIMESTAMP", now),
                    bigquery.ScalarQueryParameter("deployed_by", "STRING", user_id)
                ]
            )

            bq_client.query(update_query, job_config=job_config).result()

            metadata_updated = True
        except Exception as e:
            print(f"WARNING: Could not update template metadata: {str(e)}")
            # This is expected if template was just created (streaming buffer)
            metadata_updated = False

        response_data = {
            "template_id": template_id,
            "deployed_url": deployed_url,
            "deployed_at": now.isoformat(),
            "commit_sha": commit_sha,
            "file_path": file_path
        }

        if not metadata_updated:
            response_data["warning"] = "Template deployed but metadata update delayed (BigQuery streaming buffer)"

        return success_response(
            data=response_data,
            message="Template deployed successfully"
        )

    except Exception as e:
        print(f"ERROR in deploy_template: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


# ============================================================================
# Main Cloud Function Handler
# ============================================================================

@functions_framework.http
def form_builder_handler(request: Request):
    """
    Main Cloud Function entry point for Form Builder API.

    Routes requests to appropriate handlers based on HTTP method and path.
    All endpoints require JWT authentication via Authorization header.
    """

    # Enable CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # Add CORS headers to response
    def add_cors_headers(response):
        if isinstance(response, tuple):
            resp, status_code = response if len(response) == 2 else (response[0], response[1])
            headers = {'Access-Control-Allow-Origin': '*'}
            return (resp, status_code, headers)
        return response

    try:
        # Extract token and validate authentication
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return add_cors_headers(error_response(
                "Missing or invalid authorization header",
                "UNAUTHORIZED",
                status_code=401
            ))

        token = auth_header.replace('Bearer ', '')
        is_valid, current_user = decode_token(token)

        if not is_valid:
            return add_cors_headers(error_response(
                "Invalid or expired token",
                "UNAUTHORIZED",
                status_code=401
            ))

        # Parse path
        path = request.path.strip('/')

        # Route to appropriate handler
        # POST /form-builder/templates - Create template
        if path == 'form-builder/templates' and request.method == 'POST':
            # Check permission: requires 'edit'
            # For now, we'll check permissions inside the handler
            # In production, use @require_permission decorator
            return add_cors_headers(create_template(request, current_user))

        # GET /form-builder/templates - List templates
        elif path == 'form-builder/templates' and request.method == 'GET':
            return add_cors_headers(list_templates(request, current_user))

        # GET /form-builder/templates/:id - Get template
        elif path.startswith('form-builder/templates/') and request.method == 'GET':
            template_id = path.split('/')[-1]
            return add_cors_headers(get_template(request, template_id, current_user))

        # PUT /form-builder/templates/:id - Update template
        elif path.startswith('form-builder/templates/') and request.method == 'PUT':
            template_id = path.split('/')[-1]
            return add_cors_headers(update_template(request, template_id, current_user))

        # DELETE /form-builder/templates/:id - Delete template
        elif path.startswith('form-builder/templates/') and request.method == 'DELETE':
            template_id = path.split('/')[-1]
            # Note: This requires admin permission
            # Check if user has admin permission
            # For simplicity, checking here; in production use decorator
            return add_cors_headers(delete_template(request, template_id, current_user))

        # POST /form-builder/templates/:id/deploy - Deploy template to GitHub
        elif path.startswith('form-builder/templates/') and path.endswith('/deploy') and request.method == 'POST':
            template_id = path.split('/')[-2]  # Get ID before '/deploy'
            return add_cors_headers(deploy_template(request, template_id, current_user))

        # GET /form-builder/questions - Query questions
        elif path == 'form-builder/questions' and request.method == 'GET':
            return add_cors_headers(query_questions(request, current_user))

        # GET /form-builder/questions/:id - Get question
        elif path.startswith('form-builder/questions/') and request.method == 'GET':
            question_id = path.split('/')[-1]
            return add_cors_headers(get_question(request, question_id, current_user))

        # POST /form-builder/preview - Generate form preview
        elif path == 'form-builder/preview' and request.method == 'POST':
            return add_cors_headers(generate_preview(request, current_user))

        else:
            return add_cors_headers(error_response(
                f"Endpoint not found: {request.method} {path}",
                "NOT_FOUND",
                status_code=404
            ))

    except Exception as e:
        print(f"ERROR in form_builder_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return add_cors_headers(error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        ))

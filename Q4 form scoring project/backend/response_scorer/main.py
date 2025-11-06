"""
Response Scorer API - Cloud Function
Created: November 6, 2025

Provides REST API for submitting form responses, scoring, and analytics.

Endpoints:
- POST   /responses/submit              - Submit form response (PUBLIC)
- GET    /responses                     - List responses with filtering
- GET    /responses/:id                 - Get response details
- DELETE /responses/:id                 - Delete response (admin only)
- GET    /analytics/summary             - Get overall analytics
- GET    /analytics/template/:id        - Get template analytics
- GET    /analytics/responses/export    - Export responses to CSV

Authentication: JWT via Authorization: Bearer <token> header (except /submit)
Permissions: view, edit, admin
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

import functions_framework
from google.cloud import bigquery
from flask import Request, jsonify

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
DATASET_ID = "scoring"
FORM_BUILDER_DATASET_ID = "form_builder"

# Table names
RESPONSES_TABLE = f"{PROJECT_ID}.{DATASET_ID}.responses"
RESPONSE_ANSWERS_TABLE = f"{PROJECT_ID}.{DATASET_ID}.response_answers"
TEMPLATES_TABLE = f"{PROJECT_ID}.{FORM_BUILDER_DATASET_ID}.form_templates"
TEMPLATE_QUESTIONS_TABLE = f"{PROJECT_ID}.{FORM_BUILDER_DATASET_ID}.template_questions"


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


def add_cors_headers(response):
    """Add CORS headers to response."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


def validate_auth(request: Request, required_permission: str = 'view') -> Tuple[bool, Optional[Dict], Optional[tuple]]:
    """
    Validate JWT token and check permissions.

    Returns:
        (is_valid, user_data, error_response) tuple
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False, None, error_response("Missing or invalid authorization header", "UNAUTHORIZED", status_code=401)

    token = auth_header.replace('Bearer ', '')
    is_valid, user_data = decode_token(token)

    if not is_valid:
        return False, None, error_response("Invalid or expired token", "UNAUTHORIZED", status_code=401)

    # Check permission level (simplified - in production, query permissions table)
    user_permission = user_data.get('permission', 'view')

    permission_hierarchy = {'view': 1, 'edit': 2, 'admin': 3}
    required_level = permission_hierarchy.get(required_permission, 1)
    user_level = permission_hierarchy.get(user_permission, 0)

    if user_level < required_level:
        return False, None, error_response(
            f"Insufficient permissions. Required: {required_permission}",
            "FORBIDDEN",
            status_code=403
        )

    return True, user_data, None


# ============================================================================
# Scoring Algorithm
# ============================================================================

def calculate_score(template_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Calculate score for a response based on template questions.

    Args:
        template_id: Template ID
        answers: Dictionary of question_id -> answer_value

    Returns:
        Dictionary with scoring details
    """
    # Get template questions with weights
    query = f"""
        SELECT
            tq.question_id,
            q.question_text,
            tq.weight,
            tq.is_required
        FROM `{TEMPLATE_QUESTIONS_TABLE}` tq
        JOIN `{PROJECT_ID}.{FORM_BUILDER_DATASET_ID}.question_database` q
            ON tq.question_id = q.question_id
        WHERE tq.template_id = @template_id
        ORDER BY tq.sort_order
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("template_id", "STRING", template_id)
        ]
    )

    questions = list(bq_client.query(query, job_config=job_config).result())

    if not questions:
        raise ValueError(f"Template {template_id} not found or has no questions")

    # Calculate scoring
    total_score = 0.0
    max_possible_score = 0.0
    total_questions = len(questions)
    answered_questions = 0
    answer_details = []

    for question in questions:
        question_id = question.question_id
        question_text = question.question_text
        weight = question.weight
        is_required = question.is_required

        # Get answer
        answer_value = answers.get(question_id, "").strip()

        # Check if answered
        is_answered = bool(answer_value)
        if is_answered:
            answered_questions += 1

        # Calculate points for this question
        points_possible = float(weight) if weight else 0.0
        points_earned = 0.0

        # Only score if question has a weight (not "Info" questions)
        if weight:
            max_possible_score += points_possible

            # Award points if answered
            if is_answered:
                points_earned = points_possible
                total_score += points_earned

        # Store answer detail
        answer_details.append({
            'question_id': question_id,
            'question_text': question_text,
            'answer_value': answer_value,
            'points_earned': points_earned,
            'points_possible': points_possible,
            'is_required': is_required,
            'is_answered': is_answered
        })

    # Calculate percentages
    score_percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
    completion_percentage = (answered_questions / total_questions * 100) if total_questions > 0 else 0

    return {
        'total_score': total_score,
        'max_possible_score': max_possible_score,
        'score_percentage': round(score_percentage, 2),
        'total_questions': total_questions,
        'answered_questions': answered_questions,
        'completion_percentage': round(completion_percentage, 2),
        'answer_details': answer_details
    }


# ============================================================================
# Endpoint Handlers
# ============================================================================

def handle_submit_response(request: Request) -> tuple:
    """
    POST /responses/submit
    Submit a form response and calculate score (PUBLIC - no auth required).
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['template_id', 'answers']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return error_response(
                f"Missing required fields: {', '.join(missing)}",
                "VALIDATION_ERROR"
            )

        template_id = data['template_id']
        answers = data['answers']  # Dict of question_id -> answer_value
        submitter_email = data.get('submitter_email')
        submitter_name = data.get('submitter_name')

        # Get template details
        template_query = f"""
            SELECT template_name, opportunity_type, opportunity_subtype
            FROM `{TEMPLATES_TABLE}`
            WHERE template_id = @template_id
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("template_id", "STRING", template_id)
            ]
        )

        template_results = list(bq_client.query(template_query, job_config=job_config).result())

        if not template_results:
            return error_response(
                f"Template {template_id} not found",
                "NOT_FOUND",
                status_code=404
            )

        template = template_results[0]

        # Calculate score
        scoring_result = calculate_score(template_id, answers)

        # Generate response ID
        response_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Insert response record
        response_row = {
            'response_id': response_id,
            'template_id': template_id,
            'template_name': template.template_name,
            'opportunity_type': template.opportunity_type,
            'opportunity_subtype': template.opportunity_subtype,
            'submitter_email': submitter_email,
            'submitter_name': submitter_name,
            'total_score': scoring_result['total_score'],
            'max_possible_score': scoring_result['max_possible_score'],
            'score_percentage': scoring_result['score_percentage'],
            'total_questions': scoring_result['total_questions'],
            'answered_questions': scoring_result['answered_questions'],
            'completion_percentage': scoring_result['completion_percentage'],
            'submitted_at': now.isoformat(),
            'created_at': now.isoformat()
        }

        errors = bq_client.insert_rows_json(RESPONSES_TABLE, [response_row])
        if errors:
            return error_response(
                "Failed to save response",
                "DATABASE_ERROR",
                {"errors": errors},
                status_code=500
            )

        # Insert answer details
        answer_rows = []
        for answer_detail in scoring_result['answer_details']:
            answer_rows.append({
                'answer_id': str(uuid.uuid4()),
                'response_id': response_id,
                'question_id': answer_detail['question_id'],
                'question_text': answer_detail['question_text'],
                'answer_value': answer_detail['answer_value'],
                'points_earned': answer_detail['points_earned'],
                'points_possible': answer_detail['points_possible'],
                'created_at': now.isoformat()
            })

        errors = bq_client.insert_rows_json(RESPONSE_ANSWERS_TABLE, answer_rows)
        if errors:
            # Response is saved, but answers failed - log error but return success
            print(f"Warning: Failed to save answer details: {errors}")

        # Return response
        return success_response(
            {
                'response_id': response_id,
                'total_score': scoring_result['total_score'],
                'max_possible_score': scoring_result['max_possible_score'],
                'score_percentage': scoring_result['score_percentage'],
                'completion_percentage': scoring_result['completion_percentage'],
                'submitted_at': now.isoformat()
            },
            "Response submitted and scored successfully",
            status_code=201
        )

    except ValueError as e:
        return error_response(str(e), "VALIDATION_ERROR")
    except Exception as e:
        print(f"Error submitting response: {str(e)}")
        return error_response(
            "Failed to submit response",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


def handle_list_responses(request: Request) -> tuple:
    """
    GET /responses
    List all responses with optional filtering.
    """
    # Validate authentication
    is_valid, user_data, error = validate_auth(request, 'view')
    if not is_valid:
        return error

    try:
        # Get query parameters
        template_id = request.args.get('template_id')
        opportunity_type = request.args.get('opportunity_type')
        submitter_email = request.args.get('submitter_email')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))

        # Validate pagination
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        offset = (page - 1) * page_size

        # Build query
        where_clauses = []
        query_params = []

        if template_id:
            where_clauses.append("template_id = @template_id")
            query_params.append(bigquery.ScalarQueryParameter("template_id", "STRING", template_id))

        if opportunity_type:
            where_clauses.append("opportunity_type = @opportunity_type")
            query_params.append(bigquery.ScalarQueryParameter("opportunity_type", "STRING", opportunity_type))

        if submitter_email:
            where_clauses.append("submitter_email = @submitter_email")
            query_params.append(bigquery.ScalarQueryParameter("submitter_email", "STRING", submitter_email))

        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Count total
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `{RESPONSES_TABLE}`
            {where_clause}
        """

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        count_result = list(bq_client.query(count_query, job_config=job_config).result())[0]
        total_count = count_result.total

        # Get responses
        query = f"""
            SELECT
                response_id,
                template_id,
                template_name,
                opportunity_type,
                opportunity_subtype,
                submitter_email,
                submitter_name,
                total_score,
                max_possible_score,
                score_percentage,
                total_questions,
                answered_questions,
                completion_percentage,
                submitted_at,
                created_at
            FROM `{RESPONSES_TABLE}`
            {where_clause}
            ORDER BY submitted_at DESC
            LIMIT @page_size
            OFFSET @offset
        """

        query_params.extend([
            bigquery.ScalarQueryParameter("page_size", "INT64", page_size),
            bigquery.ScalarQueryParameter("offset", "INT64", offset)
        ])

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        results = bq_client.query(query, job_config=job_config).result()

        responses = []
        for row in results:
            responses.append({
                'response_id': row.response_id,
                'template_id': row.template_id,
                'template_name': row.template_name,
                'opportunity_type': row.opportunity_type,
                'opportunity_subtype': row.opportunity_subtype,
                'submitter_email': row.submitter_email,
                'submitter_name': row.submitter_name,
                'total_score': float(row.total_score),
                'max_possible_score': float(row.max_possible_score),
                'score_percentage': float(row.score_percentage),
                'total_questions': row.total_questions,
                'answered_questions': row.answered_questions,
                'completion_percentage': float(row.completion_percentage),
                'submitted_at': row.submitted_at.isoformat() if row.submitted_at else None,
                'created_at': row.created_at.isoformat() if row.created_at else None
            })

        return success_response({
            'items': responses,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })

    except Exception as e:
        print(f"Error listing responses: {str(e)}")
        return error_response(
            "Failed to list responses",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


def handle_get_response(request: Request, response_id: str) -> tuple:
    """
    GET /responses/:id
    Get response details including answer breakdown.
    """
    # Validate authentication
    is_valid, user_data, error = validate_auth(request, 'view')
    if not is_valid:
        return error

    try:
        # Get response
        query = f"""
            SELECT
                response_id,
                template_id,
                template_name,
                opportunity_type,
                opportunity_subtype,
                submitter_email,
                submitter_name,
                total_score,
                max_possible_score,
                score_percentage,
                total_questions,
                answered_questions,
                completion_percentage,
                submitted_at,
                created_at
            FROM `{RESPONSES_TABLE}`
            WHERE response_id = @response_id
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("response_id", "STRING", response_id)
            ]
        )

        results = list(bq_client.query(query, job_config=job_config).result())

        if not results:
            return error_response(
                f"Response {response_id} not found",
                "NOT_FOUND",
                status_code=404
            )

        row = results[0]
        response_data = {
            'response_id': row.response_id,
            'template_id': row.template_id,
            'template_name': row.template_name,
            'opportunity_type': row.opportunity_type,
            'opportunity_subtype': row.opportunity_subtype,
            'submitter_email': row.submitter_email,
            'submitter_name': row.submitter_name,
            'total_score': float(row.total_score),
            'max_possible_score': float(row.max_possible_score),
            'score_percentage': float(row.score_percentage),
            'total_questions': row.total_questions,
            'answered_questions': row.answered_questions,
            'completion_percentage': float(row.completion_percentage),
            'submitted_at': row.submitted_at.isoformat() if row.submitted_at else None,
            'created_at': row.created_at.isoformat() if row.created_at else None
        }

        # Get answer details
        answers_query = f"""
            SELECT
                answer_id,
                question_id,
                question_text,
                answer_value,
                points_earned,
                points_possible,
                created_at
            FROM `{RESPONSE_ANSWERS_TABLE}`
            WHERE response_id = @response_id
            ORDER BY created_at
        """

        answers_results = bq_client.query(answers_query, job_config=job_config).result()

        answers = []
        for ans_row in answers_results:
            answers.append({
                'answer_id': ans_row.answer_id,
                'question_id': ans_row.question_id,
                'question_text': ans_row.question_text,
                'answer_value': ans_row.answer_value,
                'points_earned': float(ans_row.points_earned),
                'points_possible': float(ans_row.points_possible),
                'created_at': ans_row.created_at.isoformat() if ans_row.created_at else None
            })

        response_data['answers'] = answers

        return success_response(response_data)

    except Exception as e:
        print(f"Error getting response: {str(e)}")
        return error_response(
            "Failed to get response",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


def handle_delete_response(request: Request, response_id: str) -> tuple:
    """
    DELETE /responses/:id
    Delete a response (admin only).
    """
    # Validate authentication (admin only)
    is_valid, user_data, error = validate_auth(request, 'admin')
    if not is_valid:
        return error

    try:
        # Delete answer details first
        delete_answers_query = f"""
            DELETE FROM `{RESPONSE_ANSWERS_TABLE}`
            WHERE response_id = @response_id
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("response_id", "STRING", response_id)
            ]
        )

        bq_client.query(delete_answers_query, job_config=job_config).result()

        # Delete response
        delete_response_query = f"""
            DELETE FROM `{RESPONSES_TABLE}`
            WHERE response_id = @response_id
        """

        bq_client.query(delete_response_query, job_config=job_config).result()

        return success_response(message=f"Response {response_id} deleted successfully")

    except Exception as e:
        print(f"Error deleting response: {str(e)}")
        return error_response(
            "Failed to delete response",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


def handle_get_analytics_summary(request: Request) -> tuple:
    """
    GET /analytics/summary
    Get overall analytics summary.
    """
    # Validate authentication
    is_valid, user_data, error = validate_auth(request, 'view')
    if not is_valid:
        return error

    try:
        # Get overall statistics
        query = f"""
            SELECT
                COUNT(*) as total_responses,
                AVG(score_percentage) as avg_score_percentage,
                AVG(completion_percentage) as avg_completion_percentage,
                MIN(score_percentage) as min_score,
                MAX(score_percentage) as max_score,
                COUNT(DISTINCT template_id) as unique_templates,
                COUNT(DISTINCT submitter_email) as unique_submitters
            FROM `{RESPONSES_TABLE}`
        """

        result = list(bq_client.query(query).result())[0]

        # Get responses by template
        by_template_query = f"""
            SELECT
                template_name,
                COUNT(*) as response_count,
                AVG(score_percentage) as avg_score
            FROM `{RESPONSES_TABLE}`
            GROUP BY template_name
            ORDER BY response_count DESC
            LIMIT 10
        """

        by_template_results = bq_client.query(by_template_query).result()

        by_template = []
        for row in by_template_results:
            by_template.append({
                'template_name': row.template_name,
                'response_count': row.response_count,
                'avg_score': round(float(row.avg_score), 2)
            })

        # Get responses by opportunity type
        by_type_query = f"""
            SELECT
                opportunity_type,
                COUNT(*) as response_count,
                AVG(score_percentage) as avg_score
            FROM `{RESPONSES_TABLE}`
            GROUP BY opportunity_type
            ORDER BY response_count DESC
        """

        by_type_results = bq_client.query(by_type_query).result()

        by_type = []
        for row in by_type_results:
            by_type.append({
                'opportunity_type': row.opportunity_type,
                'response_count': row.response_count,
                'avg_score': round(float(row.avg_score), 2)
            })

        analytics_data = {
            'summary': {
                'total_responses': result.total_responses,
                'avg_score_percentage': round(float(result.avg_score_percentage or 0), 2),
                'avg_completion_percentage': round(float(result.avg_completion_percentage or 0), 2),
                'min_score': round(float(result.min_score or 0), 2),
                'max_score': round(float(result.max_score or 0), 2),
                'unique_templates': result.unique_templates,
                'unique_submitters': result.unique_submitters
            },
            'by_template': by_template,
            'by_opportunity_type': by_type
        }

        return success_response(analytics_data)

    except Exception as e:
        print(f"Error getting analytics: {str(e)}")
        return error_response(
            "Failed to get analytics",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )


# ============================================================================
# Main Handler
# ============================================================================

@functions_framework.http
def response_scorer_handler(request: Request):
    """Main entry point for Response Scorer API."""

    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return add_cors_headers(response)

    # Parse path
    path = request.path.strip('/')

    # Route requests
    try:
        if path == 'responses/submit' and request.method == 'POST':
            response, status = handle_submit_response(request)
        elif path == 'responses' and request.method == 'GET':
            response, status = handle_list_responses(request)
        elif path.startswith('responses/') and request.method == 'GET':
            response_id = path.split('/')[1]
            response, status = handle_get_response(request, response_id)
        elif path.startswith('responses/') and request.method == 'DELETE':
            response_id = path.split('/')[1]
            response, status = handle_delete_response(request, response_id)
        elif path == 'analytics/summary' and request.method == 'GET':
            response, status = handle_get_analytics_summary(request)
        else:
            response, status = error_response(
                f"Endpoint not found: {request.method} /{path}",
                "NOT_FOUND",
                status_code=404
            )

        return add_cors_headers(response)

    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        response, status = error_response(
            "Internal server error",
            "INTERNAL_ERROR",
            {"error": str(e)},
            status_code=500
        )
        return add_cors_headers(response)

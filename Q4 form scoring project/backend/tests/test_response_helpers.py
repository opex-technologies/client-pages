"""
Unit tests for response_helpers module
Created: November 5, 2025
"""

import pytest
import json
from common.response_helpers import (
    success_response,
    error_response,
    bad_request_response,
    unauthorized_response,
    forbidden_response,
    not_found_response,
    conflict_response,
    validation_error_response,
    paginated_response,
    cors_preflight_response
)


class TestSuccessResponse:
    """Tests for success response"""

    def test_success_response_basic(self):
        """Test basic success response"""
        response_json, status_code, headers = success_response(
            data={'user_id': '123'},
            message='Success'
        )

        response = json.loads(response_json)
        assert status_code == 200
        assert response['success'] is True
        assert response['data'] == {'user_id': '123'}
        assert response['message'] == 'Success'
        assert 'timestamp' in response

    def test_success_response_custom_status(self):
        """Test success response with custom status code"""
        response_json, status_code, headers = success_response(
            data={'created': True},
            status_code=201
        )

        assert status_code == 201

    def test_success_response_list_data(self):
        """Test success response with list data"""
        data = [{'id': 1}, {'id': 2}]
        response_json, status_code, headers = success_response(data=data)

        response = json.loads(response_json)
        assert response['data'] == data


class TestErrorResponse:
    """Tests for error responses"""

    def test_error_response_basic(self):
        """Test basic error response"""
        response_json, status_code, headers = error_response(
            message='Something went wrong',
            status_code=500
        )

        response = json.loads(response_json)
        assert status_code == 500
        assert response['success'] is False
        assert response['error']['message'] == 'Something went wrong'
        assert 'ERROR_500' in response['error']['code']

    def test_error_response_with_code(self):
        """Test error response with custom error code"""
        response_json, status_code, headers = error_response(
            message='User not found',
            status_code=404,
            error_code='USER_NOT_FOUND'
        )

        response = json.loads(response_json)
        assert response['error']['code'] == 'USER_NOT_FOUND'

    def test_error_response_with_details(self):
        """Test error response with details"""
        response_json, status_code, headers = error_response(
            message='Validation failed',
            status_code=400,
            details={'field': 'email', 'error': 'Invalid format'}
        )

        response = json.loads(response_json)
        assert response['error']['details'] == {'field': 'email', 'error': 'Invalid format'}


class TestBadRequestResponse:
    """Tests for bad request response"""

    def test_bad_request_response(self):
        """Test bad request response"""
        response_json, status_code, headers = bad_request_response(
            message='Invalid input'
        )

        response = json.loads(response_json)
        assert status_code == 400
        assert response['error']['message'] == 'Invalid input'
        assert response['error']['code'] == 'BAD_REQUEST'


class TestUnauthorizedResponse:
    """Tests for unauthorized response"""

    def test_unauthorized_response(self):
        """Test unauthorized response"""
        response_json, status_code, headers = unauthorized_response(
            message='Invalid token'
        )

        response = json.loads(response_json)
        assert status_code == 401
        assert response['error']['message'] == 'Invalid token'
        assert response['error']['code'] == 'UNAUTHORIZED'


class TestForbiddenResponse:
    """Tests for forbidden response"""

    def test_forbidden_response(self):
        """Test forbidden response"""
        response_json, status_code, headers = forbidden_response(
            message='Insufficient permissions'
        )

        response = json.loads(response_json)
        assert status_code == 403
        assert response['error']['message'] == 'Insufficient permissions'


class TestNotFoundResponse:
    """Tests for not found response"""

    def test_not_found_response(self):
        """Test not found response"""
        response_json, status_code, headers = not_found_response(
            message='User not found',
            resource='user_id:123'
        )

        response = json.loads(response_json)
        assert status_code == 404
        assert response['error']['message'] == 'User not found'
        assert response['error']['details']['resource'] == 'user_id:123'


class TestConflictResponse:
    """Tests for conflict response"""

    def test_conflict_response(self):
        """Test conflict response"""
        response_json, status_code, headers = conflict_response(
            message='Email already exists',
            details={'email': 'user@example.com'}
        )

        response = json.loads(response_json)
        assert status_code == 409
        assert response['error']['message'] == 'Email already exists'
        assert response['error']['details']['email'] == 'user@example.com'


class TestValidationErrorResponse:
    """Tests for validation error response"""

    def test_validation_error_response(self):
        """Test validation error response"""
        errors = [
            'Email is required',
            'Password too short'
        ]

        response_json, status_code, headers = validation_error_response(
            errors=errors,
            message='Validation failed'
        )

        response = json.loads(response_json)
        assert status_code == 400
        assert response['error']['code'] == 'VALIDATION_ERROR'
        assert response['error']['details']['errors'] == errors


class TestPaginatedResponse:
    """Tests for paginated response"""

    def test_paginated_response_first_page(self):
        """Test paginated response for first page"""
        data = [{'id': i} for i in range(1, 51)]

        response_json, status_code, headers = paginated_response(
            data=data,
            page=1,
            page_size=50,
            total_count=150
        )

        response = json.loads(response_json)
        assert status_code == 200
        assert response['data']['pagination']['page'] == 1
        assert response['data']['pagination']['total_pages'] == 3
        assert response['data']['pagination']['has_next'] is True
        assert response['data']['pagination']['has_prev'] is False

    def test_paginated_response_middle_page(self):
        """Test paginated response for middle page"""
        data = [{'id': i} for i in range(51, 101)]

        response_json, status_code, headers = paginated_response(
            data=data,
            page=2,
            page_size=50,
            total_count=150
        )

        response = json.loads(response_json)
        assert response['data']['pagination']['has_next'] is True
        assert response['data']['pagination']['has_prev'] is True

    def test_paginated_response_last_page(self):
        """Test paginated response for last page"""
        data = [{'id': i} for i in range(101, 151)]

        response_json, status_code, headers = paginated_response(
            data=data,
            page=3,
            page_size=50,
            total_count=150
        )

        response = json.loads(response_json)
        assert response['data']['pagination']['has_next'] is False
        assert response['data']['pagination']['has_prev'] is True


class TestCORSPreflightResponse:
    """Tests for CORS preflight response"""

    def test_cors_preflight_response(self):
        """Test CORS preflight response"""
        response_json, status_code, headers = cors_preflight_response()

        assert status_code == 204
        assert headers['Access-Control-Allow-Origin'] == '*'
        assert 'GET' in headers['Access-Control-Allow-Methods']
        assert 'POST' in headers['Access-Control-Allow-Methods']


class TestResponseHeaders:
    """Tests for response headers"""

    def test_cors_headers_present(self):
        """Test that CORS headers are present"""
        response_json, status_code, headers = success_response(data={'test': True})

        assert 'Access-Control-Allow-Origin' in headers
        assert 'Access-Control-Allow-Methods' in headers
        assert 'Access-Control-Allow-Headers' in headers

    def test_content_type_header(self):
        """Test Content-Type header"""
        response_json, status_code, headers = success_response(data={'test': True})

        assert headers['Content-Type'] == 'application/json'

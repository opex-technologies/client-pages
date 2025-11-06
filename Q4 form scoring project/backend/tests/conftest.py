"""
Pytest configuration and shared fixtures
Created: November 5, 2025
"""

import pytest
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from google.cloud import bigquery

# Set test environment
os.environ['ENVIRONMENT'] = 'test'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-do-not-use-in-production'
os.environ['PROJECT_ID'] = 'opex-data-lake-k23k4y98m'


@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client for testing"""
    client = MagicMock(spec=bigquery.Client)
    client.project = 'opex-data-lake-k23k4y98m'
    return client


@pytest.fixture
def mock_request():
    """Mock Cloud Functions request object"""
    request = Mock()
    request.method = 'POST'
    request.headers = {'Content-Type': 'application/json'}
    request.get_json = Mock(return_value={})
    request.args = {}
    return request


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'user_id': str(uuid.uuid4()),
        'email': 'test@example.com',
        'full_name': 'Test User',
        'password_hash': '$2b$12$abcdefghijklmnopqrstuvwxyz1234567890',
        'status': 'active',
        'created_at': datetime.utcnow().isoformat(),
        'failed_login_attempts': 0,
        'mfa_secret': None
    }


@pytest.fixture
def sample_form_template():
    """Sample form template for testing"""
    return {
        'template_id': str(uuid.uuid4()),
        'template_name': 'Test SASE Form',
        'opportunity_type': 'Security',
        'opportunity_subtype': 'SASE',
        'description': 'Test form template',
        'questions': [
            {
                'question_id': str(uuid.uuid4()),
                'question_text': 'Do you have a firewall?',
                'weight': '10',
                'is_required': True,
                'input_type': 'radio',
                'validation_rules': None,
                'help_text': None,
                'display_order': 1
            },
            {
                'question_id': str(uuid.uuid4()),
                'question_text': 'Describe your security needs',
                'weight': 'Info',
                'is_required': False,
                'input_type': 'textarea',
                'validation_rules': None,
                'help_text': 'Please provide details',
                'display_order': 2
            }
        ],
        'version': 1,
        'status': 'draft',
        'created_at': datetime.utcnow().isoformat(),
        'created_by': str(uuid.uuid4())
    }


@pytest.fixture
def sample_response_data():
    """Sample response data for testing"""
    return {
        'response_id': str(uuid.uuid4()),
        'template_id': str(uuid.uuid4()),
        'provider_name': 'Test Provider',
        'provider_category': 'Security',
        'client_id': str(uuid.uuid4()),
        'submitted_at': datetime.utcnow().isoformat(),
        'total_score': 85.5,
        'max_possible_score': 100.0,
        'percentage_score': 85.5,
        'scored_by': str(uuid.uuid4()),
        'status': 'completed'
    }


@pytest.fixture
def sample_jwt_payload():
    """Sample JWT payload for testing"""
    return {
        'user_id': str(uuid.uuid4()),
        'email': 'test@example.com',
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }


@pytest.fixture
def valid_jwt_token(sample_jwt_payload):
    """Generate a valid JWT token for testing"""
    import jwt
    from common.config import config

    return jwt.encode(
        sample_jwt_payload,
        config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM
    )


@pytest.fixture
def expired_jwt_token():
    """Generate an expired JWT token for testing"""
    import jwt
    from common.config import config

    payload = {
        'user_id': str(uuid.uuid4()),
        'email': 'test@example.com',
        'exp': datetime.utcnow() - timedelta(hours=1),  # Expired
        'iat': datetime.utcnow() - timedelta(hours=25)
    }

    return jwt.encode(
        payload,
        config.JWT_SECRET_KEY,
        algorithm=config.JWT_ALGORITHM
    )


@pytest.fixture
def sample_permission_data():
    """Sample permission data for testing"""
    return {
        'permission_id': str(uuid.uuid4()),
        'user_id': str(uuid.uuid4()),
        'company': 'Acme Healthcare',
        'category': None,
        'permission_level': 'edit',
        'granted_by': str(uuid.uuid4()),
        'granted_at': datetime.utcnow().isoformat(),
        'is_active': True
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment after each test"""
    yield
    # Cleanup after test
    pass


def pytest_configure(config):
    """Pytest configuration"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )

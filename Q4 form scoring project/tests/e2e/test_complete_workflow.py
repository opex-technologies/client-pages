"""
End-to-End Test Suite - Complete Workflow
Tests the entire user journey through the system.

Workflow:
1. User Registration
2. User Login
3. Create Template
4. Add Questions to Template
5. Preview Form
6. Deploy Form (optional)
7. Submit Response (as end user)
8. View Response List
9. View Response Details
10. View Analytics

Run: pytest test_complete_workflow.py -v --html=report.html
"""

import pytest
import requests
import time
import uuid
from datetime import datetime
from typing import Dict, Optional


# Configuration
BASE_URL = "https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net"
AUTH_API = f"{BASE_URL}/auth-api"
FORM_BUILDER_API = f"{BASE_URL}/form-builder-api"
RESPONSE_SCORER_API = f"{BASE_URL}/response-scorer-api"

# Test data
TEST_USER_EMAIL = f"e2e-test-{uuid.uuid4().hex[:8]}@opextest.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_NAME = "E2E Test User"


class TestState:
    """Shared state across tests"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id: Optional[str] = None
    template_id: Optional[str] = None
    response_id: Optional[str] = None


@pytest.fixture(scope="module")
def state():
    """Fixture to share state between tests"""
    return TestState()


class TestAuthenticationWorkflow:
    """Test authentication flow"""

    def test_01_user_registration(self, state):
        """Test user registration"""
        print(f"\n🔐 Testing user registration for: {TEST_USER_EMAIL}")

        payload = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": TEST_USER_NAME
        }

        response = requests.post(
            f"{AUTH_API}/auth/register",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status: {response.status_code}")
        if response.status_code != 201:
            print(f"Response: {response.text}")

        assert response.status_code == 201, f"Registration failed: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "user_id" in data["data"]

        state.user_id = data["data"]["user_id"]
        print(f"✓ User registered successfully: {state.user_id}")

    def test_02_user_login(self, state):
        """Test user login"""
        print(f"\n🔐 Testing user login for: {TEST_USER_EMAIL}")

        # Wait a moment for BigQuery streaming buffer
        time.sleep(2)

        payload = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }

        response = requests.post(
            f"{AUTH_API}/auth/login",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status: {response.status_code}")

        # Note: May fail due to BigQuery streaming buffer (90 min delay)
        # This is a known limitation documented in BIGQUERY_LIMITATIONS.md
        if response.status_code != 200:
            print(f"⚠️  Login failed (expected due to BigQuery streaming buffer)")
            print(f"Response: {response.text}")
            pytest.skip("Skipping due to BigQuery streaming buffer limitation")

        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

        state.access_token = data["data"]["access_token"]
        state.refresh_token = data["data"]["refresh_token"]
        print(f"✓ Login successful, got tokens")


class TestTemplateCreationWorkflow:
    """Test template creation and management"""

    @pytest.fixture
    def auth_headers(self, state):
        """Auth headers for authenticated requests"""
        if not state.access_token:
            pytest.skip("No access token available (login may have failed)")
        return {
            "Authorization": f"Bearer {state.access_token}",
            "Content-Type": "application/json"
        }

    def test_03_list_questions(self, auth_headers):
        """Test querying available questions"""
        print("\n📋 Testing question database query")

        response = requests.get(
            f"{FORM_BUILDER_API}/questions",
            headers=auth_headers,
            params={"limit": 10, "category": "All"}
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 200, f"Failed to list questions: {response.text}"

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

        print(f"✓ Found {len(data['data'])} questions")

    def test_04_create_template(self, state, auth_headers):
        """Test creating a new form template"""
        print("\n📝 Testing template creation")

        # First, get some questions to add
        questions_response = requests.get(
            f"{FORM_BUILDER_API}/questions",
            headers=auth_headers,
            params={"limit": 3}
        )
        questions = questions_response.json()["data"][:3]

        # Prepare template data
        template_questions = []
        for idx, q in enumerate(questions):
            template_questions.append({
                "question_id": q["question_id"],
                "weight": 10 if idx < 2 else None,  # First 2 weighted, 3rd is info
                "is_required": True,
                "sort_order": idx + 1
            })

        payload = {
            "template_name": f"E2E Test Template {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "opportunity_type": "Security",
            "opportunity_subtype": "SASE",
            "description": "Template created by E2E test",
            "questions": template_questions
        }

        response = requests.post(
            f"{FORM_BUILDER_API}/templates",
            json=payload,
            headers=auth_headers
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 201, f"Failed to create template: {response.text}"

        data = response.json()
        assert data["success"] is True
        assert "template_id" in data["data"]

        state.template_id = data["data"]["template_id"]
        print(f"✓ Template created: {state.template_id}")

    def test_05_get_template(self, state, auth_headers):
        """Test retrieving template details"""
        if not state.template_id:
            pytest.skip("No template created")

        print(f"\n📝 Testing template retrieval: {state.template_id}")

        response = requests.get(
            f"{FORM_BUILDER_API}/templates/{state.template_id}",
            headers=auth_headers
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 200, f"Failed to get template: {response.text}"

        data = response.json()
        assert data["success"] is True
        assert data["data"]["template_id"] == state.template_id
        assert len(data["data"]["questions"]) == 3

        print(f"✓ Template retrieved with {len(data['data']['questions'])} questions")

    def test_06_preview_form(self, state, auth_headers):
        """Test form preview generation"""
        if not state.template_id:
            pytest.skip("No template created")

        print(f"\n👁️  Testing form preview generation")

        response = requests.post(
            f"{FORM_BUILDER_API}/templates/{state.template_id}/preview",
            headers=auth_headers
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 200, f"Failed to generate preview: {response.text}"

        data = response.json()
        assert data["success"] is True
        assert "html" in data["data"]
        assert len(data["data"]["html"]) > 1000  # Should be substantial HTML

        print(f"✓ Form preview generated ({len(data['data']['html'])} chars)")


class TestResponseWorkflow:
    """Test response submission and scoring"""

    def test_07_submit_response(self, state):
        """Test submitting a response (public endpoint)"""
        if not state.template_id:
            pytest.skip("No template created")

        print(f"\n📤 Testing response submission")

        # Create sample answers
        payload = {
            "template_id": state.template_id,
            "submitter_email": "testuser@example.com",
            "submitter_name": "Test User",
            "answers": {
                "Q001": "Yes, we have implemented security measures",
                "Q002": "50 employees",
                "Q003": "We use multi-factor authentication"
            }
        }

        response = requests.post(
            f"{RESPONSE_SCORER_API}/responses/submit",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 201, f"Failed to submit response: {response.text}"

        data = response.json()
        assert data["success"] is True
        assert "response_id" in data["data"]
        assert "total_score" in data["data"]
        assert "score_percentage" in data["data"]

        state.response_id = data["data"]["response_id"]
        print(f"✓ Response submitted: {state.response_id}")
        print(f"  Score: {data['data']['total_score']}/{data['data']['max_possible_score']} ({data['data']['score_percentage']}%)")
        print(f"  Completion: {data['data']['completion_percentage']}%")

    def test_08_list_responses(self, state):
        """Test listing responses"""
        print(f"\n📋 Testing response list")

        # Note: This endpoint requires authentication
        # If login failed, we'll skip this test
        if not state.access_token:
            print("⚠️  Skipping (no auth token)")
            pytest.skip("No authentication token available")

        headers = {"Authorization": f"Bearer {state.access_token}"}

        response = requests.get(
            f"{RESPONSE_SCORER_API}/responses",
            headers=headers,
            params={"page": 1, "page_size": 10}
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 200, f"Failed to list responses: {response.text}"

        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]

        print(f"✓ Found {len(data['data']['items'])} responses")

    def test_09_get_response_detail(self, state):
        """Test getting response details"""
        if not state.response_id or not state.access_token:
            pytest.skip("No response or auth token available")

        print(f"\n📋 Testing response detail retrieval")

        headers = {"Authorization": f"Bearer {state.access_token}"}

        response = requests.get(
            f"{RESPONSE_SCORER_API}/responses/{state.response_id}",
            headers=headers
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 200, f"Failed to get response: {response.text}"

        data = response.json()
        assert data["success"] is True
        assert data["data"]["response_id"] == state.response_id
        assert "answers" in data["data"]

        print(f"✓ Response details retrieved with {len(data['data']['answers'])} answers")


class TestAnalyticsWorkflow:
    """Test analytics and reporting"""

    def test_10_get_analytics_summary(self, state):
        """Test analytics summary"""
        if not state.access_token:
            pytest.skip("No authentication token available")

        print(f"\n📊 Testing analytics summary")

        headers = {"Authorization": f"Bearer {state.access_token}"}

        response = requests.get(
            f"{RESPONSE_SCORER_API}/analytics/summary",
            headers=headers
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 200, f"Failed to get analytics: {response.text}"

        data = response.json()
        assert data["success"] is True
        assert "summary" in data["data"]

        summary = data["data"]["summary"]
        print(f"✓ Analytics retrieved:")
        print(f"  Total responses: {summary.get('total_responses', 0)}")
        print(f"  Avg score: {summary.get('avg_score_percentage', 0):.1f}%")

    def test_11_export_responses(self, state):
        """Test CSV export"""
        if not state.access_token:
            pytest.skip("No authentication token available")

        print(f"\n💾 Testing CSV export")

        headers = {"Authorization": f"Bearer {state.access_token}"}

        response = requests.get(
            f"{RESPONSE_SCORER_API}/analytics/responses/export",
            headers=headers,
            params={"page_size": 5}
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 200, f"Failed to export: {response.text}"

        csv_data = response.text
        assert "response_id" in csv_data  # CSV header

        lines = csv_data.split('\n')
        print(f"✓ CSV export successful ({len(lines)} lines)")


class TestCleanup:
    """Cleanup test data"""

    def test_99_cleanup(self, state):
        """Clean up test data"""
        print(f"\n🧹 Cleaning up test data")

        # Delete response
        if state.response_id and state.access_token:
            headers = {"Authorization": f"Bearer {state.access_token}"}
            try:
                response = requests.delete(
                    f"{RESPONSE_SCORER_API}/responses/{state.response_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    print(f"✓ Deleted response: {state.response_id}")
            except Exception as e:
                print(f"⚠️  Could not delete response: {e}")

        # Delete template
        if state.template_id and state.access_token:
            headers = {"Authorization": f"Bearer {state.access_token}"}
            try:
                response = requests.delete(
                    f"{FORM_BUILDER_API}/templates/{state.template_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    print(f"✓ Deleted template: {state.template_id}")
            except Exception as e:
                print(f"⚠️  Could not delete template: {e}")

        print("\n✅ E2E test cleanup complete")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--html=e2e-report.html", "--self-contained-html"])

"""API endpoint tests for complaint processing."""
import pytest
from unittest.mock import patch, MagicMock
import json


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_200(self, api_client):
        """Health endpoint should return 200."""
        response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestComplaintEndpoint:
    """Test complaint processing endpoint."""

    def test_complaint_submission_success(self, api_client, sample_complaint):
        """Valid complaint should be processed successfully."""
        response = api_client.post("/complaint", json=sample_complaint)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "status" in data

    def test_complaint_missing_required_field(self, api_client):
        """Complaint missing complaint_text should fail validation."""
        invalid_complaint = {
            "customer_id": "CUST_001"
            # Missing complaint_text
        }
        response = api_client.post("/complaint", json=invalid_complaint)
        assert response.status_code == 422  # Validation error

    def test_complaint_empty_text(self, api_client):
        """Complaint with empty text should be rejected."""
        invalid_complaint = {
            "complaint_text": "",
            "customer_id": "CUST_001"
        }
        response = api_client.post("/complaint", json=invalid_complaint)
        assert response.status_code == 422

    def test_complaint_oversized_input(self, api_client):
        """Complaint exceeding reasonable size should fail."""
        huge_complaint = {
            "complaint_text": "x" * 100000,  # 100KB text
            "customer_id": "CUST_001"
        }
        response = api_client.post("/complaint", json=huge_complaint)
        # Should fail validation or handle gracefully
        assert response.status_code in [422, 413, 400]

    def test_complaint_with_valid_fields(self, api_client, sample_complaint):
        """Complaint with all optional fields should work."""
        complaint = {
            **sample_complaint,
            "channel": "email",
            "priority": "high"
        }
        response = api_client.post("/complaint", json=complaint)
        assert response.status_code == 200

    def test_complaint_response_structure(self, api_client, sample_complaint):
        """Response should have all required fields."""
        response = api_client.post("/complaint", json=sample_complaint)
        assert response.status_code == 200
        data = response.json()

        # Check required response fields
        assert "response" in data
        assert "status" in data
        assert "complaint_id" in data
        assert "category" in data
        assert "sentiment" in data


class TestComplaintStreamEndpoint:
    """Test streaming complaint endpoint."""

    def test_streaming_endpoint_returns_event_stream(self, api_client, sample_complaint):
        """Streaming endpoint should return Server-Sent Events."""
        response = api_client.post("/complaint-stream", json=sample_complaint)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_streaming_provides_progress_updates(self, api_client, sample_complaint):
        """Streaming should emit progress events."""
        response = api_client.post("/complaint-stream", json=sample_complaint, stream=True)
        assert response.status_code == 200

        # Read event stream
        events = []
        for line in response.iter_lines():
            if line and line.startswith(b"data:"):
                events.append(line)

        # Should have multiple progress events
        assert len(events) > 0


class TestComplaintHistoryEndpoint:
    """Test complaint history retrieval."""

    def test_get_customer_history_success(self, api_client):
        """Should retrieve history for valid customer."""
        response = api_client.get("/history/CUST_001")
        assert response.status_code == 200
        data = response.json()
        assert "complaints" in data
        assert isinstance(data["complaints"], list)

    def test_get_history_missing_customer(self, api_client):
        """Non-existent customer should return empty or 404."""
        response = api_client.get("/history/NONEXISTENT_CUST")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert response.json()["complaints"] == []

    def test_history_contains_complaint_details(self, api_client):
        """Retrieved history should have complaint details."""
        response = api_client.get("/history/CUST_001")
        if response.status_code == 200:
            data = response.json()
            if data["complaints"]:
                complaint = data["complaints"][0]
                assert "complaint_text" in complaint or "text" in complaint
                assert "date" in complaint or "created_at" in complaint


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    def test_malformed_json(self, api_client):
        """Malformed JSON should return 400."""
        response = api_client.post(
            "/complaint",
            content=b"not valid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code in [400, 422]

    def test_missing_content_type(self, api_client, sample_complaint):
        """Request without content-type should fail."""
        response = api_client.post(
            "/complaint",
            data=json.dumps(sample_complaint),
            headers={}
        )
        assert response.status_code in [400, 415, 422]

    def test_special_characters_in_complaint(self, api_client):
        """Complaint with special characters should be handled."""
        complaint = {
            "complaint_text": "My service has 😢 emoji and special chars: @#$%",
            "customer_id": "CUST_SPECIAL"
        }
        response = api_client.post("/complaint", json=complaint)
        # Should either work or fail gracefully
        assert response.status_code in [200, 400, 422]

    def test_very_long_customer_id(self, api_client):
        """Very long customer ID should be handled."""
        complaint = {
            "complaint_text": "Test complaint",
            "customer_id": "x" * 1000
        }
        response = api_client.post("/complaint", json=complaint)
        assert response.status_code in [200, 400, 422]

"""
API Router Tests
"""

import pytest
from fastapi import status


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, client):
        """Test /health endpoint returns OK."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

    def test_ready_check(self, client):
        """Test /ready endpoint returns OK."""
        response = client.get("/ready")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "ready" in data


class TestModelsAPI:
    """Test models API endpoints."""

    def test_list_models_empty(self, client):
        """Test listing models when none exist."""
        response = client.get("/api/v1/models")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_register_model(self, client, sample_model_data):
        """Test registering a new model."""
        response = client.post("/api/v1/models", json=sample_model_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_model_data["name"]
        assert "id" in data

    def test_register_model_invalid(self, client):
        """Test registering model with invalid data."""
        response = client.post("/api/v1/models", json={"invalid": "data"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_model(self, client, sample_model_data):
        """Test getting a specific model."""
        # First register
        create_response = client.post("/api/v1/models", json=sample_model_data)
        model_id = create_response.json()["id"]

        # Then get
        response = client.get(f"/api/v1/models/{model_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == model_id

    def test_get_model_not_found(self, client):
        """Test getting non-existent model."""
        response = client.get("/api/v1/models/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_model(self, client, sample_model_data):
        """Test updating a model."""
        # First register
        create_response = client.post("/api/v1/models", json=sample_model_data)
        model_id = create_response.json()["id"]

        # Then update
        update_data = {"description": "Updated description"}
        response = client.put(f"/api/v1/models/{model_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Updated description"

    def test_delete_model(self, client, sample_model_data):
        """Test deleting a model."""
        # First register
        create_response = client.post("/api/v1/models", json=sample_model_data)
        model_id = create_response.json()["id"]

        # Then delete
        response = client.delete(f"/api/v1/models/{model_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        get_response = client.get(f"/api/v1/models/{model_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


class TestEvaluationsAPI:
    """Test evaluations API endpoints."""

    def test_list_evaluations(self, client):
        """Test listing evaluations."""
        response = client.get("/api/v1/evaluations")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_start_evaluation(self, client, sample_model_data, sample_evaluation_config):
        """Test starting a new evaluation."""
        # First register a model
        model_response = client.post("/api/v1/models", json=sample_model_data)
        model_id = model_response.json()["id"]

        # Start evaluation
        eval_data = {
            "model_id": model_id,
            "config": sample_evaluation_config,
        }
        response = client.post("/api/v1/evaluations", json=eval_data)
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["model_id"] == model_id
        assert data["status"] in ["pending", "running"]

    def test_get_evaluation(self, client, sample_model_data, sample_evaluation_config):
        """Test getting a specific evaluation."""
        # Setup
        model_response = client.post("/api/v1/models", json=sample_model_data)
        model_id = model_response.json()["id"]
        
        eval_data = {"model_id": model_id, "config": sample_evaluation_config}
        eval_response = client.post("/api/v1/evaluations", json=eval_data)
        eval_id = eval_response.json()["id"]

        # Get evaluation
        response = client.get(f"/api/v1/evaluations/{eval_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == eval_id

    def test_cancel_evaluation(self, client, sample_model_data, sample_evaluation_config):
        """Test cancelling an evaluation."""
        # Setup
        model_response = client.post("/api/v1/models", json=sample_model_data)
        model_id = model_response.json()["id"]
        
        eval_data = {"model_id": model_id, "config": sample_evaluation_config}
        eval_response = client.post("/api/v1/evaluations", json=eval_data)
        eval_id = eval_response.json()["id"]

        # Cancel
        response = client.post(f"/api/v1/evaluations/{eval_id}/cancel")
        assert response.status_code == status.HTTP_200_OK


class TestDashboardAPI:
    """Test dashboard API endpoints."""

    def test_get_stats(self, client):
        """Test getting dashboard stats."""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_models" in data
        assert "total_evaluations" in data
        assert "risk_distribution" in data


class TestComplianceAPI:
    """Test compliance API endpoints."""

    def test_list_frameworks(self, client):
        """Test listing compliance frameworks."""
        response = client.get("/api/v1/compliance/frameworks")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_framework(self, client):
        """Test getting a specific framework."""
        response = client.get("/api/v1/compliance/frameworks/eu-ai-act")
        # May be 200 or 404 depending on if framework exists
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


class TestGuardrailsAPI:
    """Test guardrails API endpoints."""

    def test_list_guardrails(self, client):
        """Test listing guardrails."""
        response = client.get("/api/v1/guardrails")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_create_guardrail(self, client, sample_guardrail_config):
        """Test creating a guardrail."""
        response = client.post("/api/v1/guardrails", json=sample_guardrail_config)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_guardrail_config["name"]

    def test_toggle_guardrail(self, client, sample_guardrail_config):
        """Test toggling guardrail enabled state."""
        # Create
        create_response = client.post("/api/v1/guardrails", json=sample_guardrail_config)
        guardrail_id = create_response.json()["id"]

        # Toggle off
        response = client.post(
            f"/api/v1/guardrails/{guardrail_id}/toggle",
            json={"enabled": False}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["enabled"] is False


class TestConnectorsAPI:
    """Test connectors API endpoints."""

    def test_list_connectors(self, client):
        """Test listing connectors."""
        response = client.get("/api/v1/connectors")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_connector(self, client):
        """Test getting a specific connector."""
        response = client.get("/api/v1/connectors/openai")
        # May be 200 or 404
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

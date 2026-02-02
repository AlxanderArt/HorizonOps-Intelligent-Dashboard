"""
API Integration Tests for HorizonOps
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from api.main import app

client = TestClient(app)


class TestRootEndpoints:
    """Test root and system endpoints."""

    def test_root_returns_service_info(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "HorizonOps Predictive Intelligence"
        assert "version" in data
        assert "endpoints" in data

    def test_system_status_healthy(self):
        response = client.get("/api/v1/system/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data


class TestPredictionEndpoints:
    """Test prediction API endpoints."""

    def test_predict_returns_valid_response(self):
        payload = {
            "machine_id": "CNC-ALPHA-921",
            "features": {
                "vibration_rms": 22.5,
                "vibration_peak": 38.2,
                "vibration_kurtosis": 3.4,
                "temperature": 45.0,
                "temp_rate_of_change": 0.1,
                "power_consumption": 12.1,
                "power_deviation": 1.5,
                "time_since_maintenance": 200,
                "cumulative_cycles": 120000
            },
            "request_explanation": True
        }

        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "prediction_id" in data
        assert "risk_score" in data
        assert 0 <= data["risk_score"] <= 100
        assert "failure_probability" in data
        assert 0 <= data["failure_probability"] <= 1
        assert "risk_level" in data
        assert data["risk_level"] in ["low", "medium", "high", "critical"]
        assert "recommended_action" in data
        assert "explanation" in data

    def test_predict_high_risk_features(self):
        """Test that high-risk features produce high risk score."""
        payload = {
            "machine_id": "CNC-ALPHA-921",
            "features": {
                "vibration_rms": 55.0,  # High
                "vibration_peak": 85.0,  # High
                "vibration_kurtosis": 7.0,  # High - indicates bearing fault
                "temperature": 58.0,  # Elevated
                "temp_rate_of_change": 2.0,
                "power_consumption": 15.0,
                "power_deviation": 12.0,
                "time_since_maintenance": 600,  # Long time since PM
                "cumulative_cycles": 180000
            }
        }

        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["risk_score"] > 50  # Should be elevated
        assert data["risk_level"] in ["high", "critical"]

    def test_predict_low_risk_features(self):
        """Test that normal features produce low risk score."""
        payload = {
            "machine_id": "CNC-ALPHA-921",
            "features": {
                "vibration_rms": 18.0,  # Normal
                "vibration_peak": 32.0,  # Normal
                "vibration_kurtosis": 3.0,  # Normal
                "temperature": 42.0,  # Normal
                "temp_rate_of_change": 0.0,
                "power_consumption": 11.5,
                "power_deviation": 0.5,
                "time_since_maintenance": 50,  # Recent PM
                "cumulative_cycles": 80000
            }
        }

        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["risk_score"] < 40
        assert data["risk_level"] == "low"


class TestTelemetryEndpoints:
    """Test telemetry API endpoints."""

    def test_get_telemetry(self):
        response = client.get("/api/v1/telemetry/CNC-ALPHA-921")
        assert response.status_code == 200

        data = response.json()
        assert data["machine_id"] == "CNC-ALPHA-921"
        assert "data" in data
        assert len(data["data"]) > 0

    def test_get_latest_telemetry(self):
        response = client.get("/api/v1/telemetry/CNC-ALPHA-921/latest")
        assert response.status_code == 200

        data = response.json()
        assert "reading" in data
        assert "vibration_rms" in data["reading"]
        assert "temperature" in data["reading"]

    def test_telemetry_statistics(self):
        response = client.get("/api/v1/telemetry/CNC-ALPHA-921/statistics?window_minutes=60")
        assert response.status_code == 200

        data = response.json()
        assert "statistics" in data
        assert "vibration" in data["statistics"]


class TestHealthEndpoints:
    """Test health score API endpoints."""

    def test_get_machine_health(self):
        response = client.get("/api/v1/health/CNC-ALPHA-921")
        assert response.status_code == 200

        data = response.json()
        assert data["machine_id"] == "CNC-ALPHA-921"
        assert "health_score" in data
        assert 0 <= data["health_score"] <= 100
        assert "status" in data
        assert "components" in data

    def test_get_fleet_health(self):
        response = client.get("/api/v1/health/fleet")
        assert response.status_code == 200

        data = response.json()
        assert "summary" in data
        assert "machines" in data
        assert data["summary"]["total_machines"] > 0

    def test_get_health_history(self):
        response = client.get("/api/v1/health/CNC-ALPHA-921/history?days=7")
        assert response.status_code == 200

        data = response.json()
        assert "history" in data
        assert len(data["history"]) == 7


class TestFeedbackEndpoints:
    """Test feedback collection endpoints."""

    def test_submit_feedback(self):
        payload = {
            "prediction_id": "test-prediction-123",
            "machine_id": "CNC-ALPHA-921",
            "actual_outcome": "failure",
            "was_prediction_accurate": True,
            "user_notes": "Bearing replaced as predicted",
            "action_taken": "preventive_maintenance",
            "time_to_event": 48.5
        }

        response = client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "accepted"
        assert "feedback_id" in data

    def test_get_feedback_statistics(self):
        response = client.get("/api/v1/feedback/statistics")
        assert response.status_code == 200

        data = response.json()
        assert "total_feedback" in data


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_success(self):
        """Test successful login returns token."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "admin"

    def test_login_invalid_credentials(self):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_login_json_endpoint(self):
        """Test JSON-based login endpoint."""
        response = client.post(
            "/api/v1/auth/login/json",
            json={"username": "operator", "password": "operator123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "operator"

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token fails."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token."""
        # First login
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        # Access protected endpoint
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["username"] == "admin"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_predict_missing_features(self):
        """Test prediction with missing required features."""
        payload = {
            "machine_id": "CNC-ALPHA-921",
            "features": {
                "vibration_rms": 22.5
                # Missing other required features
            }
        }
        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 422  # Validation error

    def test_telemetry_with_limit(self):
        """Test telemetry endpoint respects limit parameter."""
        response = client.get("/api/v1/telemetry/CNC-ALPHA-921?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 10

    def test_health_history_max_days(self):
        """Test health history respects max days limit."""
        response = client.get("/api/v1/health/CNC-ALPHA-921/history?days=30")
        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 30

    def test_fleet_health_includes_all_machines(self):
        """Test fleet health returns all machines."""
        response = client.get("/api/v1/health/fleet")
        data = response.json()
        assert data["summary"]["total_machines"] == 8

    def test_feedback_export_labels(self):
        """Test feedback export endpoint."""
        response = client.get("/api/v1/feedback/export")
        assert response.status_code == 200
        data = response.json()
        assert "training_labels" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

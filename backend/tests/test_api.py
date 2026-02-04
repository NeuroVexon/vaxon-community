"""
Axon by NeuroVexon - API Tests
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client():
    """Create test client"""
    from main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health endpoints"""

    def test_root_endpoint(self, client):
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "tagline" in data

    def test_health_endpoint(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestSettingsEndpoints:
    """Tests for settings endpoints"""

    def test_get_settings(self, client):
        response = client.get("/api/v1/settings")

        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "llm_provider" in data
        assert "available_providers" in data


class TestAuditEndpoints:
    """Tests for audit endpoints"""

    def test_get_audit_logs(self, client):
        response = client.get("/api/v1/audit")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_audit_stats(self, client):
        response = client.get("/api/v1/audit/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_event_type" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

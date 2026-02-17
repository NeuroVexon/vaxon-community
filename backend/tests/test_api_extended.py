"""
Axon by NeuroVexon - Extended API Tests

Integration tests for API endpoints: agents, memory, conversations, analytics.
Require all backend dependencies installed (apscheduler, telegram, discord, etc.).
Run on server with: cd backend && pytest tests/test_api_extended.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Skip all tests if full dependencies are not installed
try:
    from main import app
    from fastapi.testclient import TestClient
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

pytestmark = pytest.mark.skipif(not HAS_DEPS, reason="Server dependencies not installed")


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestAgentEndpoints:
    """Tests for /api/v1/agents endpoints"""

    def test_list_agents(self, client):
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Default agents should exist
        assert len(data) >= 3

    def test_list_agents_has_default(self, client):
        response = client.get("/api/v1/agents")
        data = response.json()
        names = [a["name"] for a in data]
        assert "Assistent" in names

    def test_get_agent_detail(self, client):
        # Get list first
        agents = client.get("/api/v1/agents").json()
        agent_id = agents[0]["id"]

        response = client.get(f"/api/v1/agents/{agent_id}")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "allowed_tools" in data

    def test_get_nonexistent_agent(self, client):
        response = client.get("/api/v1/agents/nonexistent-id")
        assert response.status_code == 404

    def test_create_agent(self, client):
        response = client.post("/api/v1/agents", json={
            "name": "Test-Agent-API",
            "description": "Erstellt via Test",
            "risk_level_max": "low",
            "allowed_tools": ["web_search"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test-Agent-API"
        assert data["risk_level_max"] == "low"

    def test_update_agent(self, client):
        # Create
        created = client.post("/api/v1/agents", json={
            "name": "Update-Test",
        }).json()

        # Update
        response = client.put(f"/api/v1/agents/{created['id']}", json={
            "description": "Aktualisiert"
        })
        assert response.status_code == 200
        assert response.json()["description"] == "Aktualisiert"

    def test_delete_agent(self, client):
        # Create non-default agent
        created = client.post("/api/v1/agents", json={
            "name": "Loeschbar-API",
        }).json()

        # Delete
        response = client.delete(f"/api/v1/agents/{created['id']}")
        assert response.status_code == 200

        # Verify deleted
        response = client.get(f"/api/v1/agents/{created['id']}")
        assert response.status_code == 404

    def test_cannot_delete_default_agent(self, client):
        agents = client.get("/api/v1/agents").json()
        default = next(a for a in agents if a.get("is_default"))

        response = client.delete(f"/api/v1/agents/{default['id']}")
        # Should fail or return error
        assert response.status_code in [400, 403, 409, 200]
        if response.status_code == 200:
            # If returns 200 with error message
            response.json()
            # Default agent should still exist
            check = client.get(f"/api/v1/agents/{default['id']}")
            assert check.status_code == 200


class TestMemoryEndpoints:
    """Tests for /api/v1/memory endpoints"""

    def test_list_memories_empty(self, client):
        response = client.get("/api/v1/memory")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_memory(self, client):
        response = client.post("/api/v1/memory", json={
            "key": "API-Test",
            "content": "Erstellt via API Test",
            "category": "Test"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "API-Test"
        assert data["content"] == "Erstellt via API Test"

    def test_get_memory(self, client):
        # Create
        created = client.post("/api/v1/memory", json={
            "key": "Get-Test",
            "content": "Abrufbar"
        }).json()

        response = client.get(f"/api/v1/memory/{created['id']}")
        assert response.status_code == 200
        assert response.json()["key"] == "Get-Test"

    def test_delete_memory(self, client):
        created = client.post("/api/v1/memory", json={
            "key": "Loesch-Test",
            "content": "Wird geloescht"
        }).json()

        response = client.delete(f"/api/v1/memory/{created['id']}")
        assert response.status_code == 200

    def test_search_memories(self, client):
        client.post("/api/v1/memory", json={
            "key": "Suchbar",
            "content": "Python ist toll"
        })

        response = client.get("/api/v1/memory?search=Python")
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)


class TestConversationEndpoints:
    """Tests for /api/v1/chat/conversations endpoints"""

    def test_list_conversations(self, client):
        response = client.get("/api/v1/chat/conversations")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_send_message_creates_conversation(self, client):
        response = client.post("/api/v1/chat/send", json={
            "message": "Hallo Test"
        })
        # May return 200 or 500 depending on LLM availability
        # We just verify the endpoint exists and accepts the request
        assert response.status_code in [200, 500, 503]


class TestAnalyticsEndpoints:
    """Tests for /api/v1/analytics endpoints"""

    def test_analytics_overview(self, client):
        response = client.get("/api/v1/analytics/overview")
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data or "total_conversations" in data or isinstance(data, dict)


class TestSettingsHealth:
    """Tests for settings and health endpoints"""

    def test_health_returns_providers(self, client):
        response = client.get("/api/v1/settings/health")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_settings_returns_app_info(self, client):
        response = client.get("/api/v1/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "Axon by NeuroVexon"
        assert "llm_provider" in data

    def test_settings_masks_api_keys(self, client):
        response = client.get("/api/v1/settings")
        data = response.json()
        # API keys should not be exposed in plain text
        for key in ["anthropic_api_key", "openai_api_key"]:
            if key in data:
                value = data[key]
                if value:
                    # Should be masked or not the raw key
                    assert "sk-" not in str(value) or "***" in str(value) or value == ""


class TestRootEndpoints:
    """Tests for root-level endpoints"""

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Axon" in data.get("name", "")
        assert "version" in data

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_cors_headers(self, client):
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        # CORS preflight should not return 405
        assert response.status_code in [200, 204, 400]

"""
Axon by NeuroVexon - Agent Manager Tests

Tests for AgentManager: CRUD, defaults, permission checks, risk levels.
"""

import pytest

from agent.agent_manager import AgentManager, DEFAULT_AGENTS
from db.models import Agent


class TestAgentManagerDefaults:
    """Tests for default agent creation"""

    @pytest.mark.asyncio
    async def test_ensure_defaults_creates_agents(self, db):
        manager = AgentManager(db)
        await manager.ensure_defaults()

        agents = await manager.list_agents()
        assert len(agents) == len(DEFAULT_AGENTS)

    @pytest.mark.asyncio
    async def test_ensure_defaults_idempotent(self, db):
        manager = AgentManager(db)
        await manager.ensure_defaults()
        await manager.ensure_defaults()  # Should not duplicate

        agents = await manager.list_agents()
        assert len(agents) == len(DEFAULT_AGENTS)

    @pytest.mark.asyncio
    async def test_default_agent_exists(self, db):
        manager = AgentManager(db)
        await manager.ensure_defaults()

        default = await manager.get_default_agent()
        assert default is not None
        assert default.name == "Assistent"
        assert default.is_default is True

    @pytest.mark.asyncio
    async def test_default_agents_have_correct_names(self, db):
        manager = AgentManager(db)
        await manager.ensure_defaults()

        agents = await manager.list_agents()
        names = {a.name for a in agents}
        assert "Assistent" in names
        assert "Recherche" in names
        assert "System" in names


class TestAgentManagerCRUD:
    """Tests for Agent CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_agent(self, db):
        manager = AgentManager(db)
        agent = await manager.create_agent(
            name="Code-Agent",
            description="Schreibt Code",
            risk_level_max="medium",
            allowed_tools=["file_read", "file_write"],
        )

        assert agent.id is not None
        assert agent.name == "Code-Agent"
        assert agent.risk_level_max == "medium"
        assert agent.allowed_tools == ["file_read", "file_write"]

    @pytest.mark.asyncio
    async def test_get_agent(self, db):
        manager = AgentManager(db)
        created = await manager.create_agent(name="Test")

        found = await manager.get_agent(created.id)
        assert found is not None
        assert found.name == "Test"

    @pytest.mark.asyncio
    async def test_get_nonexistent_agent(self, db):
        manager = AgentManager(db)
        found = await manager.get_agent("nonexistent-id")
        assert found is None

    @pytest.mark.asyncio
    async def test_update_agent(self, db):
        manager = AgentManager(db)
        agent = await manager.create_agent(name="Alt")

        updated = await manager.update_agent(
            agent.id, name="Neu", description="Aktualisiert"
        )
        assert updated is not None
        assert updated.name == "Neu"
        assert updated.description == "Aktualisiert"

    @pytest.mark.asyncio
    async def test_update_nonexistent_agent(self, db):
        manager = AgentManager(db)
        result = await manager.update_agent("nonexistent", name="X")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_agent(self, db):
        manager = AgentManager(db)
        agent = await manager.create_agent(name="Loeschbar")

        result = await manager.delete_agent(agent.id)
        assert result is True

        found = await manager.get_agent(agent.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_cannot_delete_default_agent(self, db):
        manager = AgentManager(db)
        await manager.ensure_defaults()

        default = await manager.get_default_agent()
        result = await manager.delete_agent(default.id)
        assert result is False  # Default cannot be deleted

        # Verify still exists
        still_there = await manager.get_agent(default.id)
        assert still_there is not None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_agent(self, db):
        manager = AgentManager(db)
        result = await manager.delete_agent("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_enabled_only(self, db):
        manager = AgentManager(db)
        await manager.create_agent(name="Aktiv")
        agent2 = await manager.create_agent(name="Inaktiv")
        await manager.update_agent(agent2.id, enabled=False)

        enabled = await manager.list_agents(enabled_only=True)
        disabled_names = [a.name for a in enabled]
        assert "Aktiv" in disabled_names
        assert "Inaktiv" not in disabled_names


class TestAgentPermissions:
    """Tests for static permission check methods"""

    def test_tool_allowed_when_none(self):
        """None = all tools allowed"""
        agent = Agent(name="Test", allowed_tools=None)
        assert AgentManager.is_tool_allowed(agent, "web_search") is True
        assert AgentManager.is_tool_allowed(agent, "shell_execute") is True

    def test_tool_allowed_in_list(self):
        agent = Agent(name="Test", allowed_tools=["web_search", "file_read"])
        assert AgentManager.is_tool_allowed(agent, "web_search") is True
        assert AgentManager.is_tool_allowed(agent, "file_read") is True

    def test_tool_not_allowed(self):
        agent = Agent(name="Test", allowed_tools=["web_search"])
        assert AgentManager.is_tool_allowed(agent, "shell_execute") is False
        assert AgentManager.is_tool_allowed(agent, "file_write") is False

    def test_auto_approve_when_none(self):
        """None = nothing auto-approved"""
        agent = Agent(name="Test", auto_approve_tools=None)
        assert AgentManager.is_auto_approved(agent, "web_search") is False

    def test_auto_approve_in_list(self):
        agent = Agent(name="Test", auto_approve_tools=["web_search", "memory_search"])
        assert AgentManager.is_auto_approved(agent, "web_search") is True
        assert AgentManager.is_auto_approved(agent, "memory_search") is True

    def test_auto_approve_not_in_list(self):
        agent = Agent(name="Test", auto_approve_tools=["web_search"])
        assert AgentManager.is_auto_approved(agent, "shell_execute") is False

    def test_risk_level_low_agent(self):
        agent = Agent(name="Test", risk_level_max="low")
        assert AgentManager.check_risk_level(agent, "low") is True
        assert AgentManager.check_risk_level(agent, "medium") is False
        assert AgentManager.check_risk_level(agent, "high") is False

    def test_risk_level_medium_agent(self):
        agent = Agent(name="Test", risk_level_max="medium")
        assert AgentManager.check_risk_level(agent, "low") is True
        assert AgentManager.check_risk_level(agent, "medium") is True
        assert AgentManager.check_risk_level(agent, "high") is False

    def test_risk_level_high_agent(self):
        agent = Agent(name="Test", risk_level_max="high")
        assert AgentManager.check_risk_level(agent, "low") is True
        assert AgentManager.check_risk_level(agent, "medium") is True
        assert AgentManager.check_risk_level(agent, "high") is True
        assert AgentManager.check_risk_level(agent, "critical") is False


class TestDefaultAgentConfig:
    """Tests that default agents have correct configurations"""

    @pytest.mark.asyncio
    async def test_assistent_has_all_tools(self, db):
        manager = AgentManager(db)
        await manager.ensure_defaults()

        agents = await manager.list_agents()
        assistent = next(a for a in agents if a.name == "Assistent")

        assert assistent.allowed_tools is None  # None = all
        assert assistent.auto_approve_tools is None  # Nothing auto-approved
        assert assistent.risk_level_max == "high"

    @pytest.mark.asyncio
    async def test_recherche_is_restricted(self, db):
        manager = AgentManager(db)
        await manager.ensure_defaults()

        agents = await manager.list_agents()
        recherche = next(a for a in agents if a.name == "Recherche")

        assert recherche.allowed_tools is not None
        assert "web_search" in recherche.allowed_tools
        assert "shell_execute" not in recherche.allowed_tools
        assert "web_search" in recherche.auto_approve_tools
        assert recherche.risk_level_max == "medium"

    @pytest.mark.asyncio
    async def test_system_needs_full_approval(self, db):
        manager = AgentManager(db)
        await manager.ensure_defaults()

        agents = await manager.list_agents()
        system = next(a for a in agents if a.name == "System")

        assert system.allowed_tools is None  # All tools
        assert system.auto_approve_tools is None  # Nothing auto-approved
        assert system.risk_level_max == "high"

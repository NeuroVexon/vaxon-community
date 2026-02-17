"""
Axon by NeuroVexon - Database Model Tests

Tests for all SQLAlchemy models: creation, relationships, defaults, constraints.
"""

import pytest
from datetime import datetime

from db.models import (
    Conversation, Message, AuditLog, Memory, Agent, ScheduledTask, Workflow, Settings,
    generate_uuid,
)


class TestGenerateUUID:
    """Tests for UUID generation"""

    def test_returns_string(self):
        uid = generate_uuid()
        assert isinstance(uid, str)

    def test_uuid_format(self):
        uid = generate_uuid()
        parts = uid.split("-")
        assert len(parts) == 5
        assert len(uid) == 36

    def test_unique(self):
        uuids = {generate_uuid() for _ in range(100)}
        assert len(uuids) == 100


class TestConversationModel:
    """Tests for Conversation model"""

    @pytest.mark.asyncio
    async def test_create_conversation(self, db):
        conv = Conversation(title="Test Chat")
        db.add(conv)
        await db.flush()

        assert conv.id is not None
        assert len(conv.id) == 36
        assert conv.title == "Test Chat"
        assert conv.created_at is not None

    @pytest.mark.asyncio
    async def test_conversation_with_messages(self, db):
        conv = Conversation(title="Chat mit Messages")
        db.add(conv)
        await db.flush()

        msg = Message(
            conversation_id=conv.id,
            role="user",
            content="Hallo Axon"
        )
        db.add(msg)
        await db.flush()

        assert msg.conversation_id == conv.id

    @pytest.mark.asyncio
    async def test_conversation_defaults(self, db):
        conv = Conversation()
        db.add(conv)
        await db.flush()

        assert conv.title is None
        assert conv.system_prompt is None
        assert isinstance(conv.created_at, datetime)


class TestMessageModel:
    """Tests for Message model"""

    @pytest.mark.asyncio
    async def test_create_message(self, db):
        conv = Conversation(title="Test")
        db.add(conv)
        await db.flush()

        msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content="Ich bin Axon."
        )
        db.add(msg)
        await db.flush()

        assert msg.id is not None
        assert msg.role == "assistant"
        assert msg.content == "Ich bin Axon."
        assert msg.tool_calls is None
        assert msg.tool_results is None

    @pytest.mark.asyncio
    async def test_message_with_tool_calls(self, db):
        conv = Conversation()
        db.add(conv)
        await db.flush()

        msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content="Suche...",
            tool_calls=[{"name": "web_search", "arguments": {"query": "test"}}],
            tool_results=[{"result": "Ergebnis"}]
        )
        db.add(msg)
        await db.flush()

        assert msg.tool_calls[0]["name"] == "web_search"
        assert msg.tool_results[0]["result"] == "Ergebnis"


class TestAuditLogModel:
    """Tests for AuditLog model"""

    @pytest.mark.asyncio
    async def test_create_audit_log(self, db):
        conv = Conversation()
        db.add(conv)
        await db.flush()

        log = AuditLog(
            conversation_id=conv.id,
            event_type="tool_executed",
            tool_name="web_search",
            tool_params={"query": "Python"},
            result="3 Ergebnisse",
            execution_time_ms=150
        )
        db.add(log)
        await db.flush()

        assert log.id is not None
        assert log.event_type == "tool_executed"
        assert log.tool_name == "web_search"
        assert log.execution_time_ms == 150


class TestMemoryModel:
    """Tests for Memory model"""

    @pytest.mark.asyncio
    async def test_create_memory(self, db):
        mem = Memory(
            key="Lieblings-Sprache",
            content="Python",
            source="user",
            category="Technik"
        )
        db.add(mem)
        await db.flush()

        assert mem.id is not None
        assert mem.key == "Lieblings-Sprache"
        assert mem.content == "Python"
        assert mem.category == "Technik"

    @pytest.mark.asyncio
    async def test_memory_defaults(self, db):
        mem = Memory(key="Test", content="Wert")
        db.add(mem)
        await db.flush()

        assert mem.source == "user"
        assert mem.category is None
        if hasattr(mem, "embedding"):
            assert mem.embedding is None


class TestAgentModel:
    """Tests for Agent model"""

    @pytest.mark.asyncio
    async def test_create_agent(self, db):
        agent = Agent(
            name="Test-Agent",
            description="Ein Test-Agent",
            risk_level_max="medium",
            allowed_tools=["web_search", "file_read"],
            auto_approve_tools=["web_search"]
        )
        db.add(agent)
        await db.flush()

        assert agent.id is not None
        assert agent.name == "Test-Agent"
        assert agent.allowed_tools == ["web_search", "file_read"]
        assert agent.auto_approve_tools == ["web_search"]

    @pytest.mark.asyncio
    async def test_agent_defaults(self, db):
        agent = Agent(name="Default-Test")
        db.add(agent)
        await db.flush()

        assert agent.enabled is True
        assert agent.is_default is False
        assert agent.risk_level_max == "high"
        assert agent.allowed_tools is None
        assert agent.auto_approve_tools is None


class TestScheduledTaskModel:
    """Tests for ScheduledTask model"""

    @pytest.mark.asyncio
    async def test_create_scheduled_task(self, db):
        task = ScheduledTask(
            name="Taeglich 9 Uhr",
            cron_expression="0 9 * * *",
            prompt="Zeige ungelesene E-Mails",
            approval_required=True,
            notification_channel="telegram"
        )
        db.add(task)
        await db.flush()

        assert task.id is not None
        assert task.cron_expression == "0 9 * * *"
        assert task.approval_required is True
        assert task.max_retries == 1


class TestWorkflowModel:
    """Tests for Workflow model"""

    @pytest.mark.asyncio
    async def test_create_workflow(self, db):
        wf = Workflow(
            name="Tagesstart",
            description="Morgenroutine",
            trigger_phrase="Tagesstart",
            steps=[
                {"order": 1, "prompt": "Zeige E-Mails", "store_as": "mails"},
                {"order": 2, "prompt": "Fasse {{mails}} zusammen", "store_as": "summary"}
            ],
            approval_mode="once_at_start"
        )
        db.add(wf)
        await db.flush()

        assert wf.id is not None
        assert len(wf.steps) == 2
        assert wf.steps[0]["store_as"] == "mails"
        assert wf.approval_mode == "once_at_start"


class TestSettingsModel:
    """Tests for Settings model"""

    @pytest.mark.asyncio
    async def test_create_setting(self, db):
        setting = Settings(key="theme", value="dark")
        db.add(setting)
        await db.flush()

        assert setting.id is not None
        assert setting.key == "theme"
        assert setting.value == "dark"

"""
Axon by NeuroVexon - Orchestrator Tests

Tests for AgentOrchestrator: agent loop, tool approval flow, auto-approve,
blocked tools, max iterations, error handling, event types.
All LLM calls are mocked — no Ollama/API dependency needed.
"""

import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.orchestrator import AgentOrchestrator
from agent.tool_registry import ToolRegistry, ToolDefinition, RiskLevel
from agent.permission_manager import PermissionManager, PermissionScope
from llm.provider import BaseLLMProvider, ChatMessage, ToolCall, LLMResponse
from db.models import Agent


# ============================================================
# Helpers
# ============================================================


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM that returns pre-configured responses"""

    def __init__(self, responses: list[LLMResponse]):
        self._responses = list(responses)
        self._call_count = 0

    async def chat(self, messages, tools=None, stream=False):
        if self._call_count < len(self._responses):
            resp = self._responses[self._call_count]
            self._call_count += 1
            return resp
        return LLMResponse(content="No more responses", tool_calls=None)

    async def chat_stream(self, messages, tools=None):
        yield "stream not used in tests"

    async def health_check(self):
        return True


def make_tool_call(name: str, params: dict = None) -> ToolCall:
    return ToolCall(id=f"call_{name}", name=name, parameters=params or {})


async def collect_events(orchestrator, session_id, messages, on_approval=None):
    """Helper to collect all yielded events from process_message"""
    if on_approval is None:
        on_approval = AsyncMock(return_value=PermissionScope.ONCE)
    events = []
    async for event in orchestrator.process_message(
        session_id=session_id, messages=messages, on_approval_needed=on_approval
    ):
        events.append(event)
    return events


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def test_registry():
    """Create a minimal ToolRegistry for testing"""
    registry = ToolRegistry.__new__(ToolRegistry)
    registry._tools = {}

    # Low-risk, no approval needed (like web_search)
    registry.register(
        ToolDefinition(
            name="web_search",
            description="Search the web",
            description_de="Websuche",
            parameters={"query": {"type": "string", "required": True}},
            risk_level=RiskLevel.LOW,
            requires_approval=False,
        )
    )

    # Medium-risk, needs approval
    registry.register(
        ToolDefinition(
            name="file_read",
            description="Read a file",
            description_de="Datei lesen",
            parameters={"path": {"type": "string", "required": True}},
            risk_level=RiskLevel.MEDIUM,
            requires_approval=True,
        )
    )

    # High-risk, needs approval
    registry.register(
        ToolDefinition(
            name="shell_execute",
            description="Execute shell command",
            description_de="Shell-Befehl ausfuehren",
            parameters={"command": {"type": "string", "required": True}},
            risk_level=RiskLevel.HIGH,
            requires_approval=True,
        )
    )

    # Low-risk, no approval (like memory tools)
    registry.register(
        ToolDefinition(
            name="memory_save",
            description="Save to memory",
            description_de="Im Gedaechtnis speichern",
            parameters={"key": {"type": "string", "required": True}},
            risk_level=RiskLevel.LOW,
            requires_approval=False,
        )
    )

    return registry


@pytest.fixture
def test_permissions():
    """Fresh PermissionManager for each test"""
    return PermissionManager()


@pytest.fixture
def mock_agent_default():
    """Agent with all tools allowed, nothing auto-approved"""
    agent = MagicMock(spec=Agent)
    agent.name = "Assistent"
    agent.allowed_tools = None  # None = all tools allowed
    agent.auto_approve_tools = None
    agent.risk_level_max = "high"
    return agent


@pytest.fixture
def mock_agent_recherche():
    """Agent with restricted tools, web_search auto-approved"""
    agent = MagicMock(spec=Agent)
    agent.name = "Recherche"
    agent.allowed_tools = ["web_search", "web_fetch", "file_read"]
    agent.auto_approve_tools = ["web_search"]
    agent.risk_level_max = "medium"
    return agent


@pytest.fixture
def mock_agent_locked():
    """Agent with very restricted permissions"""
    agent = MagicMock(spec=Agent)
    agent.name = "Minimal"
    agent.allowed_tools = ["web_search"]
    agent.auto_approve_tools = []
    agent.risk_level_max = "low"
    return agent


# ============================================================
# Basic Flow — No Tool Calls
# ============================================================


class TestOrchestratorBasicFlow:
    """Tests for simple LLM responses without tools"""

    @pytest.mark.asyncio
    async def test_text_response_yields_text_and_done(
        self, db, test_registry, test_permissions
    ):
        llm = MockLLMProvider(
            [LLMResponse(content="Hallo, ich bin Axon!", tool_calls=None)]
        )
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        events = await collect_events(
            orch, "sess-1", [ChatMessage(role="user", content="Hallo")]
        )

        assert len(events) == 2
        assert events[0]["type"] == "text"
        assert events[0]["content"] == "Hallo, ich bin Axon!"
        assert events[1]["type"] == "done"

    @pytest.mark.asyncio
    async def test_empty_content_yields_only_done(
        self, db, test_registry, test_permissions
    ):
        llm = MockLLMProvider([LLMResponse(content=None, tool_calls=None)])
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        events = await collect_events(
            orch, "sess-2", [ChatMessage(role="user", content="Test")]
        )

        assert len(events) == 1
        assert events[0]["type"] == "done"

    @pytest.mark.asyncio
    async def test_llm_called_with_tools(self, db, test_registry, test_permissions):
        llm = MockLLMProvider([LLMResponse(content="OK", tool_calls=None)])
        llm.chat = AsyncMock(return_value=LLMResponse(content="OK", tool_calls=None))
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        await collect_events(orch, "sess-3", [ChatMessage(role="user", content="Test")])

        llm.chat.assert_called_once()
        call_kwargs = llm.chat.call_args
        assert call_kwargs[1]["tools"] is not None


# ============================================================
# Auto-Approved Tools (requires_approval=False)
# ============================================================


class TestOrchestratorAutoApprove:
    """Tests for tools that skip approval (requires_approval=False)"""

    @pytest.mark.asyncio
    async def test_auto_approved_tool_executes(
        self, db, test_registry, test_permissions
    ):
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("web_search", {"query": "Python"})],
                ),
                LLMResponse(content="Hier sind die Ergebnisse.", tool_calls=None),
            ]
        )

        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "3 Ergebnisse gefunden"
            events = await collect_events(
                orch, "sess-auto-1", [ChatMessage(role="user", content="Suche Python")]
            )

        # Should have: tool_result, text, done
        types = [e["type"] for e in events]
        assert "tool_result" in types
        assert "done" in types
        # No tool_request since auto-approved
        assert "tool_request" not in types

    @pytest.mark.asyncio
    async def test_auto_approved_tool_result_has_execution_time(
        self, db, test_registry, test_permissions
    ):
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("memory_save", {"key": "test"})],
                ),
                LLMResponse(content="Gespeichert.", tool_calls=None),
            ]
        )

        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "Memory saved"
            events = await collect_events(
                orch, "sess-auto-2", [ChatMessage(role="user", content="Merk dir das")]
            )

        tool_result = next(e for e in events if e["type"] == "tool_result")
        assert "execution_time_ms" in tool_result
        assert isinstance(tool_result["execution_time_ms"], int)

    @pytest.mark.asyncio
    async def test_auto_approved_tool_error_yields_tool_error(
        self, db, test_registry, test_permissions
    ):
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("web_search", {"query": "fail"})],
                ),
                LLMResponse(content="Fehler aufgetreten.", tool_calls=None),
            ]
        )

        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.side_effect = Exception("Network error")
            events = await collect_events(
                orch, "sess-auto-err", [ChatMessage(role="user", content="Suche")]
            )

        types = [e["type"] for e in events]
        assert "tool_error" in types
        error_event = next(e for e in events if e["type"] == "tool_error")
        assert "Network error" in error_event["error"]


# ============================================================
# Approval-Required Tools
# ============================================================


class TestOrchestratorApprovalFlow:
    """Tests for tools that require user approval"""

    @pytest.mark.asyncio
    async def test_approval_flow_approved(self, db, test_registry, test_permissions):
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("file_read", {"path": "/tmp/test.txt"})],
                ),
                LLMResponse(content="Datei gelesen.", tool_calls=None),
            ]
        )

        on_approval = AsyncMock(return_value=PermissionScope.ONCE)
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "file content"
            events = await collect_events(
                orch,
                "sess-appr-1",
                [ChatMessage(role="user", content="Lies die Datei")],
                on_approval=on_approval,
            )

        types = [e["type"] for e in events]
        assert "tool_request" in types
        assert "tool_result" in types
        assert "done" in types

        # Verify approval was called
        on_approval.assert_called_once()

    @pytest.mark.asyncio
    async def test_approval_flow_rejected(self, db, test_registry, test_permissions):
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("file_read", {"path": "/etc/secret"})],
                ),
                LLMResponse(content="OK, abgelehnt.", tool_calls=None),
            ]
        )

        on_approval = AsyncMock(return_value=None)  # None = rejected
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        events = await collect_events(
            orch,
            "sess-reject-1",
            [ChatMessage(role="user", content="Lies die Datei")],
            on_approval=on_approval,
        )

        types = [e["type"] for e in events]
        assert "tool_request" in types
        assert "tool_rejected" in types
        # Tool should NOT execute
        assert "tool_result" not in types

    @pytest.mark.asyncio
    async def test_tool_request_has_approval_id(
        self, db, test_registry, test_permissions
    ):
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("shell_execute", {"command": "ls"})],
                ),
                LLMResponse(content="Done.", tool_calls=None),
            ]
        )

        on_approval = AsyncMock(return_value=PermissionScope.ONCE)
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "output"
            events = await collect_events(
                orch,
                "sess-appr-id",
                [ChatMessage(role="user", content="Fuehre ls aus")],
                on_approval=on_approval,
            )

        tool_request = next(e for e in events if e["type"] == "tool_request")
        assert "approval_id" in tool_request
        assert len(tool_request["approval_id"]) == 8  # UUID[:8]

    @pytest.mark.asyncio
    async def test_tool_request_has_risk_level(
        self, db, test_registry, test_permissions
    ):
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("shell_execute", {"command": "date"})],
                ),
                LLMResponse(content="Done.", tool_calls=None),
            ]
        )

        on_approval = AsyncMock(return_value=PermissionScope.ONCE)
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "2026-01-01"
            events = await collect_events(
                orch,
                "sess-risk",
                [ChatMessage(role="user", content="Datum?")],
                on_approval=on_approval,
            )

        tool_request = next(e for e in events if e["type"] == "tool_request")
        assert tool_request["risk_level"] == "high"

    @pytest.mark.asyncio
    async def test_session_permission_skips_second_approval(
        self, db, test_registry, test_permissions
    ):
        """After granting SESSION permission, second call should not request approval"""
        # Pre-grant session permission
        test_permissions.grant_permission(
            "sess-perm", "file_read", {"path": "x"}, PermissionScope.SESSION
        )

        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("file_read", {"path": "y"})],
                ),
                LLMResponse(content="OK.", tool_calls=None),
            ]
        )

        on_approval = AsyncMock(return_value=PermissionScope.ONCE)
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "content"
            events = await collect_events(
                orch,
                "sess-perm",
                [ChatMessage(role="user", content="Lies")],
                on_approval=on_approval,
            )

        types = [e["type"] for e in events]
        # Should NOT have tool_request because session permission already granted
        assert "tool_request" not in types
        assert "tool_result" in types
        on_approval.assert_not_called()


# ============================================================
# Unknown / Blocked Tools
# ============================================================


class TestOrchestratorUnknownAndBlocked:
    """Tests for unknown tools and blocked tools"""

    @pytest.mark.asyncio
    async def test_unknown_tool_yields_tool_error(
        self, db, test_registry, test_permissions
    ):
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None, tool_calls=[make_tool_call("nonexistent_tool", {})]
                ),
                LLMResponse(content="Hmm.", tool_calls=None),
            ]
        )

        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)
        events = await collect_events(
            orch, "sess-unknown", [ChatMessage(role="user", content="Test")]
        )

        types = [e["type"] for e in events]
        assert "tool_error" in types
        error_event = next(e for e in events if e["type"] == "tool_error")
        assert "Unknown tool" in error_event["error"]

    @pytest.mark.asyncio
    async def test_blocked_tool_yields_tool_blocked(
        self, db, test_registry, test_permissions
    ):
        # Block file_read
        test_permissions.grant_permission(
            "sess-block", "file_read", {"path": "/bad"}, PermissionScope.NEVER
        )

        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("file_read", {"path": "/bad"})],
                ),
                LLMResponse(content="Blockiert.", tool_calls=None),
            ]
        )

        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)
        events = await collect_events(
            orch, "sess-block", [ChatMessage(role="user", content="Lies")]
        )

        types = [e["type"] for e in events]
        assert "tool_blocked" in types


# ============================================================
# Agent-Level Permissions
# ============================================================


class TestOrchestratorAgentPermissions:
    """Tests for per-agent tool restrictions"""

    @pytest.mark.asyncio
    async def test_agent_not_allowed_tool(
        self, db, test_registry, test_permissions, mock_agent_locked
    ):
        """Locked agent cannot use file_read"""
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("file_read", {"path": "/tmp/x"})],
                ),
                LLMResponse(content="Kein Zugang.", tool_calls=None),
            ]
        )

        orch = AgentOrchestrator(
            llm, db, test_registry, test_permissions, agent=mock_agent_locked
        )
        events = await collect_events(
            orch, "sess-locked", [ChatMessage(role="user", content="Lies")]
        )

        types = [e["type"] for e in events]
        assert "tool_error" in types
        # Should NOT execute or request approval
        assert "tool_result" not in types
        assert "tool_request" not in types

    @pytest.mark.asyncio
    async def test_agent_auto_approved_tool(
        self, db, test_registry, test_permissions, mock_agent_recherche
    ):
        """Recherche agent has web_search auto-approved"""
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("web_search", {"query": "test"})],
                ),
                LLMResponse(content="Ergebnisse.", tool_calls=None),
            ]
        )

        orch = AgentOrchestrator(
            llm, db, test_registry, test_permissions, agent=mock_agent_recherche
        )

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "search results"
            events = await collect_events(
                orch, "sess-rech-auto", [ChatMessage(role="user", content="Suche")]
            )

        types = [e["type"] for e in events]
        # Auto-approved → no tool_request
        assert "tool_request" not in types
        assert "tool_result" in types

    @pytest.mark.asyncio
    async def test_default_agent_allows_all(
        self, db, test_registry, test_permissions, mock_agent_default
    ):
        """Default agent with allowed_tools=None allows all tools"""
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("shell_execute", {"command": "ls"})],
                ),
                LLMResponse(content="Output.", tool_calls=None),
            ]
        )

        on_approval = AsyncMock(return_value=PermissionScope.ONCE)
        orch = AgentOrchestrator(
            llm, db, test_registry, test_permissions, agent=mock_agent_default
        )

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "files"
            events = await collect_events(
                orch,
                "sess-default",
                [ChatMessage(role="user", content="ls")],
                on_approval=on_approval,
            )

        types = [e["type"] for e in events]
        # Should be allowed (needs approval though since shell_execute requires it)
        assert "tool_request" in types
        assert "tool_result" in types

    @pytest.mark.asyncio
    async def test_no_agent_allows_all(self, db, test_registry, test_permissions):
        """Without an agent, all tools are allowed"""
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("shell_execute", {"command": "ls"})],
                ),
                LLMResponse(content="OK.", tool_calls=None),
            ]
        )

        on_approval = AsyncMock(return_value=PermissionScope.ONCE)
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions, agent=None)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "output"
            events = await collect_events(
                orch,
                "sess-no-agent",
                [ChatMessage(role="user", content="ls")],
                on_approval=on_approval,
            )

        types = [e["type"] for e in events]
        assert "tool_result" in types


# ============================================================
# Max Iterations & Multiple Tool Calls
# ============================================================


class TestOrchestratorIterations:
    """Tests for iteration limits and multi-tool scenarios"""

    @pytest.mark.asyncio
    async def test_max_iterations_warning(self, db, test_registry, test_permissions):
        """If LLM keeps calling tools, max_iterations stops the loop"""
        # LLM always returns a tool call — never a final text
        responses = [
            LLMResponse(
                content=None,
                tool_calls=[make_tool_call("web_search", {"query": f"iter-{i}"})],
            )
            for i in range(15)
        ]
        llm = MockLLMProvider(responses)
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "result"
            events = await collect_events(
                orch,
                "sess-maxiter",
                [ChatMessage(role="user", content="Endlosschleife")],
            )

        types = [e["type"] for e in events]
        assert "warning" in types
        assert "done" in types
        warning_event = next(e for e in events if e["type"] == "warning")
        assert "Maximum" in warning_event["message"]

    @pytest.mark.asyncio
    async def test_custom_max_iterations(self, db, test_registry, test_permissions):
        """Respect custom max_tool_iterations parameter"""
        responses = [
            LLMResponse(
                content=None,
                tool_calls=[make_tool_call("web_search", {"query": f"iter-{i}"})],
            )
            for i in range(10)
        ]
        llm = MockLLMProvider(responses)
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "ok"
            events = []
            async for event in orch.process_message(
                session_id="sess-custom-iter",
                messages=[ChatMessage(role="user", content="Loop")],
                on_approval_needed=AsyncMock(return_value=PermissionScope.ONCE),
                max_tool_iterations=3,
            ):
                events.append(event)

        # Should have exactly 3 tool_result events (plus warning + done)
        tool_results = [e for e in events if e["type"] == "tool_result"]
        assert len(tool_results) == 3

    @pytest.mark.asyncio
    async def test_multiple_tool_calls_in_one_response(
        self, db, test_registry, test_permissions
    ):
        """LLM returns multiple tool calls in a single response"""
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content="Ich suche und lese...",
                    tool_calls=[
                        make_tool_call("web_search", {"query": "Python"}),
                        make_tool_call("memory_save", {"key": "search_done"}),
                    ],
                ),
                LLMResponse(content="Fertig!", tool_calls=None),
            ]
        )

        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "ok"
            events = await collect_events(
                orch, "sess-multi", [ChatMessage(role="user", content="Such und merk")]
            )

        tool_results = [e for e in events if e["type"] == "tool_result"]
        assert len(tool_results) == 2

    @pytest.mark.asyncio
    async def test_partial_text_with_tool_calls(
        self, db, test_registry, test_permissions
    ):
        """LLM response has both content and tool_calls — text is yielded after tools"""
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content="Ich suche jetzt...",
                    tool_calls=[make_tool_call("web_search", {"query": "test"})],
                ),
                LLMResponse(content="Erledigt.", tool_calls=None),
            ]
        )

        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "found"
            events = await collect_events(
                orch, "sess-partial", [ChatMessage(role="user", content="Suche")]
            )

        [e["type"] for e in events]
        # Partial text should be yielded
        text_events = [e for e in events if e["type"] == "text"]
        assert len(text_events) >= 1


# ============================================================
# Tool Execution Errors
# ============================================================


class TestOrchestratorToolErrors:
    """Tests for error handling during tool execution"""

    @pytest.mark.asyncio
    async def test_tool_execution_error(self, db, test_registry, test_permissions):
        """ToolExecutionError is caught and yields tool_error"""
        from agent.tool_handlers import ToolExecutionError

        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("file_read", {"path": "/forbidden"})],
                ),
                LLMResponse(content="Fehler.", tool_calls=None),
            ]
        )

        on_approval = AsyncMock(return_value=PermissionScope.ONCE)
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.side_effect = ToolExecutionError("Access denied")
            events = await collect_events(
                orch,
                "sess-err-1",
                [ChatMessage(role="user", content="Lies")],
                on_approval=on_approval,
            )

        types = [e["type"] for e in events]
        assert "tool_error" in types
        error_event = next(e for e in events if e["type"] == "tool_error")
        assert "Access denied" in error_event["error"]

    @pytest.mark.asyncio
    async def test_unexpected_error(self, db, test_registry, test_permissions):
        """Unexpected exceptions are caught and yield tool_error"""
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("file_read", {"path": "/crash"})],
                ),
                LLMResponse(content="Crash.", tool_calls=None),
            ]
        )

        on_approval = AsyncMock(return_value=PermissionScope.ONCE)
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.side_effect = RuntimeError("Unexpected crash")
            events = await collect_events(
                orch,
                "sess-err-2",
                [ChatMessage(role="user", content="Crash")],
                on_approval=on_approval,
            )

        types = [e["type"] for e in events]
        assert "tool_error" in types
        error_event = next(e for e in events if e["type"] == "tool_error")
        assert "Unexpected" in error_event["error"]


# ============================================================
# Audit Logging
# ============================================================


class TestOrchestratorAuditLogging:
    """Tests that the orchestrator logs events to audit trail"""

    @pytest.mark.asyncio
    async def test_tool_request_logged(self, db, test_registry, test_permissions):
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("web_search", {"query": "audit test"})],
                ),
                LLMResponse(content="OK.", tool_calls=None),
            ]
        )

        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "result"
            with patch.object(
                orch.audit, "log_tool_request", new_callable=AsyncMock
            ) as mock_log:
                mock_log.return_value = MagicMock()
                await collect_events(
                    orch, "sess-audit-1", [ChatMessage(role="user", content="Test")]
                )
                mock_log.assert_called_once_with(
                    "sess-audit-1", "web_search", {"query": "audit test"}
                )

    @pytest.mark.asyncio
    async def test_tool_execution_logged(self, db, test_registry, test_permissions):
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("web_search", {"query": "log test"})],
                ),
                LLMResponse(content="OK.", tool_calls=None),
            ]
        )

        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.return_value = "logged result"
            with patch.object(
                orch.audit, "log_tool_execution", new_callable=AsyncMock
            ) as mock_log:
                mock_log.return_value = MagicMock()
                await collect_events(
                    orch, "sess-audit-2", [ChatMessage(role="user", content="Test")]
                )
                mock_log.assert_called_once()
                call_args = mock_log.call_args[0]
                assert call_args[0] == "sess-audit-2"  # session_id
                assert call_args[1] == "web_search"  # tool_name

    @pytest.mark.asyncio
    async def test_rejection_logged(self, db, test_registry, test_permissions):
        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("file_read", {"path": "/x"})],
                ),
                LLMResponse(content="Abgelehnt.", tool_calls=None),
            ]
        )

        on_approval = AsyncMock(return_value=None)
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch.object(
            orch.audit, "log_tool_rejection", new_callable=AsyncMock
        ) as mock_log:
            mock_log.return_value = MagicMock()
            await collect_events(
                orch,
                "sess-audit-rej",
                [ChatMessage(role="user", content="Lies")],
                on_approval=on_approval,
            )
            mock_log.assert_called_once()
            call_args = mock_log.call_args[0]
            assert call_args[1] == "file_read"
            assert call_args[3] == "rejected"

    @pytest.mark.asyncio
    async def test_failure_logged(self, db, test_registry, test_permissions):
        from agent.tool_handlers import ToolExecutionError

        llm = MockLLMProvider(
            [
                LLMResponse(
                    content=None,
                    tool_calls=[make_tool_call("file_read", {"path": "/fail"})],
                ),
                LLMResponse(content="Fehler.", tool_calls=None),
            ]
        )

        on_approval = AsyncMock(return_value=PermissionScope.ONCE)
        orch = AgentOrchestrator(llm, db, test_registry, test_permissions)

        with patch(
            "agent.orchestrator.execute_tool", new_callable=AsyncMock
        ) as mock_exec:
            mock_exec.side_effect = ToolExecutionError("Disk error")
            with patch.object(
                orch.audit, "log_tool_failure", new_callable=AsyncMock
            ) as mock_log:
                mock_log.return_value = MagicMock()
                await collect_events(
                    orch,
                    "sess-audit-fail",
                    [ChatMessage(role="user", content="Lies")],
                    on_approval=on_approval,
                )
                mock_log.assert_called_once()
                call_args = mock_log.call_args[0]
                assert "Disk error" in call_args[3]

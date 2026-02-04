"""
Axon by NeuroVexon - Tool Tests
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tool_registry import ToolRegistry, RiskLevel
from agent.permission_manager import PermissionManager, PermissionScope


class TestToolRegistry:
    """Tests for ToolRegistry"""

    def test_registry_has_builtin_tools(self):
        registry = ToolRegistry()
        tools = registry.list_tools()

        tool_names = [t.name for t in tools]
        assert "file_read" in tool_names
        assert "file_write" in tool_names
        assert "web_search" in tool_names
        assert "shell_execute" in tool_names

    def test_get_tool(self):
        registry = ToolRegistry()
        tool = registry.get("file_read")

        assert tool is not None
        assert tool.name == "file_read"
        assert tool.risk_level == RiskLevel.MEDIUM

    def test_get_unknown_tool(self):
        registry = ToolRegistry()
        tool = registry.get("unknown_tool")

        assert tool is None

    def test_tools_for_llm_format(self):
        registry = ToolRegistry()
        llm_tools = registry.get_tools_for_llm()

        assert isinstance(llm_tools, list)
        assert len(llm_tools) > 0

        for tool in llm_tools:
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]


class TestPermissionManager:
    """Tests for PermissionManager"""

    def test_no_permission_by_default(self):
        manager = PermissionManager()

        has_perm = manager.check_permission(
            "session-1",
            "file_read",
            {"path": "/test.txt"}
        )

        assert has_perm is False

    def test_grant_once_permission(self):
        manager = PermissionManager()

        manager.grant_permission(
            "session-1",
            "file_read",
            {"path": "/test.txt"},
            PermissionScope.ONCE
        )

        # Should have permission for exact params
        has_perm = manager.check_permission(
            "session-1",
            "file_read",
            {"path": "/test.txt"}
        )
        assert has_perm is True

        # Should NOT have permission for different params
        has_perm_other = manager.check_permission(
            "session-1",
            "file_read",
            {"path": "/other.txt"}
        )
        assert has_perm_other is False

    def test_grant_session_permission(self):
        manager = PermissionManager()

        manager.grant_permission(
            "session-1",
            "file_read",
            {"path": "/test.txt"},
            PermissionScope.SESSION
        )

        # Should have permission for any params
        has_perm = manager.check_permission(
            "session-1",
            "file_read",
            {"path": "/other.txt"}
        )
        assert has_perm is True

    def test_block_permission(self):
        manager = PermissionManager()

        manager.grant_permission(
            "session-1",
            "file_read",
            {"path": "/test.txt"},
            PermissionScope.NEVER
        )

        is_blocked = manager.is_blocked("file_read", {"path": "/test.txt"})
        assert is_blocked is True

    def test_revoke_session(self):
        manager = PermissionManager()

        manager.grant_permission(
            "session-1",
            "file_read",
            {"path": "/test.txt"},
            PermissionScope.SESSION
        )

        # Verify permission exists
        assert manager.check_permission("session-1", "file_read", {}) is True

        # Revoke
        manager.revoke_session("session-1")

        # Verify permission is gone
        assert manager.check_permission("session-1", "file_read", {}) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

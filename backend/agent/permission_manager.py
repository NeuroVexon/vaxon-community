"""
Axon by NeuroVexon - Permission Manager
"""

from enum import Enum
from typing import Dict, Set, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)


class PermissionScope(str, Enum):
    ONCE = "once"           # One-time permission
    SESSION = "session"     # For this session
    NEVER = "never"         # Block permanently


class PermissionManager:
    """Manages tool execution permissions"""

    def __init__(self):
        # Session-based permissions: session_id -> set of permission keys
        self._session_permissions: Dict[str, Set[str]] = {}
        # Blocked patterns: set of permission keys that are permanently blocked
        self._blocked: Set[str] = set()
        # Pending approvals: approval_id -> approval request
        self._pending: Dict[str, dict] = {}

    def _create_permission_key(self, tool: str, params: dict) -> str:
        """Create a unique key for a tool+params combination"""
        # Sort params for consistent hashing
        param_str = str(sorted(params.items()))
        return hashlib.sha256(f"{tool}:{param_str}".encode()).hexdigest()[:16]

    def _create_tool_key(self, tool: str) -> str:
        """Create a key for tool-level permission"""
        return hashlib.sha256(f"tool:{tool}".encode()).hexdigest()[:16]

    def check_permission(
        self,
        session_id: str,
        tool: str,
        params: dict
    ) -> bool:
        """Check if permission exists for this tool call"""
        # Check if blocked
        exact_key = self._create_permission_key(tool, params)
        tool_key = self._create_tool_key(tool)

        if exact_key in self._blocked or tool_key in self._blocked:
            logger.info(f"Tool {tool} is blocked")
            return False

        # Check session permissions
        session_perms = self._session_permissions.get(session_id, set())

        # Check exact match first
        if exact_key in session_perms:
            return True

        # Check tool-level permission
        if tool_key in session_perms:
            return True

        return False

    def grant_permission(
        self,
        session_id: str,
        tool: str,
        params: dict,
        scope: PermissionScope
    ) -> None:
        """Grant permission for a tool call"""
        exact_key = self._create_permission_key(tool, params)
        tool_key = self._create_tool_key(tool)

        if scope == PermissionScope.NEVER:
            # Block this exact call
            self._blocked.add(exact_key)
            logger.info(f"Blocked tool call: {tool}")

        elif scope == PermissionScope.SESSION:
            # Grant for entire session (tool-level)
            if session_id not in self._session_permissions:
                self._session_permissions[session_id] = set()
            self._session_permissions[session_id].add(tool_key)
            logger.info(f"Granted session permission for {tool}")

        elif scope == PermissionScope.ONCE:
            # One-time: add exact key temporarily
            if session_id not in self._session_permissions:
                self._session_permissions[session_id] = set()
            self._session_permissions[session_id].add(exact_key)
            logger.info(f"Granted one-time permission for {tool}")

    def revoke_permission(
        self,
        session_id: str,
        tool: str,
        params: Optional[dict] = None
    ) -> None:
        """Revoke a specific permission"""
        if params:
            key = self._create_permission_key(tool, params)
        else:
            key = self._create_tool_key(tool)

        if session_id in self._session_permissions:
            self._session_permissions[session_id].discard(key)

    def revoke_session(self, session_id: str) -> None:
        """Revoke all permissions for a session"""
        self._session_permissions.pop(session_id, None)
        logger.info(f"Revoked all permissions for session {session_id}")

    def is_blocked(self, tool: str, params: dict) -> bool:
        """Check if a tool call is explicitly blocked"""
        exact_key = self._create_permission_key(tool, params)
        tool_key = self._create_tool_key(tool)
        return exact_key in self._blocked or tool_key in self._blocked

    def unblock(self, tool: str, params: Optional[dict] = None) -> None:
        """Remove a tool from the blocklist"""
        if params:
            key = self._create_permission_key(tool, params)
        else:
            key = self._create_tool_key(tool)
        self._blocked.discard(key)

    def create_approval_request(
        self,
        session_id: str,
        tool: str,
        params: dict,
        description: str,
        risk_level: str
    ) -> str:
        """Create a pending approval request"""
        import uuid
        approval_id = str(uuid.uuid4())[:8]

        self._pending[approval_id] = {
            "id": approval_id,
            "session_id": session_id,
            "tool": tool,
            "params": params,
            "description": description,
            "risk_level": risk_level
        }

        return approval_id

    def get_pending_approval(self, approval_id: str) -> Optional[dict]:
        """Get a pending approval request"""
        return self._pending.get(approval_id)

    def resolve_approval(self, approval_id: str) -> Optional[dict]:
        """Remove and return a pending approval"""
        return self._pending.pop(approval_id, None)

    def get_session_permissions(self, session_id: str) -> list[str]:
        """Get all permissions for a session (for debugging)"""
        return list(self._session_permissions.get(session_id, set()))


# Global instance
permission_manager = PermissionManager()

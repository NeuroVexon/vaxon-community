"""
Axon by NeuroVexon - Audit Logger
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from db.models import AuditLog

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    TOOL_REQUESTED = "tool_requested"
    TOOL_APPROVED = "tool_approved"
    TOOL_REJECTED = "tool_rejected"
    TOOL_EXECUTED = "tool_executed"
    TOOL_FAILED = "tool_failed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"


class AuditLogger:
    """Logs all tool-related events for audit purposes"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def log(
        self,
        session_id: str,
        event_type: AuditEventType,
        tool_name: Optional[str] = None,
        tool_params: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
        user_decision: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> AuditLog:
        """Create an audit log entry"""

        entry = AuditLog(
            id=str(uuid.uuid4()),
            conversation_id=session_id,
            timestamp=datetime.utcnow(),
            event_type=event_type.value,
            tool_name=tool_name,
            tool_params=tool_params,
            result=result[:1000] if result else None,  # Truncate long results
            error=error,
            user_decision=user_decision,
            execution_time_ms=execution_time_ms
        )

        self.db.add(entry)
        await self.db.flush()
        await self.db.commit()

        logger.info(
            f"Audit: {event_type.value} - {tool_name or 'N/A'} "
            f"(session: {session_id[:8]}...)"
        )

        return entry

    async def log_tool_request(
        self,
        session_id: str,
        tool_name: str,
        tool_params: dict
    ) -> AuditLog:
        """Log a tool request"""
        return await self.log(
            session_id=session_id,
            event_type=AuditEventType.TOOL_REQUESTED,
            tool_name=tool_name,
            tool_params=tool_params
        )

    async def log_tool_approval(
        self,
        session_id: str,
        tool_name: str,
        tool_params: dict,
        decision: str
    ) -> AuditLog:
        """Log a tool approval"""
        return await self.log(
            session_id=session_id,
            event_type=AuditEventType.TOOL_APPROVED,
            tool_name=tool_name,
            tool_params=tool_params,
            user_decision=decision
        )

    async def log_tool_rejection(
        self,
        session_id: str,
        tool_name: str,
        tool_params: dict,
        reason: str = "rejected"
    ) -> AuditLog:
        """Log a tool rejection"""
        return await self.log(
            session_id=session_id,
            event_type=AuditEventType.TOOL_REJECTED,
            tool_name=tool_name,
            tool_params=tool_params,
            user_decision=reason
        )

    async def log_tool_execution(
        self,
        session_id: str,
        tool_name: str,
        tool_params: dict,
        result: str,
        execution_time_ms: int
    ) -> AuditLog:
        """Log a successful tool execution"""
        return await self.log(
            session_id=session_id,
            event_type=AuditEventType.TOOL_EXECUTED,
            tool_name=tool_name,
            tool_params=tool_params,
            result=result,
            execution_time_ms=execution_time_ms
        )

    async def log_tool_failure(
        self,
        session_id: str,
        tool_name: str,
        tool_params: dict,
        error: str
    ) -> AuditLog:
        """Log a failed tool execution"""
        return await self.log(
            session_id=session_id,
            event_type=AuditEventType.TOOL_FAILED,
            tool_name=tool_name,
            tool_params=tool_params,
            error=error
        )

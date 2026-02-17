"""
Axon by NeuroVexon - Database Models
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Conversation(Base):
    """Conversations / Chat Sessions"""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=True)
    system_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Chat Messages"""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Tool-related
    tool_calls = Column(JSON, nullable=True)  # If assistant requested tools
    tool_results = Column(JSON, nullable=True)  # Results from tool execution

    conversation = relationship("Conversation", back_populates="messages")


class AuditLog(Base):
    """Audit Log for Tool Executions"""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Event
    event_type = Column(String(50), nullable=False)  # tool_requested, tool_approved, tool_rejected, tool_executed, tool_failed

    # Tool Info
    tool_name = Column(String(100), nullable=True)
    tool_params = Column(JSON, nullable=True)

    # Result
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

    # User Decision
    user_decision = Column(String(20), nullable=True)  # once, session, never, rejected

    # Metrics
    execution_time_ms = Column(Integer, nullable=True)

    conversation = relationship("Conversation", back_populates="audit_logs")


class Memory(Base):
    """Persistent Agent Memory — facts the AI remembers across conversations"""
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    key = Column(String(255), nullable=False, unique=True)  # Thema / Kurzform
    content = Column(Text, nullable=False)  # Der eigentliche Fakt
    source = Column(String(50), nullable=False, default="user")  # user, agent, system
    category = Column(String(100), nullable=True)  # optional: Kategorie
    embedding = Column(LargeBinary, nullable=True)  # Vektor-Embedding als Bytes (numpy float32)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Skill(Base):
    """Registered Skills — Community-erweiterbare Fähigkeiten"""
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=False)  # Pfad zum Skill-Modul
    file_hash = Column(String(64), nullable=False)  # SHA-256 Hash für Integritätsprüfung
    version = Column(String(20), default="1.0.0")
    author = Column(String(100), nullable=True)
    enabled = Column(Boolean, default=False)  # Erst nach Approval aktiv
    approved = Column(Boolean, default=False)  # User hat den Skill explizit genehmigt
    risk_level = Column(String(20), default="medium")  # low, medium, high, critical
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Agent(Base):
    """Agent Profiles — different personas with different permissions"""
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    model = Column(String(100), nullable=True)  # z.B. "ollama/qwen2.5:7b", "claude-sonnet", None = global default
    allowed_tools = Column(JSON, nullable=True)  # ["web_search", "file_read"] oder None = alle
    allowed_skills = Column(JSON, nullable=True)  # ["email_inbox"] oder None = alle
    risk_level_max = Column(String(20), default="high")  # low, medium, high — max ohne Approval
    auto_approve_tools = Column(JSON, nullable=True)  # ["web_search"] — Tools ohne Approval
    is_default = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScheduledTask(Base):
    """Scheduled Tasks — proaktive Aufgaben mit Approval-Gate"""
    __tablename__ = "scheduled_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    cron_expression = Column(String(100), nullable=False)  # z.B. "0 9 * * *" = taeglich 9 Uhr
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True)
    prompt = Column(Text, nullable=False)  # Was der Agent ausfuehren soll
    approval_required = Column(Boolean, default=True)
    notification_channel = Column(String(20), default="web")  # web, telegram, discord
    max_retries = Column(Integer, default=1)
    last_run = Column(DateTime, nullable=True)
    last_result = Column(Text, nullable=True)
    next_run = Column(DateTime, nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Workflow(Base):
    """Workflow-Chains — mehrstufige Agent-Aufgaben"""
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    trigger_phrase = Column(String(255), nullable=True)  # z.B. "Tagesstart", "Wochenbericht"
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True)
    steps = Column(JSON, nullable=False)  # [{order, prompt, store_as}]
    approval_mode = Column(String(20), default="each_step")  # each_step, once_at_start, never
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkflowRun(Base):
    """Workflow-Ausfuehrungen — History"""
    __tablename__ = "workflow_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    status = Column(String(20), default="running")  # running, completed, failed, cancelled
    current_step = Column(Integer, default=0)
    context = Column(JSON, nullable=True)  # Variable-Kontext {store_as: result}
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class UploadedDocument(Base):
    """Uploaded Documents — Dateien die in Conversations hochgeladen wurden"""
    __tablename__ = "uploaded_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=True)
    filename = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, default=0)
    extracted_text = Column(Text, nullable=True)
    file_path = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Settings(Base):
    """User Settings"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

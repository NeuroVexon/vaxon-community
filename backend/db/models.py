"""
Axon by NeuroVexon - Database Models
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
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


class Settings(Base):
    """User Settings"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

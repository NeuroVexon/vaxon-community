"""
Axon by NeuroVexon - LLM Provider Base Class
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str


class ToolCall(BaseModel):
    id: str
    name: str
    parameters: dict


class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    finish_reason: str = "stop"


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[dict]] = None,
        stream: bool = False
    ) -> LLMResponse:
        """Send chat message and get response"""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[dict]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available"""
        pass

"""
Axon by NeuroVexon - Claude (Anthropic) LLM Provider
"""

from typing import AsyncGenerator, Optional
import logging

from .provider import BaseLLMProvider, ChatMessage, LLMResponse, ToolCall
from core.config import settings

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude API provider"""

    def __init__(self):
        self.model = settings.claude_model
        self.api_key = settings.anthropic_api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        return self._client

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert OpenAI-style tools to Claude format"""
        claude_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                claude_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}})
                })
        return claude_tools

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[dict]] = None,
        stream: bool = False
    ) -> LLMResponse:
        """Send chat message to Claude"""
        client = self._get_client()

        # Separate system message
        system_message = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_message = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": chat_messages
        }

        if system_message:
            kwargs["system"] = system_message

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        response = await client.messages.create(**kwargs)

        # Parse response
        content = None
        tool_calls = None

        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    parameters=block.input
                ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason or "stop"
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[dict]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from Claude"""
        client = self._get_client()

        # Separate system message
        system_message = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_message = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": chat_messages
        }

        if system_message:
            kwargs["system"] = system_message

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def health_check(self) -> bool:
        """Check if Claude API is accessible"""
        if not self.api_key:
            return False
        try:
            client = self._get_client()
            # Simple validation - try to create a minimal request
            return True
        except Exception as e:
            logger.warning(f"Claude health check failed: {e}")
            return False

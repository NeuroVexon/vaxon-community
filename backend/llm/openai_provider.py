"""
Axon by NeuroVexon - OpenAI LLM Provider
"""

from typing import AsyncGenerator, Optional
import logging
import json

from .provider import BaseLLMProvider, ChatMessage, LLMResponse, ToolCall
from core.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""

    def __init__(self):
        self.model = settings.openai_model
        self.api_key = settings.openai_api_key
        self._client = None
        self._current_key = None

    def update_config(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Update provider configuration"""
        if api_key and api_key != self._current_key:
            self.api_key = api_key
            self._client = None  # Force recreate client
            self._current_key = api_key
        if model:
            self.model = model

    def _get_client(self):
        if self._client is None or self._current_key != self.api_key:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self.api_key)
                self._current_key = self.api_key
            except ImportError:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )
        return self._client

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[dict]] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Send chat message to OpenAI"""
        client = self._get_client()

        kwargs = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }

        if tools:
            kwargs["tools"] = tools

        response = await client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        # Parse tool calls
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    parameters=json.loads(tc.function.arguments),
                )
                for tc in message.tool_calls
            ]

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=response.choices[0].finish_reason or "stop",
        )

    async def chat_stream(
        self, messages: list[ChatMessage], tools: Optional[list[dict]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from OpenAI"""
        client = self._get_client()

        kwargs = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }

        if tools:
            kwargs["tools"] = tools

        stream = await client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        if not self.api_key:
            return False
        try:
            client = self._get_client()
            await client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False

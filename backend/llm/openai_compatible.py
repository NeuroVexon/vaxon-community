# Copyright 2026 NeuroVexon UG (haftungsbeschraenkt)
# SPDX-License-Identifier: Apache-2.0
"""
Axon by NeuroVexon - OpenAI-Compatible LLM Provider

Generic provider for any API that uses the OpenAI chat completions format.
Works with: Groq, OpenRouter, Together, Mistral, and many more.
"""

from typing import AsyncGenerator, Optional
import logging
import json

from .provider import BaseLLMProvider, ChatMessage, LLMResponse, ToolCall

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseLLMProvider):
    """Generic OpenAI-compatible API provider (Groq, OpenRouter, etc.)"""

    def __init__(self, base_url: str, provider_name: str = "openai-compatible"):
        self.base_url = base_url
        self.provider_name = provider_name
        self.model: Optional[str] = None
        self.api_key: Optional[str] = None
        self._client = None
        self._current_key: Optional[str] = None

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
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                self._current_key = self.api_key
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        return self._client

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[dict]] = None,
        stream: bool = False
    ) -> LLMResponse:
        """Send chat message via OpenAI-compatible API"""
        client = self._get_client()

        kwargs = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages]
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
                    parameters=json.loads(tc.function.arguments)
                )
                for tc in message.tool_calls
            ]

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=response.choices[0].finish_reason or "stop"
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[dict]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response via OpenAI-compatible API"""
        client = self._get_client()

        kwargs = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True
        }

        if tools:
            kwargs["tools"] = tools

        stream = await client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def health_check(self) -> bool:
        """Check if API is accessible"""
        if not self.api_key:
            return False
        try:
            client = self._get_client()
            await client.models.list()
            return True
        except Exception as e:
            logger.warning(f"{self.provider_name} health check failed: {e}")
            return False

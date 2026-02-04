"""
Axon by NeuroVexon - Ollama LLM Provider
"""

import httpx
import json
from typing import AsyncGenerator, Optional
import logging

from .provider import BaseLLMProvider, ChatMessage, LLMResponse, ToolCall
from core.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider"""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[dict]] = None,
        stream: bool = False
    ) -> LLMResponse:
        """Send chat message to Ollama"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": self.model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "stream": False
            }

            # Ollama supports tools in newer versions
            if tools:
                payload["tools"] = tools

            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Parse tool calls if present
            tool_calls = None
            if "message" in data and "tool_calls" in data["message"]:
                tool_calls = [
                    ToolCall(
                        id=tc.get("id", f"call_{i}"),
                        name=tc["function"]["name"],
                        parameters=tc["function"]["arguments"]
                    )
                    for i, tc in enumerate(data["message"]["tool_calls"])
                ]

            return LLMResponse(
                content=data.get("message", {}).get("content"),
                tool_calls=tool_calls,
                finish_reason=data.get("done_reason", "stop")
            )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[dict]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from Ollama"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": self.model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "stream": True
            }

            if tools:
                payload["tools"] = tools

            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue

    async def health_check(self) -> bool:
        """Check if Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

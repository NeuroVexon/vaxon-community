"""
Axon by NeuroVexon - Ollama LLM Provider
"""

import httpx
import json
import re
from typing import AsyncGenerator, Optional
import logging

from .provider import BaseLLMProvider, ChatMessage, LLMResponse, ToolCall
from core.config import settings

logger = logging.getLogger(__name__)


def _parse_tool_calls_from_text(text: str, available_tools: list[dict]) -> Optional[list[ToolCall]]:
    """
    Fallback parser: extract tool calls from text when the model outputs them
    as text instead of structured tool_calls (common with mistral:7b-instruct).

    Handles patterns like:
    - [TOOL_CALLS] [{"name":"memory_save","arguments":{...}}]
    - memory_save(key="...", content="...")
    """
    if not text or not available_tools:
        return None

    tool_names = {t["function"]["name"] for t in available_tools}

    # Pattern 1: [TOOL_CALLS] [...json...]
    match = re.search(r'\[TOOL_CALLS\]\s*(\[.*?\])', text, re.DOTALL)
    if match:
        try:
            calls = json.loads(match.group(1))
            result = []
            for i, call in enumerate(calls):
                name = call.get("name", "")
                args = call.get("arguments", {})
                if name in tool_names:
                    result.append(ToolCall(id=f"fallback_{i}", name=name, parameters=args))
            if result:
                logger.info(f"Parsed {len(result)} tool call(s) from [TOOL_CALLS] text")
                return result
        except (json.JSONDecodeError, KeyError):
            pass

    # Pattern 2: JSON object in code fences: ```{"name":"tool","arguments":{...}}```
    fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if fence_match:
        try:
            obj = json.loads(fence_match.group(1))
            name = obj.get("name", "")
            args = obj.get("arguments", {})
            if name in tool_names and args:
                logger.info(f"Parsed tool call from code fence: {name}({args})")
                return [ToolCall(id="fallback_0", name=name, parameters=args)]
        except (json.JSONDecodeError, KeyError):
            pass

    # Build lookup: tool_name -> first required parameter name
    tool_first_param = {}
    for t in available_tools:
        fname = t["function"]["name"]
        required = t["function"]["parameters"].get("required", [])
        if required:
            tool_first_param[fname] = required[0]

    # Pattern 3: tool_name(key="value", ...) or tool_name({"key": "value"}) or tool_name("positional")
    for tool_name in tool_names:
        pattern = rf'{re.escape(tool_name)}\s*\((.+?)\)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            args_str = match.group(1).strip()
            try:
                # Try JSON-style: {"key": "value"}
                if args_str.startswith('{'):
                    args = json.loads(args_str)
                else:
                    # Try kwargs-style: key="value", content="value"
                    args = {}
                    for kv in re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', args_str):
                        args[kv.group(1)] = kv.group(2)

                    # Fallback: positional arg like tool("value")
                    if not args:
                        pos_match = re.match(r'^["\'](.+?)["\']$', args_str)
                        if pos_match and tool_name in tool_first_param:
                            param_name = tool_first_param[tool_name]
                            args = {param_name: pos_match.group(1)}

                if args:
                    logger.info(f"Parsed tool call from text: {tool_name}({args})")
                    return [ToolCall(id="fallback_0", name=tool_name, parameters=args)]
            except (json.JSONDecodeError, KeyError):
                pass

    return None


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

            content = data.get("message", {}).get("content")

            # Fallback: parse tool calls from text if model didn't use structured format
            if not tool_calls and content and tools:
                parsed = _parse_tool_calls_from_text(content, tools)
                if parsed:
                    tool_calls = parsed
                    content = None  # Don't return the raw text as content

            return LLMResponse(
                content=content,
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

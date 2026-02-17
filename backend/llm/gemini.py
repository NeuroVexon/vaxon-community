# Copyright 2026 NeuroVexon UG (haftungsbeschraenkt)
# SPDX-License-Identifier: Apache-2.0
"""
Axon by NeuroVexon - Google Gemini LLM Provider

Gemini uses its own API format — not OpenAI-compatible.
Supports tool calling via Gemini Function Calling.
"""

from typing import AsyncGenerator, Optional
import logging

from .provider import BaseLLMProvider, ChatMessage, LLMResponse, ToolCall

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider"""

    def __init__(self):
        self.model: str = "gemini-2.0-flash"
        self.api_key: Optional[str] = None
        self._client = None
        self._current_key: Optional[str] = None

    def update_config(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Update provider configuration"""
        if api_key and api_key != self._current_key:
            self.api_key = api_key
            self._client = None
            self._current_key = api_key
        if model:
            self.model = model

    def _get_client(self):
        if self._client is None or self._current_key != self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                self._current_key = self.api_key
            except ImportError:
                raise ImportError(
                    "google-genai package not installed. Run: pip install google-genai"
                )
        return self._client

    def _convert_tools_to_gemini(self, tools: list[dict]) -> list[dict]:
        """Convert OpenAI-style tools to Gemini Function Calling format"""
        gemini_functions = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                params = func.get("parameters", {})

                # Gemini erwartet ein leicht anderes Schema
                gemini_func = {
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "parameters": params
                }
                gemini_functions.append(gemini_func)

        return gemini_functions

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[dict]] = None,
        stream: bool = False
    ) -> LLMResponse:
        """Send chat message to Gemini"""
        client = self._get_client()
        from google.genai import types

        # Build contents for Gemini
        system_instruction = None
        contents = []
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            elif m.role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=m.content)]
                ))
            elif m.role == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=m.content)]
                ))

        # Build config
        config_kwargs = {}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        # Convert tools if provided
        gemini_tools = None
        if tools:
            gemini_fns = self._convert_tools_to_gemini(tools)
            if gemini_fns:
                from google.genai.types import FunctionDeclaration, Tool
                declarations = []
                for fn in gemini_fns:
                    declarations.append(FunctionDeclaration(
                        name=fn["name"],
                        description=fn["description"],
                        parameters=fn["parameters"]
                    ))
                gemini_tools = [Tool(function_declarations=declarations)]
                config_kwargs["tools"] = gemini_tools

        config = types.GenerateContentConfig(**config_kwargs)

        response = await client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

        # Parse response
        content = None
        tool_calls = None

        if response.candidates and response.candidates[0].content:
            parts = response.candidates[0].content.parts
            if parts:
                for part in parts:
                    if part.text:
                        content = (content or "") + part.text
                    elif part.function_call:
                        if tool_calls is None:
                            tool_calls = []
                        fc = part.function_call
                        tool_calls.append(ToolCall(
                            id=f"gemini_{len(tool_calls)}",
                            name=fc.name,
                            parameters=dict(fc.args) if fc.args else {}
                        ))

        finish_reason = "stop"
        if response.candidates:
            fr = response.candidates[0].finish_reason
            if fr:
                # Gemini enum: e.g. FinishReason.STOP → extract name
                fr_str = fr.name if hasattr(fr, "name") else str(fr)
                finish_reason = fr_str.lower()

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[dict]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from Gemini"""
        client = self._get_client()
        from google.genai import types

        # Build contents
        system_instruction = None
        contents = []
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            elif m.role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=m.content)]
                ))
            elif m.role == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=m.content)]
                ))

        config_kwargs = {}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        # Convert tools for streaming too
        if tools:
            gemini_fns = self._convert_tools_to_gemini(tools)
            if gemini_fns:
                from google.genai.types import FunctionDeclaration, Tool
                declarations = []
                for fn in gemini_fns:
                    declarations.append(FunctionDeclaration(
                        name=fn["name"],
                        description=fn["description"],
                        parameters=fn["parameters"]
                    ))
                config_kwargs["tools"] = [Tool(function_declarations=declarations)]

        config = types.GenerateContentConfig(**config_kwargs)

        async for chunk in client.aio.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text

    async def health_check(self) -> bool:
        """Check if Gemini API is accessible"""
        if not self.api_key:
            return False
        try:
            client = self._get_client()
            # Simple validation request
            await client.aio.models.list()
            return True
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False

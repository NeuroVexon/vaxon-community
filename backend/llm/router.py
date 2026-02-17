# Copyright 2026 NeuroVexon UG (haftungsbeschränkt)
# SPDX-License-Identifier: Apache-2.0
"""
Axon by NeuroVexon - LLM Provider Router
"""

from typing import Optional
import logging

from .provider import BaseLLMProvider
from .ollama import OllamaProvider
from .claude import ClaudeProvider
from .openai_provider import OpenAIProvider
from .openai_compatible import OpenAICompatibleProvider
from .gemini import GeminiProvider
from core.config import settings, LLMProvider

logger = logging.getLogger(__name__)


class LLMRouter:
    """Routes requests to the configured LLM provider"""

    def __init__(self):
        self._providers: dict[LLMProvider, BaseLLMProvider] = {}
        self._current_provider: Optional[LLMProvider] = None
        self._db_settings: dict = {}

    def update_settings(self, db_settings: dict):
        """Update router with settings from database"""
        self._db_settings = db_settings

        # Update Claude provider if exists
        if LLMProvider.CLAUDE in self._providers:
            api_key = db_settings.get("anthropic_api_key") or settings.anthropic_api_key
            model = db_settings.get("claude_model") or settings.claude_model
            self._providers[LLMProvider.CLAUDE].update_config(api_key=api_key, model=model)

        # Update OpenAI provider if exists
        if LLMProvider.OPENAI in self._providers:
            api_key = db_settings.get("openai_api_key") or settings.openai_api_key
            model = db_settings.get("openai_model") or settings.openai_model
            self._providers[LLMProvider.OPENAI].update_config(api_key=api_key, model=model)

        # Update Ollama provider if exists
        if LLMProvider.OLLAMA in self._providers:
            model = db_settings.get("ollama_model") or settings.ollama_model
            self._providers[LLMProvider.OLLAMA].update_config(model=model)

        # Update Gemini provider if exists
        if LLMProvider.GEMINI in self._providers:
            api_key = db_settings.get("gemini_api_key") or settings.gemini_api_key
            model = db_settings.get("gemini_model") or settings.gemini_model
            self._providers[LLMProvider.GEMINI].update_config(api_key=api_key, model=model)

        # Update Groq provider if exists
        if LLMProvider.GROQ in self._providers:
            api_key = db_settings.get("groq_api_key") or settings.groq_api_key
            model = db_settings.get("groq_model") or settings.groq_model
            self._providers[LLMProvider.GROQ].update_config(api_key=api_key, model=model)

        # Update OpenRouter provider if exists
        if LLMProvider.OPENROUTER in self._providers:
            api_key = db_settings.get("openrouter_api_key") or settings.openrouter_api_key
            model = db_settings.get("openrouter_model") or settings.openrouter_model
            self._providers[LLMProvider.OPENROUTER].update_config(api_key=api_key, model=model)

    def _get_or_create_provider(self, provider: LLMProvider) -> BaseLLMProvider:
        """Get or create a provider instance"""
        if provider not in self._providers:
            if provider == LLMProvider.OLLAMA:
                self._providers[provider] = OllamaProvider()
            elif provider == LLMProvider.CLAUDE:
                p = ClaudeProvider()
                api_key = self._db_settings.get("anthropic_api_key") or settings.anthropic_api_key
                model = self._db_settings.get("claude_model") or settings.claude_model
                p.update_config(api_key=api_key, model=model)
                self._providers[provider] = p
            elif provider == LLMProvider.OPENAI:
                p = OpenAIProvider()
                api_key = self._db_settings.get("openai_api_key") or settings.openai_api_key
                model = self._db_settings.get("openai_model") or settings.openai_model
                p.update_config(api_key=api_key, model=model)
                self._providers[provider] = p
            elif provider == LLMProvider.GEMINI:
                p = GeminiProvider()
                api_key = self._db_settings.get("gemini_api_key") or settings.gemini_api_key
                model = self._db_settings.get("gemini_model") or settings.gemini_model
                p.update_config(api_key=api_key, model=model)
                self._providers[provider] = p
            elif provider == LLMProvider.GROQ:
                p = OpenAICompatibleProvider(
                    base_url="https://api.groq.com/openai/v1",
                    provider_name="groq"
                )
                api_key = self._db_settings.get("groq_api_key") or settings.groq_api_key
                model = self._db_settings.get("groq_model") or settings.groq_model
                p.update_config(api_key=api_key, model=model)
                self._providers[provider] = p
            elif provider == LLMProvider.OPENROUTER:
                p = OpenAICompatibleProvider(
                    base_url="https://openrouter.ai/api/v1",
                    provider_name="openrouter"
                )
                api_key = self._db_settings.get("openrouter_api_key") or settings.openrouter_api_key
                model = self._db_settings.get("openrouter_model") or settings.openrouter_model
                p.update_config(api_key=api_key, model=model)
                self._providers[provider] = p
            else:
                raise ValueError(f"Unknown provider: {provider}")
        return self._providers[provider]

    def get_provider(self, provider: Optional[LLMProvider] = None) -> BaseLLMProvider:
        """Get the LLM provider to use"""
        target = provider or settings.llm_provider
        return self._get_or_create_provider(target)

    def get_current_provider_name(self) -> str:
        """Get the name of the current provider from DB or default"""
        return self._db_settings.get("llm_provider", settings.llm_provider.value)

    async def health_check_all(self) -> dict[str, bool]:
        """Check health of all providers"""
        results = {}
        for provider in LLMProvider:
            try:
                p = self._get_or_create_provider(provider)
                results[provider.value] = await p.health_check()
            except Exception as e:
                logger.warning(f"Health check failed for {provider}: {e}")
                results[provider.value] = False
        return results


# Global router instance
llm_router = LLMRouter()

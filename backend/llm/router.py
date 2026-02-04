"""
Axon by NeuroVexon - LLM Provider Router
"""

from typing import Optional
import logging

from .provider import BaseLLMProvider
from .ollama import OllamaProvider
from .claude import ClaudeProvider
from .openai_provider import OpenAIProvider
from core.config import settings, LLMProvider

logger = logging.getLogger(__name__)


class LLMRouter:
    """Routes requests to the configured LLM provider"""

    def __init__(self):
        self._providers: dict[LLMProvider, BaseLLMProvider] = {}
        self._current_provider: Optional[LLMProvider] = None

    def _get_or_create_provider(self, provider: LLMProvider) -> BaseLLMProvider:
        """Get or create a provider instance"""
        if provider not in self._providers:
            if provider == LLMProvider.OLLAMA:
                self._providers[provider] = OllamaProvider()
            elif provider == LLMProvider.CLAUDE:
                self._providers[provider] = ClaudeProvider()
            elif provider == LLMProvider.OPENAI:
                self._providers[provider] = OpenAIProvider()
            else:
                raise ValueError(f"Unknown provider: {provider}")
        return self._providers[provider]

    def get_provider(self, provider: Optional[LLMProvider] = None) -> BaseLLMProvider:
        """Get the LLM provider to use"""
        target = provider or settings.llm_provider
        return self._get_or_create_provider(target)

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

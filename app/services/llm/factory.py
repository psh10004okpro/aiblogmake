"""
LLM Provider Factory.

Factory for creating and managing LLM provider instances.
"""

from typing import Optional, Dict
from app.core.config import settings
from app.utils.logger import get_logger
from .base import BaseLLMProvider
from .claude_provider import ClaudeProvider
from .chatgpt_provider import ChatGPTProvider
from .gemini_provider import GeminiProvider

logger = get_logger(__name__)


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    _providers: Dict[str, BaseLLMProvider] = {}

    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_name: Name of the provider (claude, chatgpt, gemini).
            api_key: Override API key (uses settings if not provided).
            model: Override model name (uses settings if not provided).
            max_tokens: Override max_tokens (uses settings if not provided).
            temperature: Override temperature (uses settings if not provided).

        Returns:
            BaseLLMProvider: Provider instance.

        Raises:
            ValueError: If provider_name is not supported.
            ValueError: If API key is not available.
        """
        provider_name = provider_name.lower()

        if provider_name == "claude":
            api_key = api_key or settings.anthropic_api_key
            model = model or settings.claude_model
            max_tokens = max_tokens or settings.claude_max_tokens
            temperature = temperature or settings.claude_temperature

            if not api_key:
                raise ValueError("Anthropic API key is not configured")

            logger.info("creating_claude_provider", model=model)
            return ClaudeProvider(
                api_key=api_key,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )

        elif provider_name == "chatgpt":
            api_key = api_key or settings.openai_api_key
            model = model or settings.chatgpt_model
            max_tokens = max_tokens or settings.chatgpt_max_tokens
            temperature = temperature or settings.chatgpt_temperature

            if not api_key:
                raise ValueError("OpenAI API key is not configured")

            logger.info("creating_chatgpt_provider", model=model)
            return ChatGPTProvider(
                api_key=api_key,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                org_id=settings.openai_org_id
            )

        elif provider_name == "gemini":
            api_key = api_key or settings.gemini_api_key
            model = model or settings.gemini_model
            max_tokens = max_tokens or settings.gemini_max_tokens
            temperature = temperature or settings.gemini_temperature

            if not api_key:
                raise ValueError("Google Gemini API key is not configured")

            logger.info("creating_gemini_provider", model=model)
            return GeminiProvider(
                api_key=api_key,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )

        else:
            raise ValueError(
                f"Unsupported provider: {provider_name}. "
                f"Must be one of: claude, chatgpt, gemini"
            )

    @classmethod
    def get_default_provider(cls) -> BaseLLMProvider:
        """
        Get the default provider from settings.

        Returns:
            BaseLLMProvider: Default provider instance.
        """
        provider_name = settings.default_llm_provider
        logger.info("getting_default_provider", provider=provider_name)
        return cls.create_provider(provider_name)

    @classmethod
    def get_cached_provider(
        cls,
        provider_name: str,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Get or create a cached provider instance.

        This caches provider instances to avoid repeated initialization.
        Only use this if you're sure the configuration won't change.

        Args:
            provider_name: Name of the provider.
            **kwargs: Provider configuration overrides.

        Returns:
            BaseLLMProvider: Cached or new provider instance.
        """
        cache_key = f"{provider_name}_{kwargs.get('model', 'default')}"

        if cache_key not in cls._providers:
            logger.debug("creating_cached_provider", cache_key=cache_key)
            cls._providers[cache_key] = cls.create_provider(provider_name, **kwargs)
        else:
            logger.debug("using_cached_provider", cache_key=cache_key)

        return cls._providers[cache_key]

    @classmethod
    def clear_cache(cls):
        """Clear the provider cache."""
        logger.info("clearing_provider_cache", count=len(cls._providers))
        cls._providers.clear()

    @classmethod
    def list_available_providers(cls) -> Dict[str, bool]:
        """
        List available providers based on API key configuration.

        Returns:
            Dict[str, bool]: Provider availability status.
        """
        return {
            "claude": bool(settings.anthropic_api_key),
            "chatgpt": bool(settings.openai_api_key),
            "gemini": bool(settings.gemini_api_key),
        }


def get_llm_provider(
    provider_name: Optional[str] = None,
    **kwargs
) -> BaseLLMProvider:
    """
    Convenience function to get an LLM provider.

    Args:
        provider_name: Name of provider (uses default if None).
        **kwargs: Provider configuration overrides.

    Returns:
        BaseLLMProvider: Provider instance.

    Example:
        ```python
        # Get default provider
        provider = get_llm_provider()

        # Get specific provider
        claude = get_llm_provider("claude")
        chatgpt = get_llm_provider("chatgpt", temperature=0.9)
        ```
    """
    if provider_name is None:
        return LLMProviderFactory.get_default_provider()

    return LLMProviderFactory.create_provider(provider_name, **kwargs)

"""
Base LLM provider interface.

This module defines the abstract base class for all LLM providers,
ensuring consistent interface across different providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """Standardized LLM response."""

    content: str
    """Generated text content"""

    model: str
    """Model used for generation"""

    tokens_used: int
    """Total tokens used (input + output)"""

    provider: str
    """Provider name (claude, chatgpt, gemini)"""

    finish_reason: str = "stop"
    """Reason for completion (stop, length, etc.)"""

    metadata: Optional[Dict[str, Any]] = None
    """Additional provider-specific metadata"""


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str, model: str, max_tokens: int = 4000, temperature: float = 0.7):
        """
        Initialize the LLM provider.

        Args:
            api_key: API key for the provider.
            model: Model name/identifier.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0-1.0).
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate text from a prompt.

        Args:
            prompt: User prompt to generate from.
            max_tokens: Override default max_tokens.
            temperature: Override default temperature.
            system_prompt: System/instruction prompt (if supported).

        Returns:
            LLMResponse: Standardized response object.

        Raises:
            Exception: Provider-specific API errors.
        """
        pass

    @abstractmethod
    async def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> LLMResponse:
        """
        Generate with automatic retry on failures.

        Args:
            prompt: User prompt to generate from.
            max_retries: Maximum number of retry attempts.
            **kwargs: Additional generation parameters.

        Returns:
            LLMResponse: Standardized response object.

        Raises:
            Exception: If all retries fail.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
        pass

    @property
    def is_available(self) -> bool:
        """Check if provider is available (has valid API key)."""
        return bool(self.api_key and self.api_key.strip())

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(model={self.model}, max_tokens={self.max_tokens})"

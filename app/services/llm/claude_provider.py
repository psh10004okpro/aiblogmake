"""
Claude LLM provider implementation.

Uses Anthropic's Claude API for content generation.
"""

import asyncio
from typing import Optional
import anthropic
from anthropic import APIError, APIConnectionError, RateLimitError

from .base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeProvider(BaseLLMProvider):
    """Claude LLM provider using Anthropic API."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", max_tokens: int = 4000, temperature: float = 0.7):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key.
            model: Claude model name.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
        """
        super().__init__(api_key, model, max_tokens, temperature)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "claude"

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate text using Claude API.

        Args:
            prompt: User prompt.
            max_tokens: Override default max_tokens.
            temperature: Override default temperature.
            system_prompt: System prompt (Claude supports this natively).

        Returns:
            LLMResponse: Standardized response.
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        try:
            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Build request kwargs
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }

            # Add system prompt if provided
            if system_prompt:
                kwargs["system"] = system_prompt

            logger.debug(
                "claude_api_request",
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                has_system=bool(system_prompt)
            )

            response = await self.client.messages.create(**kwargs)

            # Extract content
            content = response.content[0].text

            # Calculate total tokens
            total_tokens = response.usage.input_tokens + response.usage.output_tokens

            logger.info(
                "claude_generation_success",
                model=self.model,
                tokens=total_tokens,
                stop_reason=response.stop_reason
            )

            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=total_tokens,
                provider=self.provider_name,
                finish_reason=response.stop_reason,
                metadata={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "stop_sequence": response.stop_sequence,
                }
            )

        except RateLimitError as e:
            logger.error("claude_rate_limit_error", error=str(e))
            raise
        except APIConnectionError as e:
            logger.error("claude_connection_error", error=str(e))
            raise
        except APIError as e:
            logger.error("claude_api_error", error=str(e), status_code=e.status_code)
            raise
        except Exception as e:
            logger.error("claude_unexpected_error", error=str(e), error_type=type(e).__name__)
            raise

    async def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> LLMResponse:
        """
        Generate with exponential backoff retry.

        Args:
            prompt: User prompt.
            max_retries: Maximum retry attempts.
            **kwargs: Additional generation parameters.

        Returns:
            LLMResponse: Standardized response.

        Raises:
            Exception: If all retries fail.
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await self.generate(prompt, **kwargs)

            except RateLimitError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        "claude_rate_limit_retry",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("claude_rate_limit_exhausted", attempts=max_retries)
                    raise

            except APIConnectionError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        "claude_connection_retry",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("claude_connection_exhausted", attempts=max_retries)
                    raise

            except Exception as e:
                # Don't retry on other errors
                logger.error("claude_error_no_retry", error=str(e), error_type=type(e).__name__)
                raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise Exception("Failed to generate with Claude after retries")

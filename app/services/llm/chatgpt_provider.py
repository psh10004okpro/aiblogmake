"""
ChatGPT LLM provider implementation.

Uses OpenAI's ChatGPT API for content generation.
"""

import asyncio
from typing import Optional
from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from .base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChatGPTProvider(BaseLLMProvider):
    """ChatGPT LLM provider using OpenAI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        org_id: Optional[str] = None
    ):
        """
        Initialize ChatGPT provider.

        Args:
            api_key: OpenAI API key.
            model: ChatGPT model name (gpt-4o, gpt-4-turbo, gpt-3.5-turbo).
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            org_id: Optional organization ID.
        """
        super().__init__(api_key, model, max_tokens, temperature)
        self.client = AsyncOpenAI(
            api_key=api_key,
            organization=org_id
        )

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "chatgpt"

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate text using ChatGPT API.

        Args:
            prompt: User prompt.
            max_tokens: Override default max_tokens.
            temperature: Override default temperature.
            system_prompt: System prompt for ChatGPT.

        Returns:
            LLMResponse: Standardized response.
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        try:
            # Build messages
            messages = []

            # Add system prompt if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            logger.debug(
                "chatgpt_api_request",
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                has_system=bool(system_prompt)
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Extract content
            content = response.choices[0].message.content

            # Get finish reason
            finish_reason = response.choices[0].finish_reason

            # Calculate total tokens
            total_tokens = response.usage.total_tokens

            logger.info(
                "chatgpt_generation_success",
                model=self.model,
                tokens=total_tokens,
                finish_reason=finish_reason
            )

            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=total_tokens,
                provider=self.provider_name,
                finish_reason=finish_reason,
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "system_fingerprint": response.system_fingerprint,
                }
            )

        except RateLimitError as e:
            logger.error("chatgpt_rate_limit_error", error=str(e))
            raise
        except APIConnectionError as e:
            logger.error("chatgpt_connection_error", error=str(e))
            raise
        except APIError as e:
            logger.error("chatgpt_api_error", error=str(e), status_code=getattr(e, 'status_code', None))
            raise
        except Exception as e:
            logger.error("chatgpt_unexpected_error", error=str(e), error_type=type(e).__name__)
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
                        "chatgpt_rate_limit_retry",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("chatgpt_rate_limit_exhausted", attempts=max_retries)
                    raise

            except APIConnectionError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        "chatgpt_connection_retry",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("chatgpt_connection_exhausted", attempts=max_retries)
                    raise

            except Exception as e:
                # Don't retry on other errors
                logger.error("chatgpt_error_no_retry", error=str(e), error_type=type(e).__name__)
                raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise Exception("Failed to generate with ChatGPT after retries")

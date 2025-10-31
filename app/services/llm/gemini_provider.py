"""
Gemini LLM provider implementation.

Uses Google's Gemini API for content generation.
"""

import asyncio
from typing import Optional
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Gemini LLM provider using Google Generative AI API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro-latest",
        max_tokens: int = 4000,
        temperature: float = 0.7
    ):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key.
            model: Gemini model name.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
        """
        super().__init__(api_key, model, max_tokens, temperature)

        # Configure the API
        genai.configure(api_key=api_key)

        # Initialize the model
        self.client = genai.GenerativeModel(model)

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "gemini"

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate text using Gemini API.

        Args:
            prompt: User prompt.
            max_tokens: Override default max_tokens.
            temperature: Override default temperature.
            system_prompt: System instruction (Gemini supports this as system_instruction).

        Returns:
            LLMResponse: Standardized response.
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        try:
            # Build generation config
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            # If system prompt is provided, recreate model with system instruction
            model = self.client
            if system_prompt:
                model = genai.GenerativeModel(
                    self.model,
                    system_instruction=system_prompt
                )

            logger.debug(
                "gemini_api_request",
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                has_system=bool(system_prompt)
            )

            # Generate content (synchronous call - wrap in asyncio)
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=generation_config
            )

            # Extract content
            content = response.text

            # Get finish reason
            finish_reason = str(response.candidates[0].finish_reason.name) if response.candidates else "STOP"

            # Estimate tokens (Gemini doesn't provide exact token counts in all cases)
            # We'll use approximate calculation or metadata if available
            total_tokens = 0
            if hasattr(response, 'usage_metadata'):
                total_tokens = (
                    response.usage_metadata.prompt_token_count +
                    response.usage_metadata.candidates_token_count
                )
            else:
                # Rough estimation: ~4 characters per token
                total_tokens = (len(prompt) + len(content)) // 4

            logger.info(
                "gemini_generation_success",
                model=self.model,
                tokens=total_tokens,
                finish_reason=finish_reason
            )

            metadata = {
                "finish_reason_raw": finish_reason,
            }

            # Add usage metadata if available
            if hasattr(response, 'usage_metadata'):
                metadata.update({
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                })

            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=total_tokens,
                provider=self.provider_name,
                finish_reason=finish_reason,
                metadata=metadata
            )

        except google_exceptions.ResourceExhausted as e:
            logger.error("gemini_rate_limit_error", error=str(e))
            raise
        except google_exceptions.GoogleAPIError as e:
            logger.error("gemini_api_error", error=str(e))
            raise
        except Exception as e:
            logger.error("gemini_unexpected_error", error=str(e), error_type=type(e).__name__)
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

            except google_exceptions.ResourceExhausted as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        "gemini_rate_limit_retry",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("gemini_rate_limit_exhausted", attempts=max_retries)
                    raise

            except google_exceptions.GoogleAPIError as e:
                last_exception = e
                # Check if it's a retryable error
                if attempt < max_retries - 1 and hasattr(e, 'code') and e.code in [503, 504]:
                    wait_time = 2 ** attempt
                    logger.warning(
                        "gemini_api_retry",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time,
                        error_code=e.code
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("gemini_api_error_no_retry", error=str(e))
                    raise

            except Exception as e:
                # Don't retry on other errors
                logger.error("gemini_error_no_retry", error=str(e), error_type=type(e).__name__)
                raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise Exception("Failed to generate with Gemini after retries")

"""LLM client for OpenRouter API - Infrastructure layer only.

This module handles:
- HTTP transport with connection pooling
- Authentication & API key management
- Retry logic with exponential backoff
- Timeout handling
- Rate limiting
- Observability (logging, metrics)
- Generic structured output enforcement (JSON schema validation)
- Error handling

Business logic (prompts, use cases) should be in service layer.
"""

import httpx
import json
import asyncio
import logging
from typing import Optional, Type, TypeVar, AsyncIterator
from datetime import datetime
from pydantic import BaseModel, ValidationError

from .config import get_config

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limit is exceeded."""
    pass


class LLMValidationError(LLMError):
    """Raised when LLM response doesn't match expected schema."""
    pass


class TokenUsage(BaseModel):
    """Token usage statistics from LLM API."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: Optional[float] = None


class LLMResponse(BaseModel):
    """Complete LLM response with metadata."""
    content: str
    usage: Optional[TokenUsage] = None
    model: str
    finish_reason: Optional[str] = None
    response_time_ms: int


class LLMClient:
    """Client for OpenRouter/LLM API operations.

    This is a pure infrastructure client - it handles transport, auth, retries,
    and structured output enforcement. Business logic should be in service layer.
    """

    def __init__(
        self,
        api_key: str,
        api_url: str,
        model: str,
        timeout: float = 60.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

        # Metrics tracking
        self._request_count = 0
        self._total_tokens = 0
        self._total_cost_usd = 0.0

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            model: Optional model override (uses default if not specified)

        Returns:
            LLMResponse with content and metadata

        Raises:
            LLMError: On API errors
            LLMRateLimitError: On rate limit exceeded
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        return await self._execute_request(payload)

    async def generate_structured_completion(
        self,
        schema: Type[T],
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: Optional[str] = None,
        fallback_on_validation_error: bool = False,
    ) -> T:
        """Generate a structured completion that conforms to a Pydantic schema.

        Args:
            schema: Pydantic model class to validate response
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model: Optional model override
            fallback_on_validation_error: If True, return partial data on validation errors

        Returns:
            Instance of schema with parsed response

        Raises:
            LLMValidationError: If response doesn't match schema and no fallback
            LLMError: On other API errors
        """
        # Enhance system prompt to request JSON format
        json_instruction = f"\n\nRespond with valid JSON matching this schema: {schema.model_json_schema()}"
        enhanced_system_prompt = (system_prompt or "") + json_instruction

        response = await self.generate_completion(
            prompt=prompt,
            system_prompt=enhanced_system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
        )

        # Parse JSON response
        try:
            # Try to extract JSON from markdown code blocks if present
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            return schema.model_validate(data)

        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(
                f"Failed to parse LLM response as {schema.__name__}: {e}",
                extra={
                    "response_content": response.content[:500],
                    "schema": schema.__name__,
                }
            )

            if fallback_on_validation_error:
                # Try to construct partial object
                try:
                    # Attempt to extract any valid JSON from response
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        return schema.model_validate(data)
                except:
                    pass

            raise LLMValidationError(
                f"Response does not match schema {schema.__name__}: {str(e)}"
            ) from e

    async def stream_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream completion tokens as they are generated.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model: Optional model override

        Yields:
            Token strings as they arrive
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        headers = self._build_headers()

        payload = {
            "model": model or self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        async with self.client.stream(
            "POST",
            f"{self.api_url}/chat/completions",
            headers=headers,
            json=payload,
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue

    async def _execute_request(self, payload: dict) -> LLMResponse:
        """Execute HTTP request with retry logic.

        Args:
            payload: Request payload

        Returns:
            LLMResponse

        Raises:
            LLMError: On API errors after retries
            LLMRateLimitError: On rate limit exceeded
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                start_time = datetime.now()

                response = await self._make_api_call(payload)

                end_time = datetime.now()
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)

                # Parse successful response
                llm_response = self._parse_response(response, response_time_ms)

                # Log request
                self._log_request(payload, llm_response, success=True)

                # Update metrics
                self._update_metrics(llm_response)

                return llm_response

            except LLMRateLimitError as e:
                # Don't retry on rate limits
                self._log_request(payload, None, success=False, error=str(e))
                raise

            except LLMError as e:
                last_exception = e

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"LLM request failed (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    self._log_request(payload, None, success=False, error=str(e))

        # All retries exhausted
        raise last_exception or LLMError("Request failed after all retries")

    async def _make_api_call(self, payload: dict) -> httpx.Response:
        """Make the actual API call.

        Args:
            payload: Request payload

        Returns:
            HTTP response

        Raises:
            LLMError: On HTTP errors
            LLMRateLimitError: On rate limit
        """
        headers = self._build_headers()

        try:
            response = await self.client.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload,
            )

            # Check for rate limiting
            if response.status_code == 429:
                raise LLMRateLimitError("Rate limit exceeded")

            response.raise_for_status()

            return response

        except httpx.HTTPStatusError as e:
            raise LLMError(f"HTTP error {e.response.status_code}: {e}") from e

        except httpx.TimeoutException as e:
            raise LLMError(f"Request timeout: {e}") from e

        except httpx.RequestError as e:
            raise LLMError(f"Request error: {e}") from e

    def _build_headers(self) -> dict:
        """Build HTTP headers for API request."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _parse_response(self, response: httpx.Response, response_time_ms: int) -> LLMResponse:
        """Parse HTTP response into LLMResponse.

        Args:
            response: HTTP response
            response_time_ms: Response time in milliseconds

        Returns:
            LLMResponse

        Raises:
            LLMError: If response format is invalid
        """
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise LLMError(f"Invalid JSON response: {e}") from e

        if "choices" not in data or len(data["choices"]) == 0:
            raise LLMError("No choices in response")

        content = data["choices"][0].get("message", {}).get("content", "")
        finish_reason = data["choices"][0].get("finish_reason")

        # Parse usage statistics
        usage = None
        if "usage" in data:
            usage_data = data["usage"]
            estimated_cost = self._estimate_cost(
                usage_data.get("prompt_tokens", 0),
                usage_data.get("completion_tokens", 0),
            )

            usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
                estimated_cost_usd=estimated_cost,
            )

        return LLMResponse(
            content=content,
            usage=usage,
            model=data.get("model", self.model),
            finish_reason=finish_reason,
            response_time_ms=response_time_ms,
        )

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost in USD based on token usage.

        This uses approximate pricing for Claude 3.5 Sonnet via OpenRouter.
        Adjust based on actual model pricing.
        """
        # Approximate pricing (per million tokens)
        # Claude 3.5 Sonnet: $3 input, $15 output
        input_cost_per_million = 3.0
        output_cost_per_million = 15.0

        input_cost = (prompt_tokens / 1_000_000) * input_cost_per_million
        output_cost = (completion_tokens / 1_000_000) * output_cost_per_million

        return input_cost + output_cost

    def _log_request(
        self,
        payload: dict,
        response: Optional[LLMResponse],
        success: bool,
        error: Optional[str] = None,
    ):
        """Log request details for observability.

        Args:
            payload: Request payload
            response: LLM response (if successful)
            success: Whether request succeeded
            error: Error message (if failed)
        """
        log_data = {
            "model": payload.get("model", self.model),
            "max_tokens": payload.get("max_tokens"),
            "temperature": payload.get("temperature"),
            "success": success,
        }

        if response and response.usage:
            log_data.update({
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "estimated_cost_usd": response.usage.estimated_cost_usd,
                "response_time_ms": response.response_time_ms,
            })

        if error:
            log_data["error"] = error

        if success:
            logger.info("LLM request completed", extra=log_data)
        else:
            logger.error("LLM request failed", extra=log_data)

    def _update_metrics(self, response: LLMResponse):
        """Update internal metrics counters.

        Args:
            response: LLM response
        """
        self._request_count += 1

        if response.usage:
            self._total_tokens += response.usage.total_tokens
            if response.usage.estimated_cost_usd:
                self._total_cost_usd += response.usage.estimated_cost_usd

    def get_metrics(self) -> dict:
        """Get current metrics.

        Returns:
            Dict with request count, token usage, and cost
        """
        return {
            "request_count": self._request_count,
            "total_tokens": self._total_tokens,
            "total_cost_usd": self._total_cost_usd,
        }

    def reset_metrics(self):
        """Reset metrics counters."""
        self._request_count = 0
        self._total_tokens = 0
        self._total_cost_usd = 0.0


# Global client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        config = get_config()
        _llm_client = LLMClient(
            api_key=config.openrouter_api_key,
            api_url=config.openrouter_api_url,
            model=config.llm_model,
        )
    return _llm_client

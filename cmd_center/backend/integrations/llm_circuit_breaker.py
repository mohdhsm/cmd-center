"""Circuit breaker and resilience patterns for LLM operations.

This module provides:
- Circuit breaker to prevent cascading failures
- Rate limiting to stay within API limits
- Request timeout handling
- Fallback strategies
"""

import time
import logging
import asyncio
from enum import Enum
from typing import Optional, Callable, Any, TypeVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Open circuit after this many failures
    success_threshold: int = 2  # Close circuit after this many successes in half-open
    timeout_seconds: float = 60.0  # Wait this long before half-open
    expected_exception: type = Exception  # Which exceptions count as failures


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=datetime.now)
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open and rejecting requests."""
    pass


class CircuitBreaker:
    """Circuit breaker for LLM requests.

    Implements the circuit breaker pattern to prevent cascading failures:
    - CLOSED: Normal operation, requests go through
    - OPEN: Service is failing, reject requests immediately
    - HALF_OPEN: Testing if service recovered, allow limited requests

    Usage:
        breaker = CircuitBreaker(
            failure_threshold=5,
            timeout_seconds=60,
        )

        async def call_llm():
            return await breaker.call(
                lambda: llm.generate_completion(...)
            )
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()

    async def call(self, func: Callable[[], Any]) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Async function to execute

        Returns:
            Result from function

        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: Original exception from func
        """
        self.stats.total_requests += 1

        # Check circuit state
        if self.stats.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self._should_attempt_reset():
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                self.stats.state = CircuitState.HALF_OPEN
                self.stats.last_state_change = datetime.now()
            else:
                # Still open, reject request
                logger.warning("Circuit breaker OPEN - rejecting request")
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN. "
                    f"Last failure: {self.stats.last_failure_time}. "
                    f"Will retry after {self.config.timeout_seconds}s timeout."
                )

        # Execute function
        try:
            result = await func()
            self._on_success()
            return result

        except self.config.expected_exception as e:
            self._on_failure(e)
            raise

    def _on_success(self):
        """Handle successful request."""
        self.stats.total_successes += 1

        if self.stats.state == CircuitState.HALF_OPEN:
            self.stats.success_count += 1
            logger.info(
                f"Circuit breaker HALF_OPEN success "
                f"({self.stats.success_count}/{self.config.success_threshold})"
            )

            # Check if we can close the circuit
            if self.stats.success_count >= self.config.success_threshold:
                logger.info("Circuit breaker transitioning to CLOSED (recovered)")
                self.stats.state = CircuitState.CLOSED
                self.stats.failure_count = 0
                self.stats.success_count = 0
                self.stats.last_state_change = datetime.now()

        elif self.stats.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.stats.failure_count = 0

    def _on_failure(self, exception: Exception):
        """Handle failed request."""
        self.stats.total_failures += 1
        self.stats.failure_count += 1
        self.stats.last_failure_time = datetime.now()

        logger.warning(
            f"Circuit breaker recorded failure "
            f"({self.stats.failure_count}/{self.config.failure_threshold}): "
            f"{type(exception).__name__}: {str(exception)}"
        )

        if self.stats.state == CircuitState.HALF_OPEN:
            # Failure in half-open means service still broken
            logger.warning("Circuit breaker transitioning to OPEN (still failing)")
            self.stats.state = CircuitState.OPEN
            self.stats.failure_count = 0
            self.stats.success_count = 0
            self.stats.last_state_change = datetime.now()

        elif self.stats.state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if self.stats.failure_count >= self.config.failure_threshold:
                logger.error(
                    f"Circuit breaker transitioning to OPEN "
                    f"({self.stats.failure_count} failures)"
                )
                self.stats.state = CircuitState.OPEN
                self.stats.last_state_change = datetime.now()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try half-open."""
        if self.stats.last_failure_time is None:
            return True

        elapsed = (datetime.now() - self.stats.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout_seconds

    def get_stats(self) -> dict:
        """Get current circuit breaker statistics."""
        return {
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_state_change": self.stats.last_state_change.isoformat(),
            "total_requests": self.stats.total_requests,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "uptime_pct": (self.stats.total_successes / self.stats.total_requests * 100)
            if self.stats.total_requests > 0 else 100.0,
        }

    def reset(self):
        """Reset circuit breaker to initial state."""
        logger.info("Circuit breaker manually reset")
        self.stats = CircuitBreakerStats()


class RateLimiter:
    """Token bucket rate limiter for LLM requests.

    Limits requests per minute to stay within API rate limits.

    Usage:
        limiter = RateLimiter(requests_per_minute=60)
        await limiter.acquire()  # Blocks until token available
    """

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a token for making a request.

        Blocks if no tokens available until refill.
        """
        async with self.lock:
            # Refill tokens
            now = time.time()
            elapsed = now - self.last_refill
            refill_amount = int(elapsed * (self.requests_per_minute / 60.0))

            if refill_amount > 0:
                self.tokens = min(self.requests_per_minute, self.tokens + refill_amount)
                self.last_refill = now

            # Wait if no tokens
            while self.tokens <= 0:
                wait_time = 60.0 / self.requests_per_minute
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

                # Refill after waiting
                now = time.time()
                elapsed = now - self.last_refill
                refill_amount = int(elapsed * (self.requests_per_minute / 60.0))
                if refill_amount > 0:
                    self.tokens = min(self.requests_per_minute, self.tokens + refill_amount)
                    self.last_refill = now

            # Consume token
            self.tokens -= 1

    def get_stats(self) -> dict:
        """Get current rate limiter statistics."""
        return {
            "available_tokens": self.tokens,
            "max_tokens": self.requests_per_minute,
            "last_refill": datetime.fromtimestamp(self.last_refill).isoformat(),
        }


class LLMResilience:
    """Combined resilience wrapper for LLM operations.

    Combines circuit breaker and rate limiting for robust LLM calls.

    Usage:
        resilience = LLMResilience(
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=5),
            rate_limit_rpm=60,
        )

        result = await resilience.execute(
            lambda: llm.generate_completion(...),
            fallback=lambda: "Fallback response"
        )
    """

    def __init__(
        self,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        rate_limit_rpm: int = 60,
    ):
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config)
        self.rate_limiter = RateLimiter(rate_limit_rpm)

    async def execute(
        self,
        func: Callable[[], T],
        fallback: Optional[Callable[[], T]] = None,
    ) -> T:
        """Execute function with full resilience protection.

        Args:
            func: Async function to execute
            fallback: Optional fallback function if circuit is open

        Returns:
            Result from func or fallback

        Raises:
            CircuitBreakerOpen: If circuit is open and no fallback provided
            Exception: Original exception from func
        """
        # Apply rate limiting first
        await self.rate_limiter.acquire()

        # Then circuit breaker
        try:
            return await self.circuit_breaker.call(func)
        except CircuitBreakerOpen as e:
            if fallback:
                logger.warning("Circuit breaker open, using fallback")
                return fallback()
            raise

    def get_stats(self) -> dict:
        """Get combined statistics."""
        return {
            "circuit_breaker": self.circuit_breaker.get_stats(),
            "rate_limiter": self.rate_limiter.get_stats(),
        }


# Global resilience instance
_llm_resilience: Optional[LLMResilience] = None


def get_llm_resilience() -> LLMResilience:
    """Get or create LLM resilience singleton.

    Default configuration:
    - Circuit breaker: 5 failures trigger open, 60s timeout
    - Rate limiter: 60 requests per minute
    """
    global _llm_resilience
    if _llm_resilience is None:
        _llm_resilience = LLMResilience(
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout_seconds=60.0,
            ),
            rate_limit_rpm=60,
        )
    return _llm_resilience

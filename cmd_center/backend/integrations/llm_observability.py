"""Structured logging and observability for LLM operations.

This module provides:
- Structured JSON logging with context
- Request/response tracing
- Performance metrics
- Cost tracking
- Error categorization
"""

import logging
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass, asdict, field

# Configure structured logging
logger = logging.getLogger(__name__)


@dataclass
class LLMRequestContext:
    """Context for a single LLM request."""
    request_id: str
    service: str  # "writer_service", "cashflow_prediction_service", etc.
    operation: str  # "draft_email", "predict_cashflow", etc.
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    response_time_ms: Optional[int] = None
    success: bool = True
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class LLMObservabilityLogger:
    """Structured logger for LLM operations with context tracking."""

    def __init__(self):
        self.logger = logging.getLogger("llm_observability")
        # Set to INFO to capture all LLM operations
        self.logger.setLevel(logging.INFO)

    def log_request_start(self, context: LLMRequestContext):
        """Log the start of an LLM request.

        Args:
            context: Request context
        """
        self.logger.info(
            f"LLM Request Started: {context.service}.{context.operation}",
            extra={
                "event": "llm_request_start",
                "request_id": context.request_id,
                "service": context.service,
                "operation": context.operation,
                "model": context.model,
                "metadata": context.metadata,
            }
        )

    def log_request_complete(self, context: LLMRequestContext):
        """Log successful completion of an LLM request.

        Args:
            context: Request context with results
        """
        self.logger.info(
            f"LLM Request Complete: {context.service}.{context.operation} "
            f"[{context.response_time_ms}ms, {context.total_tokens} tokens, ${context.cost_usd:.4f}]",
            extra={
                "event": "llm_request_complete",
                **context.to_dict(),
            }
        )

    def log_request_error(self, context: LLMRequestContext, error: Exception):
        """Log an LLM request error.

        Args:
            context: Request context
            error: Exception that occurred
        """
        context.success = False
        context.error_type = type(error).__name__
        context.error_message = str(error)

        self.logger.error(
            f"LLM Request Failed: {context.service}.{context.operation} - {context.error_type}: {context.error_message}",
            extra={
                "event": "llm_request_error",
                **context.to_dict(),
            },
            exc_info=True
        )

    def log_validation_error(self, context: LLMRequestContext, schema_name: str, response_snippet: str):
        """Log a validation error when LLM response doesn't match schema.

        Args:
            context: Request context
            schema_name: Name of Pydantic schema that failed validation
            response_snippet: First 500 chars of response
        """
        self.logger.warning(
            f"LLM Validation Error: {context.service}.{context.operation} - "
            f"Response didn't match {schema_name}",
            extra={
                "event": "llm_validation_error",
                "request_id": context.request_id,
                "service": context.service,
                "operation": context.operation,
                "schema_name": schema_name,
                "response_snippet": response_snippet,
            }
        )

    def log_retry(self, context: LLMRequestContext, attempt: int, max_retries: int, error: Exception):
        """Log a retry attempt.

        Args:
            context: Request context
            attempt: Current attempt number
            max_retries: Maximum retries allowed
            error: Error that triggered retry
        """
        self.logger.warning(
            f"LLM Request Retry: {context.service}.{context.operation} - "
            f"Attempt {attempt}/{max_retries} after {type(error).__name__}",
            extra={
                "event": "llm_request_retry",
                "request_id": context.request_id,
                "service": context.service,
                "operation": context.operation,
                "attempt": attempt,
                "max_retries": max_retries,
                "error_type": type(error).__name__,
                "error_message": str(error),
            }
        )

    def log_cost_alert(self, context: LLMRequestContext, threshold_usd: float):
        """Log high-cost request alert.

        Args:
            context: Request context
            threshold_usd: Cost threshold that was exceeded
        """
        self.logger.warning(
            f"LLM Cost Alert: {context.service}.{context.operation} cost ${context.cost_usd:.4f} "
            f"exceeded threshold ${threshold_usd:.4f}",
            extra={
                "event": "llm_cost_alert",
                "request_id": context.request_id,
                "service": context.service,
                "operation": context.operation,
                "cost_usd": context.cost_usd,
                "threshold_usd": threshold_usd,
                "model": context.model,
            }
        )

    def log_latency_alert(self, context: LLMRequestContext, threshold_ms: int):
        """Log high-latency request alert.

        Args:
            context: Request context
            threshold_ms: Latency threshold that was exceeded
        """
        self.logger.warning(
            f"LLM Latency Alert: {context.service}.{context.operation} took {context.response_time_ms}ms "
            f"(threshold: {threshold_ms}ms)",
            extra={
                "event": "llm_latency_alert",
                "request_id": context.request_id,
                "service": context.service,
                "operation": context.operation,
                "response_time_ms": context.response_time_ms,
                "threshold_ms": threshold_ms,
                "model": context.model,
            }
        )


# Global instance
_observability_logger: Optional[LLMObservabilityLogger] = None


def get_observability_logger() -> LLMObservabilityLogger:
    """Get or create observability logger singleton."""
    global _observability_logger
    if _observability_logger is None:
        _observability_logger = LLMObservabilityLogger()
    return _observability_logger


@contextmanager
def observe_llm_request(
    service: str,
    operation: str,
    model: str,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Context manager for observing LLM requests.

    Usage:
        with observe_llm_request("writer_service", "draft_email", "claude-3.5-sonnet") as ctx:
            result = await llm.generate_completion(...)
            ctx.prompt_tokens = result.usage.prompt_tokens
            ctx.completion_tokens = result.usage.completion_tokens
            ctx.total_tokens = result.usage.total_tokens
            ctx.cost_usd = result.usage.estimated_cost_usd
            ctx.response_time_ms = result.response_time_ms

    Args:
        service: Service name (e.g., "writer_service")
        operation: Operation name (e.g., "draft_email")
        model: LLM model being used
        request_id: Optional unique request ID
        metadata: Optional additional context
    """
    obs_logger = get_observability_logger()

    # Generate request ID if not provided
    if request_id is None:
        request_id = f"{service}_{operation}_{int(time.time() * 1000)}"

    context = LLMRequestContext(
        request_id=request_id,
        service=service,
        operation=operation,
        model=model,
        metadata=metadata or {}
    )

    start_time = time.time()
    obs_logger.log_request_start(context)

    try:
        yield context

        # Calculate response time if not already set
        if context.response_time_ms is None:
            context.response_time_ms = int((time.time() - start_time) * 1000)

        obs_logger.log_request_complete(context)

        # Alert on high costs (>$0.50 per request)
        if context.cost_usd and context.cost_usd > 0.5:
            obs_logger.log_cost_alert(context, threshold_usd=0.5)

        # Alert on high latency (>5000ms)
        if context.response_time_ms and context.response_time_ms > 5000:
            obs_logger.log_latency_alert(context, threshold_ms=5000)

    except Exception as e:
        context.response_time_ms = int((time.time() - start_time) * 1000)
        obs_logger.log_request_error(context, e)
        raise


def configure_json_logging():
    """Configure JSON-formatted logging for production use.

    Call this once at application startup to enable JSON logging.
    """
    import sys

    # Create JSON formatter
    class JSONFormatter(logging.Formatter):
        """Format log records as JSON."""

        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }

            # Add extra fields
            if hasattr(record, "__dict__"):
                for key, value in record.__dict__.items():
                    if key not in ["name", "msg", "args", "created", "filename", "funcName",
                                   "levelname", "levelno", "lineno", "module", "msecs",
                                   "pathname", "process", "processName", "relativeCreated",
                                   "thread", "threadName", "exc_info", "exc_text", "stack_info"]:
                        log_data[key] = value

            return json.dumps(log_data)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Add JSON handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    logger.info("JSON logging configured for LLM observability")

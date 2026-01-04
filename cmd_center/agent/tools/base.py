"""Base classes for agent tools."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Coroutine, Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar('T')


def run_async(coro: Coroutine[None, None, T]) -> T:
    """Run async code from sync context, handling existing event loops.

    This is needed because Textual TUI runs its own event loop,
    so we can't use asyncio.run() directly.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - safe to use asyncio.run()
        return asyncio.run(coro)

    # Already in async context - use nest_asyncio
    import nest_asyncio
    nest_asyncio.apply()
    return loop.run_until_complete(coro)


@dataclass
class ToolResult:
    """Result from executing a tool."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class PendingAction:
    """Represents a write action awaiting user confirmation.

    Write tools return this instead of executing immediately.
    User must confirm before the action is executed.
    """

    tool_name: str
    preview: str  # Human-readable preview of what will happen
    payload: dict  # Data needed to execute the action
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def pydantic_to_openai_schema(model: Type[BaseModel]) -> dict:
    """Convert Pydantic model to OpenAI function parameters schema.

    Args:
        model: Pydantic model class

    Returns:
        OpenAI-compatible parameters schema
    """
    json_schema = model.model_json_schema()

    # Remove $defs if present (not needed for OpenAI)
    schema = {
        "type": "object",
        "properties": json_schema.get("properties", {}),
    }

    # Add required fields if present
    if "required" in json_schema:
        schema["required"] = json_schema["required"]

    return schema


class BaseTool(ABC):
    """Base class for all agent tools."""

    name: str = ""
    description: str = ""
    parameters_model: Type[BaseModel] = BaseModel

    def get_openai_schema(self) -> dict:
        """Get OpenAI-compatible tool schema.

        Returns:
            Tool schema in OpenAI function format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": pydantic_to_openai_schema(self.parameters_model),
            }
        }

    @abstractmethod
    def execute(self, params: BaseModel) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            params: Validated parameters

        Returns:
            ToolResult with data or error
        """
        pass

    def parse_and_execute(self, arguments: dict) -> ToolResult:
        """Parse arguments and execute the tool.

        Args:
            arguments: Raw arguments dict from LLM

        Returns:
            ToolResult with data or error
        """
        try:
            params = self.parameters_model.model_validate(arguments)
            return self.execute(params)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

"""Base classes for agent tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, Type

from pydantic import BaseModel


@dataclass
class ToolResult:
    """Result from executing a tool."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


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

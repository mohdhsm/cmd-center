"""Tool registry for managing agent tools."""

from typing import Dict, List, Optional

from .base import BaseTool, ToolResult


class ToolRegistry:
    """Registry for agent tools."""

    def __init__(self):
        """Initialize empty registry."""
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool.

        Args:
            tool: Tool instance to register
        """
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool if found, None otherwise
        """
        return self.tools.get(name)

    def get_tools_schema(self) -> List[dict]:
        """Get OpenAI-compatible schema for all tools.

        Returns:
            List of tool schemas in OpenAI format
        """
        return [tool.get_openai_schema() for tool in self.tools.values()]

    def execute(self, name: str, arguments: dict) -> ToolResult:
        """Execute a tool by name.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            ToolResult with data or error
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found"
            )

        return tool.parse_and_execute(arguments)

    def list_tools(self) -> List[dict]:
        """List all registered tools with metadata.

        Returns:
            List of tool info dicts
        """
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self.tools.values()
        ]


# Singleton instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create tool registry singleton."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry

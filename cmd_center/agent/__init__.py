"""Omnious AI Agent module."""

from typing import TYPE_CHECKING

# Use lazy imports to avoid circular dependencies
# The actual imports happen when get_agent() or OmniousAgent are accessed
_agent_module = None


def get_agent():
    """Get or create agent singleton (lazy import)."""
    global _agent_module
    if _agent_module is None:
        from .core import agent as _mod
        _agent_module = _mod
    return _agent_module.get_agent()


def __getattr__(name):
    """Lazy loading of OmniousAgent class."""
    if name == "OmniousAgent":
        from .core.agent import OmniousAgent
        return OmniousAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["OmniousAgent", "get_agent"]

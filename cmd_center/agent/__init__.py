"""Omnious AI Agent module."""

# Defer imports to avoid circular dependencies and allow partial module testing
try:
    from .core.agent import OmniousAgent, get_agent
    __all__ = ["OmniousAgent", "get_agent"]
except ImportError:
    # Module not yet implemented
    __all__ = []

"""Agent core components."""

# Defer imports to avoid circular dependencies and allow partial module testing
try:
    from .agent import OmniousAgent, get_agent
    from .prompts import SYSTEM_PROMPT
    __all__ = ["OmniousAgent", "get_agent", "SYSTEM_PROMPT"]
except ImportError:
    # Modules not yet implemented
    __all__ = []

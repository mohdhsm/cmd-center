"""Loop registration and setup.

This module registers all loops with the global loop_registry.
Import this module during app startup to register loops.
"""

from .loop_engine import loop_registry
from .loops import (
    DocsExpiryLoop,
    BonusDueLoop,
    TaskOverdueLoop,
    ReminderProcessingLoop,
)


def register_loops() -> None:
    """Register all monitoring loops with the global registry."""
    loop_registry.register(DocsExpiryLoop())
    loop_registry.register(BonusDueLoop())
    loop_registry.register(TaskOverdueLoop())
    loop_registry.register(ReminderProcessingLoop())


# Auto-register on import
register_loops()


__all__ = ["register_loops"]

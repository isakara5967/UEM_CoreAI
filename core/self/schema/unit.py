from __future__ import annotations

"""Schema unit for the SELF system.

Represents the agent's body schema, sensor/actuator capabilities,
and general capacity model from the SELF perspective.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..self_core import SelfCore


class SchemaUnit:
    """Maintains a model of what the agent can sense and do."""

    def __init__(self, core: "SelfCore") -> None:
        self.core = core
        self.capabilities: Dict[str, Any] = {}
        self.limitations: Dict[str, Any] = {}

    def start(self) -> None:
        """Initialization logic that may read from world/perception config."""
        # TODO: query perception/world modules for initial body schema.
        pass

    def update(
        self,
        dt: float,
        world_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update schema based on changes in sensors/actuators/world."""
        # Placeholder: adjust capabilities/limitations when hardware changes.
        pass

    def export_state(self) -> Dict[str, Any]:
        """Return a serializable snapshot of the current schema."""
        return {
            "capabilities": dict(self.capabilities),
            "limitations": dict(self.limitations),
        }

    def notify_event(self, event: Dict[str, Any]) -> None:
        """React to events that change body or capability structure."""
        # Example: damage, upgrades, or mode switches.
        pass

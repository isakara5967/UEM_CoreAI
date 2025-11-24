from __future__ import annotations

"""Identity unit for the SELF system.

Responsible for relatively slow-changing self-properties such as
agent id, personality traits, social roles, and stable value profile
references coming from EthmorSynth.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..self_core import SelfCore


class IdentityUnit:
    """Maintains the agent's core identity representation."""

    def __init__(self, core: "SelfCore") -> None:
        self.core = core
        self.agent_id: str = self._init_agent_id()
        self.traits: Dict[str, float] = {}
        self.social_roles: Dict[str, Any] = {}
        self.value_profile: Optional[Dict[str, Any]] = None

    def _init_agent_id(self) -> str:
        """Initialize a stable agent identifier.

        Placeholder implementation; can be wired to config or memory.
        """
        return "UEM_AGENT"

    def start(self) -> None:
        """Perform any initialization that depends on other systems.

        Şu anda: EthmorSynth varsa, başlangıç value_profile'ını oradan çekmeye çalışır.
        """
        self.value_profile = None

        # SelfCore üzerindeki Ethmor referansını al
        ethmor = getattr(self.core, "ethmor_system", None)

        if ethmor is not None and hasattr(ethmor, "export_value_profile"):
            try:
                self.value_profile = ethmor.export_value_profile()
            except Exception:
                # Ethmor tarafında bir şey patlarsa SELF çökmemeli
                self.value_profile = None

    def update(
        self,
        dt: float,
        world_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update identity if needed (slow dynamics)."""
        # Şimdilik kimlik statik; gelecekte traits / social_roles buradan evrilir.
        pass

    def export_state(self) -> Dict[str, Any]:
        """Return a serializable snapshot of the identity state."""
        return {
            "agent_id": self.agent_id,
            "traits": dict(self.traits),
            "social_roles": dict(self.social_roles),
            "has_value_profile": self.value_profile is not None,
        }

    def notify_event(self, event: Dict[str, Any]) -> None:
        """Process salient events that might affect identity."""
        # Örn: büyük yaşam olayı → trait değişimi vs. (ileride)
        pass

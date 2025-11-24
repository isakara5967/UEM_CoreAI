from __future__ import annotations

"""Self system core orchestrator.

This module integrates SELF submodules (identity, continuity, reflection,
schema, drive_system, integrity_monitor) and exposes a unified self_state
to the rest of the UEM core.
"""

from typing import Any, Dict, Optional


class SelfCore:
    """Central SELF system orchestrator."""

    def __init__(
        self,
        memory_system: Any,
        emotion_system: Any,
        cognition_system: Any,
        planning_system: Any,
        metamind_system: Any,
        ethmor_system: Any,
        logger: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.memory_system = memory_system
        self.emotion_system = emotion_system
        self.cognition_system = cognition_system
        self.planning_system = planning_system
        self.metamind_system = metamind_system
        self.ethmor_system = ethmor_system

        self.logger = logger
        self.config = config or {}

        # Submodules (initialized in start())
        self.identity = None
        self.continuity = None
        self.reflection = None
        self.schema = None
        self.drive_system = None
        self.integrity_monitor = None

    def start(self) -> None:
        """Initialize SELF submodules."""
        from .identity.unit import IdentityUnit
        from .continuity.unit import ContinuityUnit
        from .reflection.unit import ReflectionUnit
        from .schema.unit import SchemaUnit
        from .drive_system.unit import DriveSystemUnit
        from .integrity_monitor.unit import IntegrityMonitorUnit

        self.identity = IdentityUnit(self)
        self.continuity = ContinuityUnit(self)
        self.reflection = ReflectionUnit(self)
        self.schema = SchemaUnit(self)
        self.drive_system = DriveSystemUnit(self)
        self.integrity_monitor = IntegrityMonitorUnit(self)

        # Alt modülleri başlat ve logla (diğer core sistemlerle aynı pattern)
        for unit_name, unit in [
            ("IdentityUnit", self.identity),
            ("ContinuityUnit", self.continuity),
            ("ReflectionUnit", self.reflection),
            ("SchemaUnit", self.schema),
            ("DriveSystemUnit", self.drive_system),
            ("IntegrityMonitorUnit", self.integrity_monitor),
        ]:
            if hasattr(unit, "start"):
                unit.start()
            print(f"     - {unit_name} subsystem loaded.")

        # İstersen logger üzerinden de ek log atmak için bırakıyorum:
        if self.logger is not None:
            self.logger.info("[UEM] Self system submodules initialized.")
            

    def update(self, dt: float, world_snapshot: Optional[Dict[str, Any]] = None) -> None:
        """Update SELF submodules for the current step.

        Args:
            dt: Simulation time-step.
            world_snapshot: Optional high-level snapshot from perception/world.
        """
        # Alt SELF ünitelerini sırayla güncelle
        for unit in (
            self.schema,
            self.identity,
            self.continuity,
            self.drive_system,
            self.reflection,
            self.integrity_monitor,
        ):
            if unit is not None and hasattr(unit, "update"):
                unit.update(dt, world_snapshot)

        # SELF durum raporunu MetaMind'e gönder (varsa)
        if (
            self.metamind_system is not None
            and hasattr(self.metamind_system, "receive_self_report")
        ):
            try:
                report = self.get_self_state()
                self.metamind_system.receive_self_report(report)
            except Exception:
                # MetaMind tarafında bir şey patlasa bile SELF çökmemeli
                if self.logger is not None:
                    self.logger.warning("Failed to send SELF report to MetaMind.")



    

    def get_self_state(self) -> Dict[str, Any]:
        """Return a unified SELF state representation."""
        state: Dict[str, Any] = {}

        if self.identity is not None and hasattr(self.identity, "export_state"):
            state["identity"] = self.identity.export_state()

        if self.continuity is not None and hasattr(self.continuity, "export_state"):
            state["continuity"] = self.continuity.export_state()

        if self.reflection is not None and hasattr(self.reflection, "export_state"):
            state["reflection"] = self.reflection.export_state()

        if self.schema is not None and hasattr(self.schema, "export_state"):
            state["schema"] = self.schema.export_state()

        if self.drive_system is not None and hasattr(self.drive_system, "export_state"):
            state["drive_system"] = self.drive_system.export_state()

        if self.integrity_monitor is not None and hasattr(
            self.integrity_monitor, "export_state"
        ):
            state["integrity"] = self.integrity_monitor.export_state()

        return state

    def notify_event(self, event: Dict[str, Any]) -> None:
        """Notify SELF about a salient internal or external event.

        Events that are self-relevant (identity-threatening, value-relevant,
        highly emotional, etc.) can be propagated to submodules.
        """
        for unit in (
            self.identity,
            self.continuity,
            self.reflection,
            self.schema,
            self.drive_system,
            self.integrity_monitor,
        ):
            if unit is not None and hasattr(unit, "notify_event"):
                unit.notify_event(event)

from __future__ import annotations

"""Self system core orchestrator.

This module integrates SELF submodules (identity, continuity, reflection,
schema, drive_system, integrity_monitor) and exposes a unified self_state
to the rest of the UEM core.
"""

from typing import Any, Dict, Optional

# NEW: Ontology layer-1 types
try:
    from core.ontology.types import (
        StateVector,
        SelfEntity,
        build_state_vector,
    )
except ImportError:
    # Ontology henüz yoksa, tipler opsiyonel olsun ki sistem çökmesin.
    StateVector = tuple  # type: ignore
    SelfEntity = dict    # type: ignore

    def build_state_vector(world_like: Any, emotion_like: Any) -> StateVector:  # type: ignore
        # Geçici fallback: nötr state
        return (0.5, 0.0, 0.5)


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

        # NEW: Ontology katmanı için ek alanlar
        self._state_vector: Optional[StateVector] = None
        self._last_world_snapshot: Optional[Dict[str, Any]] = None

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

    def _update_ontology_state_vector(
        self, world_snapshot: Optional[Dict[str, Any]]
    ) -> None:
        """NEW: Katman 1 ontology state_vector'ü güncelle.

        world_snapshot:
            integrated core'dan gelen WorldState benzeri yapı (dict veya dataclass).
        """
        if self.emotion_system is None:
            return

        if world_snapshot is None:
            return

        # Hem dataclass (WorldState) hem de dict ile çalışabilecek küçük bir adapter
        class _WorldAdapter:
            def __init__(self, snap: Any) -> None:
                if isinstance(snap, dict):
                    self.__dict__.update(snap)
                else:
                    # dataclass / obje ise zaten attribute'ları var
                    self.__dict__.update(snap.__dict__)

        try:
            world_like = _WorldAdapter(world_snapshot)
            self._state_vector = build_state_vector(world_like, self.emotion_system)
        except Exception as exc:  # pragma: no cover - savunma amaçlı
            if self.logger is not None:
                self.logger.warning(
                    f"[SELF] Failed to update ontology state_vector: {exc}"
                )

    def update(self, dt: float, world_snapshot: Optional[Dict[str, Any]] = None) -> None:
        """Update SELF submodules for the current step.

        Args:
            dt: Simulation time-step.
            world_snapshot: Optional high-level snapshot from perception/world.
        """
        # NEW: Son world snapshot'ı sakla ve ontolojik state_vector'ü güncelle
        if world_snapshot is not None:
            self._last_world_snapshot = world_snapshot
            self._update_ontology_state_vector(world_snapshot)

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

        # NEW: Ontoloji state vektörünü de rapora ekle (geri uyumlu ek alan)
        if self._state_vector is not None:
            state["ontology_state_vector"] = self._state_vector

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

    # NEW: Ontoloji katmanı için ek API'ler ------------------------------

    def get_state_vector(self) -> Optional[StateVector]:
        """Return current ontology Layer-1 state vector if available."""
        return self._state_vector

    def build_self_entity(self) -> Optional[SelfEntity]:
        """Create a Layer-1 SelfEntity snapshot for ontology-based modules.

        Şimdilik:
          - state_vector: _state_vector (yoksa nötr)
          - history: boş (ileride Memory/Consolidation bağlanacak)
          - goals: boş (ileride Planning bağlanacak)
        """
        if self._state_vector is None:
            # Henüz bir şey hesaplayamadıysa nötr state kullan
            state_vec: StateVector = (0.5, 0.0, 0.5)
        else:
            state_vec = self._state_vector

        try:
            entity = SelfEntity(state_vector=state_vec, history=[], goals=[])
        except Exception:
            # Ontology modülü henüz tam entegre değilse None döndür
            return None
        return entity

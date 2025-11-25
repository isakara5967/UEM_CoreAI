# core/self/self_core.py
"""Self system core orchestrator - Extended for Ontology Layer 1.

This module integrates SELF submodules (identity, continuity, reflection,
schema, drive_system, integrity_monitor) and exposes a unified self_state
to the rest of the UEM core.

Extended features:
- StateVector tracking with history
- Goal management
- State delta computation (for ETHMOR)
- Event history for empathy/memory

Author: UEM Project
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Dict, List, Optional, Deque

# Ontology layer-1 types
try:
    from core.ontology.types import (
        StateVector,
        StateDelta,
        SelfEntity,
        Event,
        Goal,
        build_state_vector,
        compute_state_delta,
    )
    ONTOLOGY_AVAILABLE = True
except ImportError:
    # Ontology henüz yoksa, tipler opsiyonel olsun ki sistem çökmesin.
    StateVector = tuple  # type: ignore
    StateDelta = tuple   # type: ignore
    SelfEntity = dict    # type: ignore
    Event = dict         # type: ignore
    Goal = dict          # type: ignore
    ONTOLOGY_AVAILABLE = False

    def build_state_vector(world_like: Any, emotion_like: Any) -> tuple:
        return (0.5, 0.0, 0.5)
    
    def compute_state_delta(before: tuple, after: tuple) -> tuple:
        return tuple(a - b for a, b in zip(after, before))


class SelfCore:
    """Central SELF system orchestrator with Ontology Layer 1 support."""

    # Configuration defaults
    DEFAULT_HISTORY_SIZE = 100
    DEFAULT_GOAL_LIMIT = 10

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

        # =====================================================================
        # ONTOLOGY LAYER 1 - State Tracking
        # =====================================================================
        
        # Current state
        self._state_vector: Optional[StateVector] = None
        self._previous_state_vector: Optional[StateVector] = None
        self._last_world_snapshot: Optional[Dict[str, Any]] = None
        
        # State history (for empathy/memory)
        history_size = self.config.get('history_size', self.DEFAULT_HISTORY_SIZE)
        self._state_history: Deque[StateVector] = deque(maxlen=history_size)
        
        # Event history
        self._event_history: Deque[Event] = deque(maxlen=history_size)
        
        # Goals
        goal_limit = self.config.get('goal_limit', self.DEFAULT_GOAL_LIMIT)
        self._goals: List[Goal] = []
        self._goal_limit = goal_limit
        
        # Timing
        self._last_update_time: float = time.time()
        self._tick_count: int = 0

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

        # Alt modülleri başlat ve logla
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

        if self.logger is not None:
            self.logger.info("[UEM] Self system submodules initialized.")
        
        # Initialize default survival goal
        self._init_default_goals()

    def _init_default_goals(self) -> None:
        """Initialize default goals for SELF."""
        if ONTOLOGY_AVAILABLE:
            # Survival goal: high resource, low threat, high wellbeing
            survival_goal = Goal(
                name="survive",
                target_state=(1.0, 0.0, 1.0),
                priority=1.0
            )
            self._goals.append(survival_goal)

    # =========================================================================
    # STATE VECTOR MANAGEMENT
    # =========================================================================

    def _update_ontology_state_vector(
        self, world_snapshot: Optional[Dict[str, Any]]
    ) -> None:
        """Update Layer 1 ontology state_vector.

        Args:
            world_snapshot: WorldState benzeri yapı (dict veya dataclass).
        """
        if self.emotion_system is None:
            return

        if world_snapshot is None:
            return

        # Adapter for both dict and dataclass
        class _WorldAdapter:
            def __init__(self, snap: Any) -> None:
                if isinstance(snap, dict):
                    # Ensure required fields exist with defaults
                    self.player_health = snap.get('player_health', 1.0)
                    self.player_energy = snap.get('player_energy', 1.0)
                    self.danger_level = snap.get('danger_level', 0.0)
                else:
                    self.player_health = getattr(snap, 'player_health', 1.0)
                    self.player_energy = getattr(snap, 'player_energy', 1.0)
                    self.danger_level = getattr(snap, 'danger_level', 0.0)

        try:
            world_like = _WorldAdapter(world_snapshot)
            
            # Store previous state for delta computation
            self._previous_state_vector = self._state_vector
            
            # Compute new state
            self._state_vector = build_state_vector(world_like, self.emotion_system)
            
            # Add to history
            if self._state_vector is not None:
                self._state_history.append(self._state_vector)
            
            self._tick_count += 1
            
        except Exception as exc:
            if self.logger is not None:
                self.logger.warning(
                    f"[SELF] Failed to update ontology state_vector: {exc}"
                )

    def get_state_vector(self) -> Optional[StateVector]:
        """Return current ontology Layer-1 state vector."""
        return self._state_vector

    def get_previous_state_vector(self) -> Optional[StateVector]:
        """Return previous state vector (for delta computation)."""
        return self._previous_state_vector

    def get_state_delta(self) -> Optional[StateDelta]:
        """Compute delta between current and previous state.
        
        Returns:
            StateDelta (resource_delta, threat_delta, wellbeing_delta) or None
        """
        if self._state_vector is None or self._previous_state_vector is None:
            return None
        
        return compute_state_delta(self._previous_state_vector, self._state_vector)

    def get_state_history(self, n: Optional[int] = None) -> List[StateVector]:
        """Get recent state history.
        
        Args:
            n: Number of recent states to return. None = all.
            
        Returns:
            List of StateVectors, oldest first.
        """
        if n is None:
            return list(self._state_history)
        return list(self._state_history)[-n:]

    # =========================================================================
    # EVENT HISTORY MANAGEMENT
    # =========================================================================

    def record_event(self, event: Event) -> None:
        """Record an event in SELF's history.
        
        Args:
            event: Ontology Event object
        """
        self._event_history.append(event)
        
        # Notify submodules
        self.notify_event({
            'type': 'ontology_event',
            'source': event.source,
            'target': event.target,
            'effect': event.effect,
            'timestamp': event.timestamp,
        })

    def create_and_record_event(
        self,
        source: str,
        target: str,
        effect: Optional[StateDelta] = None,
        timestamp: Optional[float] = None,
    ) -> Optional[Event]:
        """Create an event from current state change and record it.
        
        Args:
            source: Event source ('SELF', 'OTHER:<id>', 'ENVIRONMENT')
            target: Event target
            effect: StateDelta, or None to compute from current delta
            timestamp: Event time, or None to use current time
            
        Returns:
            Created Event or None if cannot create
        """
        if not ONTOLOGY_AVAILABLE:
            return None
        
        if effect is None:
            effect = self.get_state_delta()
            if effect is None:
                effect = (0.0, 0.0, 0.0)
        
        if timestamp is None:
            timestamp = time.time()
        
        event = Event(
            source=source,
            target=target,
            effect=effect,
            timestamp=timestamp,
        )
        
        self.record_event(event)
        return event

    def get_event_history(self, n: Optional[int] = None) -> List[Event]:
        """Get recent event history.
        
        Args:
            n: Number of recent events to return. None = all.
            
        Returns:
            List of Events, oldest first.
        """
        if n is None:
            return list(self._event_history)
        return list(self._event_history)[-n:]

    # =========================================================================
    # GOAL MANAGEMENT
    # =========================================================================

    def add_goal(self, goal: Goal) -> bool:
        """Add a goal to SELF.
        
        Args:
            goal: Ontology Goal object
            
        Returns:
            True if added, False if limit reached or duplicate
        """
        if not ONTOLOGY_AVAILABLE:
            return False
        
        # Check for duplicate
        for existing in self._goals:
            if existing.name == goal.name:
                # Update existing goal
                existing.target_state = goal.target_state
                existing.priority = goal.priority
                return True
        
        # Check limit
        if len(self._goals) >= self._goal_limit:
            # Remove lowest priority goal
            self._goals.sort(key=lambda g: g.priority, reverse=True)
            self._goals.pop()
        
        self._goals.append(goal)
        self._goals.sort(key=lambda g: g.priority, reverse=True)
        return True

    def remove_goal(self, name: str) -> bool:
        """Remove a goal by name.
        
        Args:
            name: Goal name
            
        Returns:
            True if removed, False if not found
        """
        for i, goal in enumerate(self._goals):
            if goal.name == name:
                self._goals.pop(i)
                return True
        return False

    def get_goals(self) -> List[Goal]:
        """Get all current goals, sorted by priority."""
        return list(self._goals)

    def get_primary_goal(self) -> Optional[Goal]:
        """Get highest priority goal."""
        if self._goals:
            return self._goals[0]
        return None

    # =========================================================================
    # SELF ENTITY BUILDING (for ETHMOR)
    # =========================================================================

    def build_self_entity(self) -> Optional[SelfEntity]:
        """Create a Layer-1 SelfEntity snapshot.
        
        This is the primary interface for ETHMOR and other modules
        that need SELF's ontological representation.
        
        Returns:
            SelfEntity with current state, history, and goals
        """
        if not ONTOLOGY_AVAILABLE:
            return None
        
        # State vector (default to neutral if not computed yet)
        state_vec = self._state_vector
        if state_vec is None:
            state_vec = (0.5, 0.0, 0.5)
        
        # Event history (recent events)
        history = self.get_event_history(n=20)
        
        # Goals
        goals = self.get_goals()
        
        try:
            return SelfEntity(
                state_vector=state_vec,
                history=history,
                goals=goals,
            )
        except Exception:
            return None

    # =========================================================================
    # ETHMOR INTERFACE
    # =========================================================================

    def get_ethmor_context(self) -> Dict[str, Any]:
        """Build context dict for ETHMOR evaluation.
        
        Returns:
            Dict containing all data ETHMOR needs for constraint checking
        """
        context = {
            'self_entity': self.build_self_entity(),
            'state_vector': self._state_vector,
            'previous_state_vector': self._previous_state_vector,
            'state_delta': self.get_state_delta(),
            'goals': self.get_goals(),
            'tick': self._tick_count,
        }
        
        # Add state components for easy access
        if self._state_vector:
            context['RESOURCE_LEVEL'] = self._state_vector[0]
            context['THREAT_LEVEL'] = self._state_vector[1]
            context['WELLBEING'] = self._state_vector[2]
        
        if self._previous_state_vector:
            context['RESOURCE_LEVEL_before'] = self._previous_state_vector[0]
            context['THREAT_LEVEL_before'] = self._previous_state_vector[1]
            context['WELLBEING_before'] = self._previous_state_vector[2]
        
        delta = self.get_state_delta()
        if delta:
            context['RESOURCE_LEVEL_delta'] = delta[0]
            context['THREAT_LEVEL_delta'] = delta[1]
            context['WELLBEING_delta'] = delta[2]
        
        return context

    def predict_state_after_action(
        self,
        action_name: str,
        predicted_effects: Dict[str, float],
    ) -> Optional[StateVector]:
        """Predict state vector after an action.
        
        Args:
            action_name: Name of the action
            predicted_effects: Dict with keys like 'health_delta', 'danger_delta', etc.
            
        Returns:
            Predicted StateVector or None
        """
        if self._state_vector is None:
            return None
        
        resource, threat, wellbeing = self._state_vector
        
        # Apply predicted effects
        health_delta = predicted_effects.get('health_delta', 0.0)
        energy_delta = predicted_effects.get('energy_delta', 0.0)
        danger_delta = predicted_effects.get('danger_delta', 0.0)
        valence_delta = predicted_effects.get('valence_delta', 0.0)
        
        # Compute new values
        new_resource = max(0.0, min(1.0, resource + (health_delta + energy_delta) / 2))
        new_threat = max(0.0, min(1.0, threat + danger_delta))
        
        # Wellbeing is derived from valence, approximate adjustment
        new_wellbeing = max(0.0, min(1.0, wellbeing + valence_delta / 2))
        
        return (new_resource, new_threat, new_wellbeing)

    # =========================================================================
    # MAIN UPDATE LOOP
    # =========================================================================

    def update(self, dt: float, world_snapshot: Optional[Dict[str, Any]] = None) -> None:
        """Update SELF submodules for the current step.

        Args:
            dt: Simulation time-step.
            world_snapshot: Optional WorldState snapshot.
        """
        # Update ontological state vector
        if world_snapshot is not None:
            self._last_world_snapshot = world_snapshot
            self._update_ontology_state_vector(world_snapshot)

        # Update submodules
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

        # Send report to MetaMind
        if (
            self.metamind_system is not None
            and hasattr(self.metamind_system, "receive_self_report")
        ):
            try:
                report = self.get_self_state()
                self.metamind_system.receive_self_report(report)
            except Exception:
                if self.logger is not None:
                    self.logger.warning("Failed to send SELF report to MetaMind.")

        self._last_update_time = time.time()

    # =========================================================================
    # STATE EXPORT
    # =========================================================================

    def get_self_state(self) -> Dict[str, Any]:
        """Return a unified SELF state representation."""
        state: Dict[str, Any] = {}

        # Submodule states
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

        # Ontology state
        state["ontology"] = {
            "state_vector": self._state_vector,
            "previous_state_vector": self._previous_state_vector,
            "state_delta": self.get_state_delta(),
            "history_length": len(self._event_history),
            "goals": [
                {"name": g.name, "priority": g.priority}
                for g in self._goals
            ] if ONTOLOGY_AVAILABLE else [],
            "tick": self._tick_count,
        }

        return state

    def notify_event(self, event: Dict[str, Any]) -> None:
        """Notify SELF about a salient event.

        Events that are self-relevant can be propagated to submodules.
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

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get SELF system statistics."""
        return {
            "tick_count": self._tick_count,
            "state_history_size": len(self._state_history),
            "event_history_size": len(self._event_history),
            "goal_count": len(self._goals),
            "ontology_available": ONTOLOGY_AVAILABLE,
            "last_update": self._last_update_time,
        }

    def reset_history(self) -> None:
        """Clear state and event history."""
        self._state_history.clear()
        self._event_history.clear()
        self._previous_state_vector = None

# core/self/self_core.py
"""Self system core orchestrator - v1 with Working Memory.

This module integrates SELF submodules (identity, continuity, reflection,
schema, drive_system, integrity_monitor) and exposes a unified self_state
to the rest of the UEM core.

v1 Features (Memory-independent):
- StateVector tracking with history (deque)
- State delta computation
- Event history (internal working memory)
- Goal management with priority sorting
- ETHMOR context building
- State prediction for action evaluation

Author: UEM Project
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Dict, List, Optional, Deque, Tuple

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
    # Ontology henüz yoksa, tipler opsiyonel olsun
    StateVector = Tuple[float, float, float]  # type: ignore
    StateDelta = Tuple[float, float, float]   # type: ignore
    ONTOLOGY_AVAILABLE = False

    def build_state_vector(world_like: Any, emotion_like: Any) -> Tuple[float, float, float]:
        """Fallback state vector builder."""
        try:
            health = getattr(world_like, 'player_health', 0.5)
            energy = getattr(world_like, 'player_energy', 0.5)
            danger = getattr(world_like, 'danger_level', 0.0)
            valence = getattr(emotion_like, 'valence', 0.0)
        except:
            return (0.5, 0.0, 0.5)
        
        resource = max(0.0, min(1.0, (health + energy) / 2.0))
        threat = max(0.0, min(1.0, danger))
        wellbeing = max(0.0, min(1.0, (valence + 1.0) / 2.0))
        return (resource, threat, wellbeing)
    
    def compute_state_delta(before: Tuple, after: Tuple) -> Tuple[float, float, float]:
        """Fallback delta computation."""
        return tuple(a - b for a, b in zip(after, before))  # type: ignore


# Fallback dataclasses if ontology not available
if not ONTOLOGY_AVAILABLE:
    from dataclasses import dataclass, field
    
    @dataclass
    class Event:
        source: str
        target: str
        effect: Tuple[float, float, float]
        timestamp: float
    
    @dataclass
    class Goal:
        name: str
        target_state: Tuple[float, float, float]
        priority: float = 1.0
    
    @dataclass
    class SelfEntity:
        state_vector: Tuple[float, float, float]
        history: List[Any] = field(default_factory=list)
        goals: List[Any] = field(default_factory=list)


class SelfCore:
    """Central SELF system orchestrator with Working Memory.
    
    v1: Memory-independent, uses internal deques for history.
    v2: Will add optional Memory system integration.
    """

    # Default configuration
    DEFAULT_CONFIG = {
        'history_size': 100,      # Max state history entries
        'event_history_size': 500, # Max event history entries
        'goal_limit': 10,          # Max concurrent goals
        'default_survival_goal': True,
    }

    def __init__(
        self,
        memory_system: Any = None,
        emotion_system: Any = None,
        cognition_system: Any = None,
        planning_system: Any = None,
        metamind_system: Any = None,
        ethmor_system: Any = None,
        logger: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        # External system references
        self.memory_system = memory_system
        self.emotion_system = emotion_system
        self.cognition_system = cognition_system
        self.planning_system = planning_system
        self.metamind_system = metamind_system
        self.ethmor_system = ethmor_system

        self.logger = logger
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}

        # Submodules (initialized in start())
        self.identity = None
        self.continuity = None
        self.reflection = None
        self.schema = None
        self.drive_system = None
        self.integrity_monitor = None

        # =====================================================================
        # v1 WORKING MEMORY - Internal State Tracking
        # =====================================================================
        
        # State vector tracking
        self._state_vector: Optional[StateVector] = None
        self._previous_state_vector: Optional[StateVector] = None
        self._state_delta: Optional[StateDelta] = None
        
        # History deques (Working Memory)
        # Note: If event_history_size not explicitly set, use history_size
        history_size = self.config.get('history_size', 100)
        # Check if event_history_size was explicitly provided in user config
        if config and 'event_history_size' in config:
            event_history_size = config['event_history_size']
        elif config and 'history_size' in config:
            # User set history_size but not event_history_size, use history_size
            event_history_size = history_size
        else:
            # Use default
            event_history_size = self.config.get('event_history_size', 500)
        
        self._state_history: Deque[StateVector] = deque(maxlen=history_size)
        self._delta_history: Deque[StateDelta] = deque(maxlen=history_size)
        self._event_history: Deque[Event] = deque(maxlen=event_history_size)
        
        # Goal management
        self._goals: List[Goal] = []
        self._goal_limit = self.config.get('goal_limit', 10)
        
        # Tick counter
        self._tick_count: int = 0
        
        # Last world snapshot for context
        self._last_world_snapshot: Optional[Dict[str, Any]] = None

    # =========================================================================
    # INITIALIZATION
    # =========================================================================

    def start(self) -> None:
        """Initialize SELF submodules."""
        try:
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
                if self.logger:
                    self.logger.info(f"  - {unit_name} subsystem loaded.")

        except ImportError as e:
            if self.logger:
                self.logger.warning(f"[SELF] Submodules not available: {e}")
        
        # Initialize default goals
        if self.config.get('default_survival_goal', True):
            self._init_default_goals()

    def _init_default_goals(self) -> None:
        """Initialize default survival goal."""
        if ONTOLOGY_AVAILABLE:
            from core.ontology.types import Goal as OntologyGoal
            survival = OntologyGoal(
                name="survive",
                target_state=(1.0, 0.0, 1.0),  # Max resource, min threat, max wellbeing
                priority=1.0,
            )
        else:
            survival = Goal(
                name="survive",
                target_state=(1.0, 0.0, 1.0),
                priority=1.0,
            )
        
        if not any(g.name == "survive" for g in self._goals):
            self._goals.append(survival)
            self._sort_goals()

    # =========================================================================
    # UPDATE CYCLE
    # =========================================================================

    def update(self, dt: float, world_snapshot: Optional[Dict[str, Any]] = None) -> None:
        """Update SELF for the current step.

        Args:
            dt: Simulation time-step.
            world_snapshot: Optional high-level snapshot from perception/world.
        """
        self._tick_count += 1
        
        # Save previous state before computing new one
        if self._state_vector is not None:
            self._previous_state_vector = self._state_vector
        
        # Update world snapshot and compute new state vector
        if world_snapshot is not None:
            self._last_world_snapshot = world_snapshot
            self._update_state_vector(world_snapshot)
        
        # Compute delta if we have previous state
        if self._previous_state_vector is not None and self._state_vector is not None:
            self._state_delta = compute_state_delta(
                self._previous_state_vector,
                self._state_vector
            )
            self._delta_history.append(self._state_delta)
        else:
            self._state_delta = None
        
        # Update submodules
        self._update_submodules(dt, world_snapshot)
        
        # Send report to MetaMind if available
        self._send_metamind_report()
        
        # v2: Write to Memory if available
        if self.memory_system is not None:
            self._write_to_memory()

    def _update_state_vector(self, world_snapshot: Dict[str, Any]) -> None:
        """Compute and store new state vector from world snapshot."""
        if self.emotion_system is None:
            return
        
        # Adapt world_snapshot to WorldStateLike interface
        class _WorldAdapter:
            def __init__(self, snap: Dict[str, Any]) -> None:
                self.player_health = snap.get('player_health', 0.5)
                self.player_energy = snap.get('player_energy', 0.5)
                self.danger_level = snap.get('danger_level', 0.0)
        
        try:
            world_like = _WorldAdapter(world_snapshot)
            self._state_vector = build_state_vector(world_like, self.emotion_system)
            self._state_history.append(self._state_vector)
        except Exception as exc:
            if self.logger:
                self.logger.warning(f"[SELF] Failed to update state_vector: {exc}")

    def _update_submodules(self, dt: float, world_snapshot: Optional[Dict[str, Any]]) -> None:
        """Update SELF submodules."""
        for unit in (
            self.schema,
            self.identity,
            self.continuity,
            self.drive_system,
            self.reflection,
            self.integrity_monitor,
        ):
            if unit is not None and hasattr(unit, "update"):
                try:
                    unit.update(dt, world_snapshot)
                except Exception:
                    pass  # Submodule errors don't crash SELF

    def _send_metamind_report(self) -> None:
        """Send SELF state report to MetaMind."""
        if self.metamind_system is None:
            return
        
        if not hasattr(self.metamind_system, "receive_self_report"):
            return
        
        try:
            report = self.get_self_state()
            self.metamind_system.receive_self_report(report)
        except Exception:
            if self.logger:
                self.logger.warning("[SELF] Failed to send report to MetaMind.")

    def _write_to_memory(self) -> None:
        """v2: Write state snapshot to Memory system (if available)."""
        # This is a placeholder for v2
        # Will be implemented when Memory system is ready
        pass

    # =========================================================================
    # STATE VECTOR API
    # =========================================================================

    def get_state_vector(self) -> Optional[StateVector]:
        """Return current state vector (RESOURCE, THREAT, WELLBEING)."""
        return self._state_vector

    def get_previous_state_vector(self) -> Optional[StateVector]:
        """Return previous state vector."""
        return self._previous_state_vector

    def get_state_delta(self) -> Optional[StateDelta]:
        """Return current state delta (change from previous state)."""
        return self._state_delta

    def get_state_history(self) -> List[StateVector]:
        """Return state history as list."""
        return list(self._state_history)

    def get_delta_history(self) -> List[StateDelta]:
        """Return delta history as list."""
        return list(self._delta_history)

    # =========================================================================
    # EVENT HISTORY API
    # =========================================================================

    def record_event(self, event: Event) -> None:
        """Record an event to history."""
        self._event_history.append(event)
        
        # v2: Also write to Memory if available
        if self.memory_system is not None and hasattr(self.memory_system, 'store_event'):
            try:
                self.memory_system.store_event(event)
            except Exception:
                pass

    def create_and_record_event(
        self,
        source: str,
        target: str,
        effect: Optional[StateDelta] = None,
    ) -> Optional[Event]:
        """Create an event from current state delta and record it.
        
        If effect is not provided, uses current state delta.
        """
        # Use current delta if no effect provided
        if effect is None:
            if self._state_delta is not None:
                effect = self._state_delta
            else:
                effect = (0.0, 0.0, 0.0)
        
        # Create event
        if ONTOLOGY_AVAILABLE:
            from core.ontology.types import Event as OntologyEvent
            event = OntologyEvent(
                source=source,
                target=target,
                effect=effect,
                timestamp=time.time(),
            )
        else:
            event = Event(
                source=source,
                target=target,
                effect=effect,
                timestamp=time.time(),
            )
        
        self.record_event(event)
        return event

    def get_event_history(self) -> List[Event]:
        """Return event history as list."""
        return list(self._event_history)

    def get_recent_events(self, n: int = 10) -> List[Event]:
        """Return last n events."""
        history = list(self._event_history)
        return history[-n:] if len(history) >= n else history

    # =========================================================================
    # GOAL MANAGEMENT API
    # =========================================================================

    def add_goal(self, goal: Goal) -> bool:
        """Add a goal. Returns True if added, False if limit reached."""
        # Check if goal already exists
        if any(g.name == goal.name for g in self._goals):
            return False
        
        # Check limit
        if len(self._goals) >= self._goal_limit:
            # Remove lowest priority goal to make room
            self._goals.sort(key=lambda g: g.priority, reverse=True)
            self._goals = self._goals[:self._goal_limit - 1]
        
        self._goals.append(goal)
        self._sort_goals()
        return True

    def remove_goal(self, name: str) -> bool:
        """Remove a goal by name. Returns True if removed."""
        for i, goal in enumerate(self._goals):
            if goal.name == name:
                self._goals.pop(i)
                return True
        return False

    def get_goals(self) -> List[Goal]:
        """Return goals sorted by priority (highest first)."""
        return list(self._goals)

    def get_primary_goal(self) -> Optional[Goal]:
        """Return highest priority goal."""
        if not self._goals:
            return None
        return self._goals[0]

    def _sort_goals(self) -> None:
        """Sort goals by priority (highest first)."""
        self._goals.sort(key=lambda g: g.priority, reverse=True)

    # =========================================================================
    # SELF ENTITY API
    # =========================================================================

    def build_self_entity(self) -> SelfEntity:
        """Build a SelfEntity snapshot for ontology-based modules.
        
        Returns a complete SelfEntity with:
        - Current state_vector (or neutral default)
        - Recent event history
        - Current goals
        """
        # State vector
        if self._state_vector is not None:
            state_vec = self._state_vector
        else:
            state_vec = (0.5, 0.0, 0.5)  # Neutral default
        
        # Get recent events and goals
        recent_events = self.get_recent_events(20)
        goals = self.get_goals()
        
        # Build entity
        if ONTOLOGY_AVAILABLE:
            from core.ontology.types import SelfEntity as OntologySelfEntity
            entity = OntologySelfEntity(
                state_vector=state_vec,
                history=recent_events,
                goals=goals,
            )
        else:
            entity = SelfEntity(
                state_vector=state_vec,
                history=recent_events,
                goals=goals,
            )
        
        return entity

    # =========================================================================
    # ETHMOR CONTEXT API
    # =========================================================================

    def get_ethmor_context(self) -> Dict[str, Any]:
        """Build context dictionary for ETHMOR evaluation.
        
        Returns context with before/after state levels for constraint evaluation.
        
        Key naming:
        - RESOURCE_LEVEL, THREAT_LEVEL, WELLBEING: Current values (aliases)
        - *_before: Previous update values
        - *_after: Current values (same as above, for prediction update)
        - *_delta: Change from before to after
        """
        # Current state (this is "after" the last update)
        if self._state_vector is not None:
            resource_current, threat_current, wellbeing_current = self._state_vector
        else:
            resource_current, threat_current, wellbeing_current = 0.5, 0.0, 0.5
        
        # Previous state (this is "before" the last update)
        if self._previous_state_vector is not None:
            resource_before, threat_before, wellbeing_before = self._previous_state_vector
        else:
            resource_before, threat_before, wellbeing_before = resource_current, threat_current, wellbeing_current
        
        # Compute deltas (current - previous)
        resource_delta = resource_current - resource_before
        threat_delta = threat_current - threat_before
        wellbeing_delta = wellbeing_current - wellbeing_before
        
        # Build self_entity
        self_entity = self.build_self_entity()
        
        return {
            # Current state vector
            'state_vector': self._state_vector,
            
            # Current values (aliases for convenience)
            'RESOURCE_LEVEL': resource_current,
            'THREAT_LEVEL': threat_current,
            'WELLBEING': wellbeing_current,
            
            # Before values (previous state)
            'RESOURCE_LEVEL_before': resource_before,
            'THREAT_LEVEL_before': threat_before,
            'WELLBEING_before': wellbeing_before,
            
            # After values (current state - for action prediction to update)
            'RESOURCE_LEVEL_after': resource_current,
            'THREAT_LEVEL_after': threat_current,
            'WELLBEING_after': wellbeing_current,
            
            # Delta values
            'RESOURCE_LEVEL_delta': resource_delta,
            'THREAT_LEVEL_delta': threat_delta,
            'WELLBEING_delta': wellbeing_delta,
            
            # Previous values (alternative naming)
            'previous_resource': resource_before,
            'previous_threat': threat_before,
            'previous_wellbeing': wellbeing_before,
            
            # Self entity
            'self_entity': self_entity,
        }

    # =========================================================================
    # STATE PREDICTION API
    # =========================================================================

    def predict_state_after_action(
        self,
        action_name: str,
        predicted_effects: Dict[str, float],
    ) -> Optional[StateVector]:
        """Predict state vector after applying action effects.
        
        Args:
            action_name: Name of the action
            predicted_effects: Dict with 'health_delta', 'energy_delta', 'danger_delta'
        
        Returns:
            Predicted state vector (resource, threat, wellbeing)
        """
        if self._state_vector is None:
            return None
        
        current_resource, current_threat, current_wellbeing = self._state_vector
        
        # Get deltas
        health_delta = predicted_effects.get('health_delta', 0.0)
        energy_delta = predicted_effects.get('energy_delta', 0.0)
        danger_delta = predicted_effects.get('danger_delta', 0.0)
        
        # Compute predicted state
        # Resource = (health + energy) / 2
        # So resource_delta = (health_delta + energy_delta) / 2
        resource_delta = (health_delta + energy_delta) / 2.0
        predicted_resource = max(0.0, min(1.0, current_resource + resource_delta))
        
        # Threat = danger_level
        predicted_threat = max(0.0, min(1.0, current_threat + danger_delta))
        
        # Wellbeing stays same (would need emotion prediction for accuracy)
        predicted_wellbeing = current_wellbeing
        
        return (predicted_resource, predicted_threat, predicted_wellbeing)

    # =========================================================================
    # UNIFIED STATE API
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

        if self.integrity_monitor is not None and hasattr(self.integrity_monitor, "export_state"):
            state["integrity"] = self.integrity_monitor.export_state()

        # Ontology state section
        state["ontology"] = {
            "state_vector": self._state_vector,
            "previous_state_vector": self._previous_state_vector,
            "state_delta": self._state_delta,
            "tick": self._tick_count,
        }
        
        # Legacy field for backward compatibility
        if self._state_vector is not None:
            state["ontology_state_vector"] = self._state_vector

        return state

    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about SELF state."""
        return {
            'tick_count': self._tick_count,
            'state_history_size': len(self._state_history),
            'delta_history_size': len(self._delta_history),
            'event_history_size': len(self._event_history),
            'goal_count': len(self._goals),
            'has_state_vector': self._state_vector is not None,
            'has_memory_system': self.memory_system is not None,
        }

    # =========================================================================
    # EVENT NOTIFICATION
    # =========================================================================

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
                try:
                    unit.notify_event(event)
                except Exception:
                    pass  # Submodule errors don't crash SELF

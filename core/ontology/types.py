# core/ontology/types.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Protocol, Dict, Any
import math


# ---- Primitive Types ------------------------------------------------------

StateVector = Tuple[float, float, float]   # (resource, threat, wellbeing)
StateDelta = Tuple[float, float, float]


@dataclass
class Event:
    source: str          # 'SELF', 'OTHER:<id>', 'ENVIRONMENT'
    target: str          # same format
    effect: StateDelta   # delta on (resource, threat, wellbeing)
    timestamp: float


@dataclass
class Goal:
    name: str
    target_state: StateVector
    priority: float = 1.0


@dataclass
class SelfEntity:
    state_vector: StateVector
    history: List[Event] = field(default_factory=list)
    goals: List[Goal] = field(default_factory=list)


@dataclass
class OtherEntity:
    id: str
    observed_state: StateVector
    predicted_state: Optional[StateVector] = None


# ---- Interfaces to existing modules --------------------------------------


class WorldStateLike(Protocol):
    player_health: float
    player_energy: float
    danger_level: float


class EmotionCoreLike(Protocol):
    valence: float   # -1 .. +1


class EthmorLike(Protocol):
    def check_constraint_breach(self, event: Event, context: Dict[str, Any]) -> float:
        """
        Return violation level in [0, 1].
        Concrete EthmorSynthSystem will implement this.
        """
        ...


# ---- State construction helpers ------------------------------------------


def build_state_vector(world: WorldStateLike, emotion: EmotionCoreLike) -> StateVector:
    """Compute (RESOURCE_LEVEL, THREAT_LEVEL, WELLBEING) from modules."""
    resource = max(0.0, min(1.0, (world.player_health + world.player_energy) / 2.0))
    threat = max(0.0, min(1.0, world.danger_level))
    wellbeing = max(0.0, min(1.0, (emotion.valence + 1.0) / 2.0))
    return (resource, threat, wellbeing)


def compute_state_delta(before: StateVector, after: StateVector) -> StateDelta:
    return tuple(a - b for a, b in zip(after, before))  # type: ignore


# ---- VALUE functions ------------------------------------------------------


def compute_benefit(wellbeing_before: float, wellbeing_after: float) -> float:
    return max(0.0, wellbeing_after - wellbeing_before)


def compute_cost(resource_before: float, resource_after: float) -> float:
    return max(0.0, resource_before - resource_after)


def compute_violation(
    ethmor: EthmorLike, event: Event, context: Dict[str, Any]
) -> float:
    """Delegate to ETHMOR. This keeps ontology independent from implementation."""
    return ethmor.check_constraint_breach(event, context)


# ---- RELATION helpers -----------------------------------------------------


def causes(event: Event) -> StateDelta:
    """By design, EVENT.effect already is the StateDelta."""
    return event.effect


def affects(
    entity: SelfEntity | OtherEntity, event: Event, wellbeing_before: float, wellbeing_after: float
) -> float:
    """Return wellbeing delta caused by event on given entity."""
    return wellbeing_after - wellbeing_before


def similar(state_a: StateVector, state_b: StateVector) -> float:
    """Cosine similarity between two state vectors."""
    ax, ay, az = state_a
    bx, by, bz = state_b
    dot = ax * bx + ay * by + az * bz
    norm_a = math.sqrt(ax * ax + ay * ay + az * az)
    norm_b = math.sqrt(bx * bx + by * by + bz * bz)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

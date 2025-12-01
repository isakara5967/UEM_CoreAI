# core/ontology/types.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Protocol, Dict, Any
import math


# ---- Primitive Types ------------------------------------------------------

StateVector = Tuple[float, ...]   # 16D: (resource, threat, wellbeing, health, energy, valence, arousal, dominance, reserved...)
StateDelta = Tuple[float, ...]  # 16D delta


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
    """Compute 16D state vector from modules.
    
    Structure:
        [0] resource   - (health + energy) / 2
        [1] threat     - danger_level  
        [2] wellbeing  - (valence + 1) / 2
        [3] health     - player_health (raw)
        [4] energy     - player_energy (raw)
        [5] valence    - emotion.valence (raw)
        [6] arousal    - emotion.arousal (raw)
        [7] dominance  - emotion.dominance (raw)
        [8-15] reserved
    """
    # Raw values
    health = getattr(world, 'player_health', 0.5)
    energy = getattr(world, 'player_energy', 0.5)
    danger = getattr(world, 'danger_level', 0.0)
    valence = getattr(emotion, 'valence', 0.0)
    arousal = getattr(emotion, 'arousal', 0.0)
    dominance = getattr(emotion, 'dominance', 0.0)
    
    # Derived values
    resource = max(0.0, min(1.0, (health + energy) / 2.0))
    threat = max(0.0, min(1.0, danger))
    wellbeing = max(0.0, min(1.0, (valence + 1.0) / 2.0))
    
    return (
        resource, threat, wellbeing,           # [0-2] derived
        health, energy, valence,               # [3-5] raw
        arousal, dominance,                    # [6-7] raw
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0  # [8-15] reserved
    )


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

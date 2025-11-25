# core/ontology/grounding.py
from __future__ import annotations

from typing import Dict, Any

from core.integrated_uem_core import WorldState
from core.emotion import EmotionCore
from .types import (
    StateVector,
    StateDelta,
    SelfEntity,
    Event,
    Goal,
    build_state_vector,
    compute_state_delta,
)


def build_self_entity(
    world: WorldState,
    emotion: EmotionCore,
    history: list[Event],
    goals: list[Goal],
) -> SelfEntity:
    """Create a SelfEntity snapshot from current modules."""
    state_vec: StateVector = build_state_vector(world, emotion)
    return SelfEntity(state_vector=state_vec, history=list(history), goals=list(goals))


def world_to_state_vector(world: WorldState, emotion: EmotionCore) -> StateVector:
    return build_state_vector(world, emotion)


def event_from_world_change(
    world_before: WorldState,
    world_after: WorldState,
    timestamp: float,
    source: str = "ENVIRONMENT",
    target: str = "SELF",
) -> Event:
    """Construct an EVENT from two consecutive WorldState snapshots."""
    # For now we ignore WELLBEING here and let EmotionCore handle it.
    from .types import StateVector

    # resource/threat from world, wellbeing handled separately
    # caller is expected to reconstruct wellbeing via EmotionCore
    dummy_emotion_before = type("E", (), {"valence": 0.0})()
    dummy_emotion_after = type("E", (), {"valence": 0.0})()

    state_before: StateVector = build_state_vector(world_before, dummy_emotion_before)
    state_after: StateVector = build_state_vector(world_after, dummy_emotion_after)
    delta: StateDelta = compute_state_delta(state_before, state_after)

    return Event(source=source, target=target, effect=delta, timestamp=timestamp)

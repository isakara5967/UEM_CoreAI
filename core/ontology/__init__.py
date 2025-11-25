# core/ontology/__init__.py
"""
UEM Ontology Layer 1 - Core 12 Concepts

This module provides the foundational ontology for UEM's internal language.

ENTITY (3):
    - SELF: The UEM agent itself
    - OTHER: Non-self agents modeled by UEM
    - EVENT: Discrete occurrence that may change states

STATE (3):
    - RESOURCE_LEVEL: Normalized (health + energy) / 2
    - THREAT_LEVEL: Perceived danger level
    - WELLBEING: Affective quality from EmotionCore.valence

VALUE (3):
    - BENEFIT: Positive change in WELLBEING
    - COST: Negative change in RESOURCE_LEVEL
    - VIOLATION: Degree of ETHMOR constraint breach

RELATION (3):
    - CAUSES: Event → StateDelta
    - AFFECTS: Entity × Event → wellbeing_delta
    - SIMILAR: StateVector × StateVector → similarity

Usage:
    from core.ontology import (
        StateVector,
        SelfEntity,
        OtherEntity,
        Event,
        Goal,
        build_state_vector,
        similar,
    )
"""

from .types import (
    # Primitive types
    StateVector,
    StateDelta,
    # Entity dataclasses
    Event,
    Goal,
    SelfEntity,
    OtherEntity,
    # Protocols for module interfaces
    WorldStateLike,
    EmotionCoreLike,
    EthmorLike,
    # State construction
    build_state_vector,
    compute_state_delta,
    # Value functions
    compute_benefit,
    compute_cost,
    compute_violation,
    # Relation functions
    causes,
    affects,
    similar,
)

from .grounding import (
    build_self_entity,
    world_to_state_vector,
    event_from_world_change,
)

__all__ = [
    # Types
    "StateVector",
    "StateDelta",
    "Event",
    "Goal",
    "SelfEntity",
    "OtherEntity",
    # Protocols
    "WorldStateLike",
    "EmotionCoreLike",
    "EthmorLike",
    # State functions
    "build_state_vector",
    "compute_state_delta",
    # Value functions
    "compute_benefit",
    "compute_cost",
    "compute_violation",
    # Relation functions
    "causes",
    "affects",
    "similar",
    # Grounding functions
    "build_self_entity",
    "world_to_state_vector",
    "event_from_world_change",
]

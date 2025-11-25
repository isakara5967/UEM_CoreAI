# core/ethmor/__init__.py
"""
ETHMOR - Ethics & Morality Reasoning System

Provides ethical constraint evaluation for UEM actions and events.

Usage:
    from core.ethmor import EthmorSystem, EthmorContext, ActionDecision
    
    ethmor = EthmorSystem("config/ethmor/constraints_v0.yaml")
    
    context = EthmorContext.from_self_context(self_core.get_ethmor_context())
    result = ethmor.evaluate(context)
    
    if result.decision == ActionDecision.ALLOW:
        # Execute action
        pass
"""

from .ethmor_system import (
    # Enums
    ConstraintType,
    ConstraintScope,
    ActionDecision,
    # Data types
    Constraint,
    ConstraintViolation,
    EthmorEvaluationResult,
    EthmorContext,
    # Components
    ConstraintStore,
    ConstraintEvaluator,
    ActionFilter,
    # Main system
    EthmorSystem,
)

__all__ = [
    # Enums
    "ConstraintType",
    "ConstraintScope",
    "ActionDecision",
    # Data types
    "Constraint",
    "ConstraintViolation",
    "EthmorEvaluationResult",
    "EthmorContext",
    # Components
    "ConstraintStore",
    "ConstraintEvaluator",
    "ActionFilter",
    # Main system
    "EthmorSystem",
]

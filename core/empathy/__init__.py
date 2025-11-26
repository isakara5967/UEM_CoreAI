# core/empathy/__init__.py
"""Empathy system for UEM."""

from .empathy_orchestrator import (
    EmpathyOrchestrator,
    EmpathyResult,
    OtherEntity,
    create_empathy_orchestrator,
    EmpathyIntegrationMixin,
)

__all__ = [
    'EmpathyOrchestrator',
    'EmpathyResult',
    'OtherEntity',
    'create_empathy_orchestrator',
    'EmpathyIntegrationMixin',
]

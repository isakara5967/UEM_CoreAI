# core/planning/__init__.py
"""
Planning Module for UEM

Exports:
    - Planner, PlanningContext, ActionPlan (v1 - Brief compliant)
    - PlanningCore (legacy, still works)
"""

# New v1 API (Brief compliant)
from .types import PlanningContext, ActionPlan, CandidateAction, get_predicted_effect
from .planner import Planner, create_planner

# Legacy API (backward compatible)
from .planning_core import PlanningCore

__all__ = [
    # New API
    'Planner',
    'PlanningContext', 
    'ActionPlan',
    'CandidateAction',
    'create_planner',
    'get_predicted_effect',
    # Legacy
    'PlanningCore',
]

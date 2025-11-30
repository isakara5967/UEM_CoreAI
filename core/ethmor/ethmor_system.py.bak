# core/ethmor/ethmor_system.py
"""
ETHMOR - Ethics & Morality Reasoning System

ETHMOR evaluates actions and events against ethical constraints,
producing violation scores and action decisions (ALLOW/FLAG/BLOCK).

Components:
- ConstraintStore: Loads and stores constraints from YAML
- ConstraintEvaluator: Evaluates conditions against context
- ActionFilter: Makes final ALLOW/FLAG/BLOCK decisions

Author: UEM Project
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ============================================================================
# ENUMS AND DATA TYPES
# ============================================================================

class ConstraintType(Enum):
    """Constraint type: HARD or SOFT."""
    HARD = "HARD"
    SOFT = "SOFT"


class ConstraintScope(Enum):
    """Constraint scope."""
    SELF = "SELF"
    OTHER = "OTHER"
    WORLD = "WORLD"


class ActionDecision(Enum):
    """Action decision result."""
    ALLOW = "ALLOW"
    FLAG = "FLAG"
    BLOCK = "BLOCK"


@dataclass
class Constraint:
    """Single ethical constraint."""
    id: str
    type: ConstraintType
    scope: ConstraintScope
    condition: str
    severity: float
    description: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Constraint":
        """Create Constraint from dictionary."""
        return cls(
            id=data["id"],
            type=ConstraintType(data["type"]),
            scope=ConstraintScope(data["scope"]),
            condition=data["condition"],
            severity=float(data["severity"]),
            description=data.get("description", ""),
        )


@dataclass
class ConstraintViolation:
    """Result of evaluating a single constraint."""
    constraint_id: str
    constraint_type: ConstraintType
    triggered: bool
    local_violation: float  # 0.0 - 1.0
    details: str = ""


@dataclass
class EthmorEvaluationResult:
    """Complete evaluation result."""
    violation_score: float  # 0.0 - 1.0
    triggered_constraints: List[ConstraintViolation]
    decision: ActionDecision
    explanation: str
    hard_violation: bool = False


@dataclass
class EthmorContext:
    """Context for ETHMOR evaluation.
    
    Contains all data needed to evaluate constraints.
    Built from SelfCore.get_ethmor_context() + action info.
    """
    # State values (from SELF)
    RESOURCE_LEVEL: float = 0.5
    THREAT_LEVEL: float = 0.0
    WELLBEING: float = 0.5
    
    # Before values
    RESOURCE_LEVEL_before: float = 0.5
    THREAT_LEVEL_before: float = 0.0
    WELLBEING_before: float = 0.5
    
    # After values (predicted)
    RESOURCE_LEVEL_after: float = 0.5
    THREAT_LEVEL_after: float = 0.0
    WELLBEING_after: float = 0.5
    
    # Delta values
    RESOURCE_LEVEL_delta: float = 0.0
    THREAT_LEVEL_delta: float = 0.0
    WELLBEING_delta: float = 0.0
    
    # Other agent values (if applicable)
    WELLBEING_other: float = 0.5
    WELLBEING_other_delta: float = 0.0
    
    # Computed values
    benefit: float = 0.0  # positive_delta(WELLBEING)
    cost: float = 0.0     # negative_delta(RESOURCE_LEVEL)
    
    # Action info
    action_name: str = ""
    action_type: str = ""
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_self_context(
        cls,
        self_context: Dict[str, Any],
        predicted_state: Optional[Tuple[float, float, float]] = None,
        action_name: str = "",
        action_type: str = "",
        other_wellbeing: float = 0.5,
        other_wellbeing_delta: float = 0.0,
    ) -> "EthmorContext":
        """Build EthmorContext from SelfCore context + predictions."""
        
        ctx = cls()
        
        # Current values
        ctx.RESOURCE_LEVEL = self_context.get('RESOURCE_LEVEL', 0.5)
        ctx.THREAT_LEVEL = self_context.get('THREAT_LEVEL', 0.0)
        ctx.WELLBEING = self_context.get('WELLBEING', 0.5)
        
        # Before values
        ctx.RESOURCE_LEVEL_before = self_context.get('RESOURCE_LEVEL_before', ctx.RESOURCE_LEVEL)
        ctx.THREAT_LEVEL_before = self_context.get('THREAT_LEVEL_before', ctx.THREAT_LEVEL)
        ctx.WELLBEING_before = self_context.get('WELLBEING_before', ctx.WELLBEING)
        
        # After values (from prediction or current)
        if predicted_state:
            ctx.RESOURCE_LEVEL_after = predicted_state[0]
            ctx.THREAT_LEVEL_after = predicted_state[1]
            ctx.WELLBEING_after = predicted_state[2]
        else:
            ctx.RESOURCE_LEVEL_after = ctx.RESOURCE_LEVEL
            ctx.THREAT_LEVEL_after = ctx.THREAT_LEVEL
            ctx.WELLBEING_after = ctx.WELLBEING
        
        # Deltas (based on after - before)
        ctx.RESOURCE_LEVEL_delta = ctx.RESOURCE_LEVEL_after - ctx.RESOURCE_LEVEL_before
        ctx.THREAT_LEVEL_delta = ctx.THREAT_LEVEL_after - ctx.THREAT_LEVEL_before
        ctx.WELLBEING_delta = ctx.WELLBEING_after - ctx.WELLBEING_before
        
        # Other agent
        ctx.WELLBEING_other = other_wellbeing
        ctx.WELLBEING_other_delta = other_wellbeing_delta
        
        # Computed values
        ctx.benefit = max(0.0, ctx.WELLBEING_delta)
        ctx.cost = max(0.0, -ctx.RESOURCE_LEVEL_delta)
        
        # Action info
        ctx.action_name = action_name
        ctx.action_type = action_type
        
        return ctx
    
    def to_eval_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for condition evaluation."""
        return {
            'RESOURCE_LEVEL': self.RESOURCE_LEVEL,
            'THREAT_LEVEL': self.THREAT_LEVEL,
            'WELLBEING': self.WELLBEING,
            'RESOURCE_LEVEL_before': self.RESOURCE_LEVEL_before,
            'THREAT_LEVEL_before': self.THREAT_LEVEL_before,
            'WELLBEING_before': self.WELLBEING_before,
            'RESOURCE_LEVEL_after': self.RESOURCE_LEVEL_after,
            'THREAT_LEVEL_after': self.THREAT_LEVEL_after,
            'WELLBEING_after': self.WELLBEING_after,
            'RESOURCE_LEVEL_delta': self.RESOURCE_LEVEL_delta,
            'THREAT_LEVEL_delta': self.THREAT_LEVEL_delta,
            'WELLBEING_delta': self.WELLBEING_delta,
            'WELLBEING_other': self.WELLBEING_other,
            'WELLBEING_other_delta': self.WELLBEING_other_delta,
            'benefit': self.benefit,
            'cost': self.cost,
            'action_name': self.action_name,
            'action_type': self.action_type,
        }


# ============================================================================
# CONSTRAINT STORE
# ============================================================================

class ConstraintStore:
    """Loads and stores ethical constraints."""
    
    def __init__(self):
        self.constraints: List[Constraint] = []
        self.thresholds = {
            'allow_max': 0.3,
            'flag_max': 0.7,
        }
    
    def load_from_yaml(self, path: str) -> None:
        """Load constraints from YAML file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        ethmor_data = data.get('ethmor', data)
        
        # Load thresholds
        if 'thresholds' in ethmor_data:
            self.thresholds.update(ethmor_data['thresholds'])
        
        # Load constraints
        self.constraints = []
        for c_data in ethmor_data.get('constraints', []):
            constraint = Constraint.from_dict(c_data)
            self.constraints.append(constraint)
    
    def load_from_dict(self, data: Dict[str, Any]) -> None:
        """Load constraints from dictionary."""
        ethmor_data = data.get('ethmor', data)
        
        if 'thresholds' in ethmor_data:
            self.thresholds.update(ethmor_data['thresholds'])
        
        self.constraints = []
        for c_data in ethmor_data.get('constraints', []):
            constraint = Constraint.from_dict(c_data)
            self.constraints.append(constraint)
    
    def get_hard_constraints(self) -> List[Constraint]:
        """Get all HARD constraints."""
        return [c for c in self.constraints if c.type == ConstraintType.HARD]
    
    def get_soft_constraints(self) -> List[Constraint]:
        """Get all SOFT constraints."""
        return [c for c in self.constraints if c.type == ConstraintType.SOFT]


# ============================================================================
# CONSTRAINT EVALUATOR
# ============================================================================

class ConstraintEvaluator:
    """Evaluates constraints against context."""
    
    def __init__(self, store: ConstraintStore):
        self.store = store
    
    def evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition string against context.
        
        Uses safe evaluation with only allowed operations.
        """
        try:
            # Replace 'and' and 'or' for Python evaluation
            expr = condition
            
            # Create safe evaluation context
            safe_context = dict(context)
            
            # Evaluate
            result = eval(expr, {"__builtins__": {}}, safe_context)
            return bool(result)
            
        except Exception as e:
            # If evaluation fails, assume not triggered
            return False
    
    def evaluate_constraint(
        self,
        constraint: Constraint,
        context: EthmorContext,
    ) -> ConstraintViolation:
        """Evaluate a single constraint."""
        
        eval_dict = context.to_eval_dict()
        triggered = self.evaluate_condition(constraint.condition, eval_dict)
        
        if triggered:
            local_violation = constraint.severity
        else:
            local_violation = 0.0
        
        return ConstraintViolation(
            constraint_id=constraint.id,
            constraint_type=constraint.type,
            triggered=triggered,
            local_violation=local_violation,
            details=constraint.description if triggered else "",
        )
    
    def evaluate_all(self, context: EthmorContext) -> List[ConstraintViolation]:
        """Evaluate all constraints."""
        violations = []
        for constraint in self.store.constraints:
            violation = self.evaluate_constraint(constraint, context)
            violations.append(violation)
        return violations


# ============================================================================
# ACTION FILTER
# ============================================================================

class ActionFilter:
    """Makes ALLOW/FLAG/BLOCK decisions based on violations."""
    
    def __init__(self, store: ConstraintStore):
        self.store = store
    
    def compute_violation_score(
        self,
        violations: List[ConstraintViolation],
    ) -> Tuple[float, bool]:
        """Compute total violation score.
        
        Returns:
            Tuple of (violation_score, has_hard_violation)
        """
        hard_violation = 0.0
        soft_violations = []
        has_hard = False
        
        for v in violations:
            if v.triggered:
                if v.constraint_type == ConstraintType.HARD:
                    hard_violation = max(hard_violation, v.local_violation)
                    has_hard = True
                else:
                    soft_violations.append(v.local_violation)
        
        # Aggregate soft violations (weighted average by severity)
        if soft_violations:
            aggregated_soft = sum(soft_violations) / len(soft_violations)
        else:
            aggregated_soft = 0.0
        
        # Final score: max of hard and soft
        final_score = max(hard_violation, aggregated_soft)
        
        return final_score, has_hard
    
    def decide(
        self,
        violation_score: float,
        has_hard_violation: bool,
    ) -> ActionDecision:
        """Make decision based on violation score."""
        
        # Hard violations always block
        if has_hard_violation and violation_score >= 0.9:
            return ActionDecision.BLOCK
        
        allow_max = self.store.thresholds.get('allow_max', 0.3)
        flag_max = self.store.thresholds.get('flag_max', 0.7)
        
        if violation_score < allow_max:
            return ActionDecision.ALLOW
        elif violation_score < flag_max:
            return ActionDecision.FLAG
        else:
            return ActionDecision.BLOCK


# ============================================================================
# MAIN ETHMOR SYSTEM
# ============================================================================

class EthmorSystem:
    """Main ETHMOR system integrating all components.
    
    Usage:
        ethmor = EthmorSystem()
        ethmor.load_constraints("config/ethmor/constraints_v0.yaml")
        
        context = EthmorContext.from_self_context(self_core.get_ethmor_context())
        result = ethmor.evaluate(context)
        
        if result.decision == ActionDecision.BLOCK:
            # Don't execute action
            pass
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.store = ConstraintStore()
        self.evaluator = ConstraintEvaluator(self.store)
        self.filter = ActionFilter(self.store)
        
        self._last_result: Optional[EthmorEvaluationResult] = None
        
        if config_path:
            self.load_constraints(config_path)
    
    def load_constraints(self, path: str) -> None:
        """Load constraints from YAML file."""
        self.store.load_from_yaml(path)
    
    def load_constraints_from_dict(self, data: Dict[str, Any]) -> None:
        """Load constraints from dictionary."""
        self.store.load_from_dict(data)
    
    def evaluate(self, context: EthmorContext) -> EthmorEvaluationResult:
        """Evaluate context against all constraints.
        
        Args:
            context: EthmorContext with all relevant state info
            
        Returns:
            EthmorEvaluationResult with score, violations, and decision
        """
        # Evaluate all constraints
        violations = self.evaluator.evaluate_all(context)
        
        # Compute score
        score, has_hard = self.filter.compute_violation_score(violations)
        
        # Make decision
        decision = self.filter.decide(score, has_hard)
        
        # Build explanation
        triggered = [v for v in violations if v.triggered]
        if triggered:
            explanations = [f"[{v.constraint_id}] {v.details}" for v in triggered]
            explanation = "; ".join(explanations)
        else:
            explanation = "No constraints violated."
        
        result = EthmorEvaluationResult(
            violation_score=score,
            triggered_constraints=triggered,
            decision=decision,
            explanation=explanation,
            hard_violation=has_hard,
        )
        
        self._last_result = result
        return result
    
    def check_constraint_breach(
        self,
        event: Any,
        context: Dict[str, Any],
    ) -> float:
        """EthmorLike protocol implementation.
        
        This is called by ontology's compute_violation().
        
        Args:
            event: Ontology Event object
            context: Additional context dict
            
        Returns:
            Violation score 0.0-1.0
        """
        # Build EthmorContext from event and context
        ethmor_ctx = EthmorContext()
        
        # Extract state from context if available
        if 'RESOURCE_LEVEL' in context:
            ethmor_ctx.RESOURCE_LEVEL = context['RESOURCE_LEVEL']
        if 'THREAT_LEVEL' in context:
            ethmor_ctx.THREAT_LEVEL = context['THREAT_LEVEL']
        if 'WELLBEING' in context:
            ethmor_ctx.WELLBEING = context['WELLBEING']
        
        # Use event effect as delta
        if hasattr(event, 'effect'):
            ethmor_ctx.RESOURCE_LEVEL_delta = event.effect[0]
            ethmor_ctx.THREAT_LEVEL_delta = event.effect[1]
            ethmor_ctx.WELLBEING_delta = event.effect[2]
            
            # Compute after values
            ethmor_ctx.RESOURCE_LEVEL_after = ethmor_ctx.RESOURCE_LEVEL + event.effect[0]
            ethmor_ctx.THREAT_LEVEL_after = ethmor_ctx.THREAT_LEVEL + event.effect[1]
            ethmor_ctx.WELLBEING_after = ethmor_ctx.WELLBEING + event.effect[2]
        
        # Compute benefit/cost
        ethmor_ctx.benefit = max(0.0, ethmor_ctx.WELLBEING_delta)
        ethmor_ctx.cost = max(0.0, -ethmor_ctx.RESOURCE_LEVEL_delta)
        
        # Evaluate
        result = self.evaluate(ethmor_ctx)
        return result.violation_score
    
    def filter_action(
        self,
        context: EthmorContext,
    ) -> ActionDecision:
        """Convenience method to get just the decision."""
        result = self.evaluate(context)
        return result.decision
    
    def explain_last_decision(self) -> str:
        """Get explanation for the last evaluation."""
        if self._last_result:
            return self._last_result.explanation
        return "No evaluation performed yet."
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ETHMOR statistics."""
        return {
            "total_constraints": len(self.store.constraints),
            "hard_constraints": len(self.store.get_hard_constraints()),
            "soft_constraints": len(self.store.get_soft_constraints()),
            "thresholds": self.store.thresholds.copy(),
        }

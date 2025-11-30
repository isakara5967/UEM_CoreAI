# core/planning/predata_calculator.py
"""
Planner PreData Calculator - Computes derived metrics for PreData logging.

Calculates:
- utility_breakdown: Contribution of each factor to final utility
- candidate_plans: List of considered action candidates
- somatic_bias: Bias from somatic marker system

Author: UEM Project
Date: 30 November 2025
Version: 1.0
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple


@dataclass
class CandidatePlan:
    """Represents a candidate action plan."""
    action: str
    utility: float
    reasoning: str = ""
    predicted_effect: Optional[Tuple[float, float, float]] = None
    somatic_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action,
            'utility': self.utility,
            'reasoning': self.reasoning,
            'predicted_effect': self.predicted_effect,
            'somatic_score': self.somatic_score,
        }


@dataclass
class UtilityBreakdown:
    """Breakdown of utility calculation components."""
    base_utility: float = 0.0
    goal_contribution: float = 0.0
    emotion_contribution: float = 0.0
    memory_contribution: float = 0.0
    somatic_contribution: float = 0.0
    risk_penalty: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'base_utility': round(self.base_utility, 4),
            'goal_contribution': round(self.goal_contribution, 4),
            'emotion_contribution': round(self.emotion_contribution, 4),
            'memory_contribution': round(self.memory_contribution, 4),
            'somatic_contribution': round(self.somatic_contribution, 4),
            'risk_penalty': round(self.risk_penalty, 4),
            'total': round(self.total(), 4),
        }
    
    def total(self) -> float:
        return (
            self.base_utility +
            self.goal_contribution +
            self.emotion_contribution +
            self.memory_contribution +
            self.somatic_contribution -
            self.risk_penalty
        )


class PlannerPreDataCalculator:
    """
    Calculates derived planner metrics for PreData logging.
    
    Usage:
        calc = PlannerPreDataCalculator()
        calc.add_candidate("flee", 0.8, "High danger")
        calc.set_utility_breakdown(base=0.5, goal=0.2)
        calc.set_somatic_bias(-0.1)
        predata = calc.get_predata()
        calc.reset()
    """
    
    def __init__(self):
        self._candidates: List[CandidatePlan] = []
        self._utility_breakdown: Optional[UtilityBreakdown] = None
        self._somatic_bias: Optional[float] = None
        self._selected_action: Optional[str] = None
    
    def add_candidate(
        self,
        action: str,
        utility: float,
        reasoning: str = "",
        predicted_effect: Optional[Tuple[float, float, float]] = None,
        somatic_score: Optional[float] = None,
    ) -> None:
        """Add a candidate action plan."""
        self._candidates.append(CandidatePlan(
            action=action,
            utility=utility,
            reasoning=reasoning,
            predicted_effect=predicted_effect,
            somatic_score=somatic_score,
        ))
    
    def set_utility_breakdown(
        self,
        base: float = 0.0,
        goal: float = 0.0,
        emotion: float = 0.0,
        memory: float = 0.0,
        somatic: float = 0.0,
        risk_penalty: float = 0.0,
    ) -> None:
        """Set the utility breakdown for the selected action."""
        self._utility_breakdown = UtilityBreakdown(
            base_utility=base,
            goal_contribution=goal,
            emotion_contribution=emotion,
            memory_contribution=memory,
            somatic_contribution=somatic,
            risk_penalty=risk_penalty,
        )
    
    def set_somatic_bias(self, bias: float) -> None:
        """Set somatic bias (-1.0 to 1.0)."""
        self._somatic_bias = max(-1.0, min(1.0, bias))
    
    def set_selected_action(self, action: str) -> None:
        """Record which action was selected."""
        self._selected_action = action
    
    def get_predata(self) -> Dict[str, Any]:
        """Get computed PreData fields."""
        sorted_candidates = sorted(
            self._candidates,
            key=lambda c: c.utility,
            reverse=True
        )
        
        return {
            'utility_breakdown': (
                self._utility_breakdown.to_dict()
                if self._utility_breakdown else None
            ),
            'candidate_plans': [c.to_dict() for c in sorted_candidates],
            'somatic_bias': round(self._somatic_bias, 4) if self._somatic_bias else None,
            'selected_action': self._selected_action,
            'candidate_count': len(self._candidates),
        }
    
    def reset(self) -> None:
        """Reset for new planning cycle."""
        self._candidates.clear()
        self._utility_breakdown = None
        self._somatic_bias = None
        self._selected_action = None
    
    @staticmethod
    def compute_somatic_bias_from_markers(
        action: str,
        somatic_scores: Dict[str, float],
    ) -> float:
        """Compute somatic bias from marker scores."""
        if action not in somatic_scores:
            return 0.0
        
        action_score = somatic_scores[action]
        if len(somatic_scores) > 1:
            avg_score = sum(somatic_scores.values()) / len(somatic_scores)
            bias = action_score - avg_score
        else:
            bias = action_score
        
        return round(bias, 4)


# Singleton
_default_calculator: Optional[PlannerPreDataCalculator] = None


def get_planner_predata_calculator() -> PlannerPreDataCalculator:
    global _default_calculator
    if _default_calculator is None:
        _default_calculator = PlannerPreDataCalculator()
    return _default_calculator


__all__ = [
    'PlannerPreDataCalculator',
    'CandidatePlan',
    'UtilityBreakdown',
    'get_planner_predata_calculator',
]

# core/planning/types.py
"""
Planning Module Types - v2

Includes PlanningContext, ActionPlan, CandidateAction for PlannerV2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

# Type aliases
StateVector = Tuple[float, float, float]   # (resource, threat, wellbeing)
StateDelta = Tuple[float, float, float]


# ============================================================================
# CANDIDATE ACTION
# ============================================================================

@dataclass
class CandidateAction:
    """Intermediate representation during planning pipeline."""
    action: str                           # "flee", "help", etc.
    target: Optional[str] = None          # entity or location ID
    predicted_effect: StateDelta = (0.0, 0.0, 0.0)
    utility: float = 0.0
    reasoning: List[str] = field(default_factory=list)
    base_params: Dict[str, Any] = field(default_factory=dict)
    
    # Modifiers (computed during pipeline)
    somatic_modifier: float = 0.0
    empathy_modifier: float = 0.0
    goal_alignment: float = 0.0
    state_improvement: float = 0.0


# ============================================================================
# ACTION PLAN (OUTPUT)
# ============================================================================

@dataclass
class ActionPlan:
    """Final output of the planning pipeline."""
    action: str
    target: Optional[str] = None
    predicted_effect: StateDelta = (0.0, 0.0, 0.0)
    confidence: float = 0.5
    utility: float = 0.0
    reasoning: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'action': self.action,
            'target': self.target,
            'predicted_effect': self.predicted_effect,
            'confidence': self.confidence,
            'utility': self.utility,
            'reasoning': self.reasoning,
        }


# ============================================================================
# PLANNING CONTEXT (INPUT)
# ============================================================================

@dataclass
class PlanningContext:
    """Input context for the planning pipeline."""
    
    # State
    state_vector: StateVector = (0.5, 0.5, 0.5)
    
    # Goals
    goals: List[Any] = field(default_factory=list)
    
    # World info
    world_snapshot: Any = None
    
    # Available actions
    available_actions: List[str] = field(default_factory=lambda: [
        "flee", "approach", "help", "attack", "explore", "wait"
    ])
    
    # Somatic markers
    somatic_markers: Any = None
    
    # Empathy result
    empathy_result: Any = None
    
    # Emotion state
    emotion_state: Dict[str, float] = field(default_factory=dict)
    
    # Appraisal result
    appraisal_result: Any = None
    
    def get_valence(self) -> float:
        """Get emotional valence."""
        if self.emotion_state:
            return self.emotion_state.get('valence', 0.0)
        if self.appraisal_result:
            if hasattr(self.appraisal_result, 'valence'):
                return self.appraisal_result.valence
            if isinstance(self.appraisal_result, dict):
                return self.appraisal_result.get('valence', 0.0)
        return 0.0
    
    def get_arousal(self) -> float:
        """Get emotional arousal."""
        if self.emotion_state:
            return self.emotion_state.get('arousal', 0.5)
        if self.appraisal_result:
            if hasattr(self.appraisal_result, 'arousal'):
                return self.appraisal_result.arousal
            if isinstance(self.appraisal_result, dict):
                return self.appraisal_result.get('arousal', 0.5)
        return 0.5


# ============================================================================
# ACTION EFFECTS (Predicted outcomes)
# ============================================================================

DEFAULT_ACTION_EFFECTS: Dict[str, StateDelta] = {
    'flee':     (0.0, -0.3, +0.1),    # Threat decreases, slight wellbeing boost
    'approach': (+0.1, +0.1, 0.0),    # Resource potential, slight threat increase
    'help':     (-0.1, 0.0, +0.2),    # Cost resource, boost wellbeing
    'attack':   (0.0, -0.2, -0.1),    # Reduce threat, wellbeing cost
    'explore':  (+0.1, +0.05, 0.0),   # Resource potential, minor threat
    'wait':     (0.0, 0.0, 0.0),      # No change (observe)
}


def get_predicted_effect(action: str) -> StateDelta:
    """Get default predicted effect for an action."""
    return DEFAULT_ACTION_EFFECTS.get(action, (0.0, 0.0, 0.0))

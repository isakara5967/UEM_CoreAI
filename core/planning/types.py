# core/planning/types.py
"""
Planning Module Types - v1

Author: UEM Project
Date: 26 November 2025
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

# Type aliases
StateVector = Tuple[float, ...]   # 16D state vector
StateDelta = Tuple[float, float, float]


# ============================================================================
# CANDIDATE ACTION
# ============================================================================

@dataclass
class CandidateAction:
    """Intermediate representation during planning pipeline."""
    action: str                           # "flee", "help", etc.
    target: Optional[str] = None          # entity or location ID
    predicted_effect: StateDelta = (0.0,) * 16
    utility: float = 0.0
    reasoning: List[str] = field(default_factory=list)
    
    # === PreData Fields (v1.9) ===
    utility_breakdown: Optional[Dict[str, float]] = None
    candidate_plans: Optional[List[Dict[str, Any]]] = None
    somatic_bias: Optional[float] = None
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
    """
    Final output of the planning pipeline.
    
    Attributes:
        action: Action name ("flee", "help", "attack", etc.)
        target: Target entity or location ID
        predicted_effect: Expected (Δresource, Δthreat, Δwellbeing)
        confidence: How confident the planner is (0-1)
        utility: Final decision score (for debug + RL)
        reasoning: Explanation steps
    """
    action: str
    target: Optional[str] = None
    predicted_effect: StateDelta = (0.0,) * 16
    confidence: float = 0.5
    utility: float = 0.0
    reasoning: List[str] = field(default_factory=list)
    
    # === PreData Fields (v1.9) ===
    utility_breakdown: Optional[Dict[str, float]] = None
    candidate_plans: Optional[List[Dict[str, Any]]] = None
    somatic_bias: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'action': self.action,
            'target': self.target,
            'predicted_effect': self.predicted_effect,
            'confidence': self.confidence,
            'utility': self.utility,
            'reasoning': self.reasoning,
            'utility_breakdown': self.utility_breakdown,
            'candidate_plans': self.candidate_plans,
            'somatic_bias': self.somatic_bias,
        }


# ============================================================================
# PLANNING CONTEXT (INPUT)
# ============================================================================

@dataclass
class PlanningContext:
    """
    Input context for the planning pipeline.
    
    Groups:
        - Internal state (Self)
        - Affective evaluations
        - External world
        - Available actions
        - Optional social feedback
    """
    # Internal state (Self)
    state_vector: StateVector = (0.5,) * 16
    goals: List[Any] = field(default_factory=list)
    
    # Affective evaluations
    appraisal_result: Optional[Any] = None      # AppraisalResult or dict
    somatic_markers: Optional[Any] = None       # SomaticMarkerSystem
    
    # External world
    world_snapshot: Optional[Any] = None        # WorldSnapshot
    
    # Physically possible primitive actions
    available_actions: List[str] = field(default_factory=lambda: [
        "flee", "approach", "help", "attack", "explore", "wait"
    ])
    
    # Optional social feedback
    empathy_result: Optional[Any] = None        # EmpathyResult
    
    # Emotion state (convenience)
    emotion_state: Optional[Dict[str, float]] = None
    
    def get_danger_level(self) -> float:
        """Extract danger level from world snapshot or state vector."""
        if self.world_snapshot:
            if hasattr(self.world_snapshot, 'danger_level'):
                return self.world_snapshot.danger_level
            if isinstance(self.world_snapshot, dict):
                return self.world_snapshot.get('danger_level', 0.0)
        # Fallback to state_vector threat component
        return self.state_vector[1]
    
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

# Default predicted effects for each action type
DEFAULT_ACTION_EFFECTS: Dict[str, StateDelta] = {
    'flee':     (0.0, -0.3, +0.1),    # Threat decreases, slight wellbeing boost
    'approach': (+0.1, +0.1, 0.0),    # Resource potential, slight threat increase
    'help':     (-0.1, 0.0, +0.2),    # Cost resource, boost wellbeing
    'attack':   (0.0, -0.2, -0.1),    # Reduce threat, wellbeing cost
    'explore':  (+0.1, +0.05, 0.0),   # Resource potential, minor threat
    'wait':     (0.0, 0.0, 0.0),      # No change (observe)
}


def get_predicted_effect(action: str) -> StateDelta:
    """Get default predicted effect for an action. Returns 16D."""
    effect_3d = DEFAULT_ACTION_EFFECTS.get(action, (0.0, 0.0, 0.0))
    # Pad to 16D: first 3 are derived (resource, threat, wellbeing)
    return effect_3d + (0.0,) * 13

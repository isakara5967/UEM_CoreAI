# core/unified_types.py
"""
Unified Types for Core Integration v1

Author: UEM Project
Date: 26 November 2025
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Import from existing ontology
try:
    from core.ontology.types import StateVector, StateDelta, Goal
except ImportError:
    # Fallback definitions
    StateVector = Tuple[float, float, float]
    StateDelta = Tuple[float, float, float]
    Goal = Any


# ============================================================================
# PHASE 2 - MEMORY
# ============================================================================

@dataclass
class MemoryContext:
    """Memory retrieval results."""
    similar_experiences: List[Dict[str, Any]] = field(default_factory=list)
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # === PreData Fields (v1.9) ===
    retrieval_count: Optional[int] = None
    memory_relevance: Optional[float] = None
    working_memory_load: Optional[float] = None
    ltm_write_count: Optional[int] = None


# ============================================================================
# PHASE 3 - SELF
# ============================================================================

@dataclass
class SelfState:
    """Self module state snapshot."""
    state_vector: StateVector
    state_delta: StateDelta
    goals: List[Goal] = field(default_factory=list)
    
    # === PreData Fields (v1.9) ===
    confidence_score: Optional[float] = None
    resource_usage: Optional[Dict[str, Any]] = None


# ============================================================================
# PHASE 4 - APPRAISAL
# ============================================================================

@dataclass
class AppraisalResult:
    """Emotional appraisal result."""
    valence: float = 0.0       # -1 to +1
    arousal: float = 0.5       # 0 to 1
    dominance: float = 0.0     # -1 to +1
    emotion_label: str = "neutral"
    
    # === PreData Fields (v1.9) ===
    valence_delta: Optional[float] = None
    arousal_volatility: Optional[float] = None
    engagement: Optional[float] = None
    mood_baseline: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'valence': self.valence,
            'arousal': self.arousal,
            'dominance': self.dominance,
            'emotion_label': self.emotion_label,
            'valence_delta': self.valence_delta,
            'arousal_volatility': self.arousal_volatility,
            'engagement': self.engagement,
            'mood_baseline': self.mood_baseline,
        }


# ============================================================================
# PHASE 8 - EXECUTION
# ============================================================================

@dataclass
class ActionResult:
    """Execution outcome."""
    action_name: str
    target: Optional[str] = None
    success: bool = True
    outcome_type: str = "neutral"
    outcome_valence: float = 0.0
    actual_effect: StateDelta = (0.0, 0.0, 0.0)
    reasoning: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_name': self.action_name,
            'target': self.target,
            'success': self.success,
            'outcome_type': self.outcome_type,
            'outcome_valence': self.outcome_valence,
            'actual_effect': self.actual_effect,
            'reasoning': self.reasoning,
        }


# ============================================================================
# METRICS (Optional)
# ============================================================================

@dataclass
class CycleMetrics:
    """Performance metrics for a cognitive cycle (Sprint 0C extended)."""
    tick: int = 0
    total_time_ms: float = 0.0
    phase_times: Dict[str, float] = field(default_factory=dict)
    
    # Sprint 0C: Extended metrics for MetaMind
    action_taken: Optional[str] = None
    action_success: bool = False
    emotion_valence: float = 0.0
    emotion_arousal: float = 0.5
    emotion_label: str = "neutral"
    
    # === PreData Fields (v1.9) ===
    valence_delta: Optional[float] = None
    arousal_volatility: Optional[float] = None
    engagement: Optional[float] = None
    mood_baseline: Optional[float] = None
    conscious_type: Optional[str] = None
    conscious_activation: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tick': self.tick,
            'total_time_ms': self.total_time_ms,
            'phase_times': self.phase_times,
            'action_taken': self.action_taken,
            'action_success': self.action_success,
            'emotion_valence': self.emotion_valence,
            'emotion_arousal': self.emotion_arousal,
            'emotion_label': self.emotion_label,
            'conscious_type': self.conscious_type,
            'conscious_activation': self.conscious_activation,
        }

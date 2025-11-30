# core/self/types.py
"""
Self module type definitions.

Provides SelfEvalResult class as specified in master document.
Alias/wrapper to SelfState for architectural consistency.

Author: UEM Project
Date: 30 November 2025
Version: 1.0 (Hybrid/Alias Strategy per Alice decision)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.unified_types import SelfState

# Import ontology types if available
try:
    from core.ontology.types import StateVector, StateDelta, Goal
except ImportError:
    StateVector = Tuple[float, float, float]
    StateDelta = Tuple[float, float, float]
    Goal = Any


@dataclass
class SelfEvalResult:
    """
    Self-evaluation results - Document-compliant interface.
    
    Master spec: UEM_PreData_Log_Master_Implementation_Document_Fix.md Section 6.2.7
    
    PreData Fields:
        - confidence_score: Agent's confidence in current state/decisions (0.0-1.0)
        - resource_usage: Dictionary of resource consumption metrics
    """
    # Core fields
    state_vector: StateVector = (0.5, 0.0, 0.5)  # (RESOURCE, THREAT, WELLBEING)
    state_delta: StateDelta = (0.0, 0.0, 0.0)
    goals: List[Goal] = field(default_factory=list)
    
    # PreData fields (v1.9)
    confidence_score: Optional[float] = None
    resource_usage: Optional[Dict[str, Any]] = None
    
    def to_self_state(self) -> SelfState:
        """Convert to SelfState for internal use."""
        return SelfState(
            state_vector=self.state_vector,
            state_delta=self.state_delta,
            goals=self.goals,
            confidence_score=self.confidence_score,
            resource_usage=self.resource_usage,
        )
    
    @classmethod
    def from_self_state(cls, state: SelfState) -> "SelfEvalResult":
        """Create from existing SelfState."""
        return cls(
            state_vector=state.state_vector,
            state_delta=state.state_delta,
            goals=state.goals,
            confidence_score=state.confidence_score,
            resource_usage=state.resource_usage,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            'state_vector': {
                'RESOURCE': self.state_vector[0],
                'THREAT': self.state_vector[1],
                'WELLBEING': self.state_vector[2],
            },
            'state_delta': {
                'd_RESOURCE': self.state_delta[0],
                'd_THREAT': self.state_delta[1],
                'd_WELLBEING': self.state_delta[2],
            },
            'goals_count': len(self.goals),
            'confidence_score': self.confidence_score,
            'resource_usage': self.resource_usage,
        }


__all__ = ['SelfEvalResult', 'SelfState']

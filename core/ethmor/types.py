# core/ethmor/types.py
"""
ETHMOR module type definitions.

Provides EthmorResult class as specified in master document.
Alias/wrapper to EthmorEvaluationResult for architectural consistency.

Author: UEM Project
Date: 30 November 2025
Version: 1.0 (Hybrid/Alias Strategy per Alice decision)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.ethmor.ethmor_system import (
    EthmorEvaluationResult,
    ActionDecision,
    ConstraintViolation,
    ConstraintType,
)


@dataclass
class EthmorResult:
    """
    Ethics evaluation result - Document-compliant interface.
    
    Master spec: UEM_PreData_Log_Master_Implementation_Document_Fix.md Section 6.2.3
    
    PreData Fields:
        - triggered_rules: List of triggered constraint details
        - risk_level: Overall ethical risk (0.0-1.0) - mapped from violation_score
        - ethical_confidence: Confidence in the ethical assessment (0.0-1.0)
    """
    # Core decision
    decision: str  # "allow", "flag", "block"
    
    # PreData fields (v1.9)
    triggered_rules: Optional[List[Dict[str, Any]]] = None
    risk_level: Optional[float] = None
    ethical_confidence: Optional[float] = None
    
    # Additional context
    explanation: Optional[str] = None
    hard_violation: bool = False
    
    @classmethod
    def from_evaluation_result(cls, result: EthmorEvaluationResult) -> "EthmorResult":
        """Create from existing EthmorEvaluationResult."""
        triggered_rules = []
        for violation in result.triggered_constraints:
            triggered_rules.append({
                'id': violation.constraint_id,
                'type': violation.constraint_type.value,
                'triggered': violation.triggered,
                'violation_score': violation.local_violation,
                'details': violation.details,
            })
        
        return cls(
            decision=result.decision.value.lower(),
            triggered_rules=triggered_rules if triggered_rules else None,
            risk_level=result.violation_score,
            ethical_confidence=result.ethical_confidence,
            explanation=result.explanation,
            hard_violation=result.hard_violation,
        )
    
    def to_evaluation_result(
        self,
        triggered_constraints: Optional[List[ConstraintViolation]] = None,
    ) -> EthmorEvaluationResult:
        """Convert to EthmorEvaluationResult for internal use."""
        decision_map = {
            'allow': ActionDecision.ALLOW,
            'flag': ActionDecision.FLAG,
            'block': ActionDecision.BLOCK,
        }
        decision_enum = decision_map.get(self.decision.lower(), ActionDecision.ALLOW)
        
        return EthmorEvaluationResult(
            violation_score=self.risk_level or 0.0,
            triggered_constraints=triggered_constraints or [],
            decision=decision_enum,
            explanation=self.explanation or "",
            hard_violation=self.hard_violation,
            ethical_confidence=self.ethical_confidence,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            'decision': self.decision,
            'triggered_rules': self.triggered_rules,
            'risk_level': self.risk_level,
            'ethical_confidence': self.ethical_confidence,
            'hard_violation': self.hard_violation,
        }
    
    @property
    def is_blocked(self) -> bool:
        return self.decision.lower() == 'block'
    
    @property
    def is_flagged(self) -> bool:
        return self.decision.lower() == 'flag'
    
    @property
    def is_allowed(self) -> bool:
        return self.decision.lower() == 'allow'


__all__ = [
    'EthmorResult',
    'EthmorEvaluationResult',
    'ActionDecision',
    'ConstraintViolation',
    'ConstraintType',
]

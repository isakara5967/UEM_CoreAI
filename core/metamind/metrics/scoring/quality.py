"""Quality scoring - measures outcome and output quality."""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass 
class QualityFactors:
    """Factors contributing to quality score."""
    outcome_success: float = 0.5
    confidence_level: float = 0.5
    completeness: float = 0.5
    appropriateness: float = 0.5


class QualityScorer:
    """
    Calculates outcome quality score for cognitive cycles.
    
    Quality measures how good the outcomes/outputs are.
    
    Usage:
        scorer = QualityScorer()
        score = scorer.calculate(cycle_data)
    """
    
    def __init__(self):
        self._history: List[float] = []
        self._success_count = 0
        self._total_count = 0
    
    def calculate(self, cycle_data: Dict[str, Any]) -> float:
        """Calculate quality score (0.0-1.0)."""
        factors = QualityFactors()
        
        # Outcome success
        factors.outcome_success = self._calc_outcome_success(cycle_data)
        
        # Confidence level
        factors.confidence_level = self._calc_confidence(cycle_data)
        
        # Completeness
        factors.completeness = self._calc_completeness(cycle_data)
        
        # Appropriateness (ETHMOR approval)
        factors.appropriateness = self._calc_appropriateness(cycle_data)
        
        # Weighted average
        score = (
            factors.outcome_success * 0.35 +
            factors.confidence_level * 0.25 +
            factors.completeness * 0.20 +
            factors.appropriateness * 0.20
        )
        
        self._history.append(score)
        self._total_count += 1
        if cycle_data.get("action_success"):
            self._success_count += 1
        
        return round(score, 3)
    
    def _calc_outcome_success(self, data: Dict) -> float:
        """Calculate outcome success score."""
        success = data.get("action_success")
        
        if success is True:
            return 1.0
        elif success is False:
            return 0.2
        else:
            # Unknown - use utility as proxy
            utility = data.get("utility", 0.5)
            return 0.4 + utility * 0.4
    
    def _calc_confidence(self, data: Dict) -> float:
        """Calculate confidence score."""
        # Check various confidence indicators
        confidence_values = []
        
        if "ethical_confidence" in data:
            confidence_values.append(data["ethical_confidence"])
        
        if "perception_confidence" in data:
            confidence_values.append(data["perception_confidence"])
        
        if "decision_confidence" in data:
            confidence_values.append(data["decision_confidence"])
        
        # Utility can indicate confidence
        if "utility" in data:
            confidence_values.append(data["utility"])
        
        if not confidence_values:
            return 0.5
        
        return sum(confidence_values) / len(confidence_values)
    
    def _calc_completeness(self, data: Dict) -> float:
        """Calculate action completeness."""
        # More complete data = higher completeness
        expected_fields = [
            "action_name", "utility", "valence", "arousal",
            "ethmor_decision", "novelty_score"
        ]
        
        present = sum(1 for f in expected_fields if data.get(f) is not None)
        return present / len(expected_fields)
    
    def _calc_appropriateness(self, data: Dict) -> float:
        """Calculate appropriateness (ethical compliance)."""
        ethmor_decision = data.get("ethmor_decision", "allow")
        risk_level = data.get("risk_level", 0.0)
        
        if ethmor_decision == "block":
            return 0.1  # Blocked = inappropriate action attempted
        elif ethmor_decision == "modify":
            return 0.6  # Modified = partially appropriate
        else:
            # Allowed - inverse of risk
            return 1.0 - (risk_level * 0.5)
    
    def get_success_rate(self) -> float:
        """Get success rate."""
        if self._total_count == 0:
            return 0.0
        return self._success_count / self._total_count
    
    def get_average(self) -> float:
        """Get average quality score."""
        if not self._history:
            return 0.5
        return sum(self._history) / len(self._history)
    
    def reset(self) -> None:
        """Reset history."""
        self._history.clear()
        self._success_count = 0
        self._total_count = 0

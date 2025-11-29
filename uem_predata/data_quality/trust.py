"""Source trust scoring."""
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class TrustFactors:
    """Factors contributing to trust score."""
    source_reputation: float = 0.5
    data_consistency: float = 0.5
    freshness: float = 0.5
    completeness: float = 0.5
    verification_status: float = 0.5


class TrustScorer:
    """
    Calculates source trust score.
    
    Trust is based on:
    - Source reputation (known vs unknown)
    - Data consistency
    - Freshness (how recent)
    - Completeness
    - Verification status
    """
    
    # Known trusted sources (expandable)
    TRUSTED_SOURCES = {
        "system": 1.0,
        "internal": 0.9,
        "verified": 0.85,
        "user": 0.7,
        "external": 0.5,
        "unknown": 0.3,
    }
    
    def __init__(self):
        self._source_cache: Dict[str, float] = {}
    
    def score(
        self,
        input_data: Any,
        source: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> float:
        """
        Calculate trust score (0.0 = untrusted, 1.0 = fully trusted).
        """
        factors = TrustFactors()
        
        # Source reputation
        if source:
            source_lower = source.lower()
            for key, score in self.TRUSTED_SOURCES.items():
                if key in source_lower:
                    factors.source_reputation = score
                    break
        
        # Data consistency check
        factors.data_consistency = self._check_consistency(input_data)
        
        # Completeness check
        factors.completeness = self._check_completeness(input_data)
        
        # Metadata factors
        if metadata:
            if metadata.get("verified"):
                factors.verification_status = 0.9
            if metadata.get("timestamp"):
                factors.freshness = 0.8  # Has timestamp = fresher
        
        # Weighted average
        weights = {
            "source_reputation": 0.3,
            "data_consistency": 0.25,
            "completeness": 0.2,
            "freshness": 0.15,
            "verification_status": 0.1,
        }
        
        score = (
            factors.source_reputation * weights["source_reputation"] +
            factors.data_consistency * weights["data_consistency"] +
            factors.completeness * weights["completeness"] +
            factors.freshness * weights["freshness"] +
            factors.verification_status * weights["verification_status"]
        )
        
        return round(score, 3)
    
    def _check_consistency(self, data: Any) -> float:
        """Check data consistency."""
        if data is None:
            return 0.3
        
        if isinstance(data, str):
            # Non-empty string is consistent
            return 0.8 if data.strip() else 0.2
        
        if isinstance(data, dict):
            if not data:
                return 0.3
            # Check for None values
            none_count = sum(1 for v in data.values() if v is None)
            ratio = 1 - (none_count / len(data))
            return max(0.3, ratio)
        
        if isinstance(data, list):
            return 0.7 if data else 0.3
        
        return 0.5
    
    def _check_completeness(self, data: Any) -> float:
        """Check data completeness."""
        if data is None:
            return 0.0
        
        if isinstance(data, str):
            if len(data) < 3:
                return 0.3
            elif len(data) < 10:
                return 0.5
            return 0.8
        
        if isinstance(data, dict):
            if not data:
                return 0.2
            # More keys = more complete
            return min(0.3 + len(data) * 0.1, 1.0)
        
        if isinstance(data, list):
            return min(0.3 + len(data) * 0.05, 1.0)
        
        return 0.5
    
    def register_source(self, source_id: str, trust_level: float) -> None:
        """Register a source with custom trust level."""
        self._source_cache[source_id] = max(0.0, min(1.0, trust_level))

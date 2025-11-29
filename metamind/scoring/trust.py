"""Trust aggregation - aggregates trust scores across sources."""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TrustRecord:
    """Record of trust for a source."""
    source_id: str
    trust_score: float
    sample_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TrustAggregator:
    """
    Aggregates trust scores across multiple sources and interactions.
    
    Maintains a moving average of trust for each source.
    
    Usage:
        aggregator = TrustAggregator()
        aggregator.update("source_1", trust_score=0.8)
        avg = aggregator.get_average_trust()
    """
    
    def __init__(self, decay_factor: float = 0.95):
        self._sources: Dict[str, TrustRecord] = {}
        self._decay_factor = decay_factor
        self._global_history: List[float] = []
    
    def update(
        self,
        source_id: str,
        trust_score: float,
        weight: float = 1.0
    ) -> float:
        """Update trust score for a source. Returns new score."""
        trust_score = max(0.0, min(1.0, trust_score))
        
        if source_id in self._sources:
            record = self._sources[source_id]
            # Exponential moving average
            old_score = record.trust_score
            new_score = (
                old_score * self._decay_factor + 
                trust_score * (1 - self._decay_factor) * weight
            )
            record.trust_score = new_score
            record.sample_count += 1
            record.last_updated = datetime.now(timezone.utc)
        else:
            self._sources[source_id] = TrustRecord(
                source_id=source_id,
                trust_score=trust_score,
                sample_count=1
            )
        
        self._global_history.append(trust_score)
        return self._sources[source_id].trust_score
    
    def get_trust(self, source_id: str) -> Optional[float]:
        """Get trust score for a source."""
        if source_id in self._sources:
            return self._sources[source_id].trust_score
        return None
    
    def get_average_trust(self) -> float:
        """Get average trust across all sources."""
        if not self._sources:
            return 0.5
        
        total = sum(r.trust_score for r in self._sources.values())
        return total / len(self._sources)
    
    def get_weighted_average(self) -> float:
        """Get sample-weighted average trust."""
        if not self._sources:
            return 0.5
        
        total_weight = sum(r.sample_count for r in self._sources.values())
        if total_weight == 0:
            return 0.5
        
        weighted_sum = sum(
            r.trust_score * r.sample_count 
            for r in self._sources.values()
        )
        return weighted_sum / total_weight
    
    def get_low_trust_sources(self, threshold: float = 0.4) -> List[str]:
        """Get sources below trust threshold."""
        return [
            source_id for source_id, record in self._sources.items()
            if record.trust_score < threshold
        ]
    
    def get_high_trust_sources(self, threshold: float = 0.8) -> List[str]:
        """Get sources above trust threshold."""
        return [
            source_id for source_id, record in self._sources.items()
            if record.trust_score >= threshold
        ]
    
    def get_all_records(self) -> Dict[str, Dict[str, Any]]:
        """Get all trust records."""
        return {
            source_id: {
                "trust_score": record.trust_score,
                "sample_count": record.sample_count,
                "last_updated": record.last_updated.isoformat()
            }
            for source_id, record in self._sources.items()
        }
    
    def decay_all(self) -> None:
        """Apply decay to all trust scores (for idle sources)."""
        for record in self._sources.values():
            record.trust_score *= self._decay_factor
    
    def reset(self) -> None:
        """Reset all trust data."""
        self._sources.clear()
        self._global_history.clear()

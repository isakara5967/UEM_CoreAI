"""Efficiency scoring - measures resource utilization and speed."""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class EfficiencyFactors:
    """Factors contributing to efficiency score."""
    time_efficiency: float = 0.5
    resource_usage: float = 0.5
    decision_speed: float = 0.5
    action_economy: float = 0.5


class EfficiencyScorer:
    """
    Calculates efficiency score for cognitive cycles.
    
    Efficiency measures how well resources (time, computation)
    are utilized to achieve goals.
    
    Usage:
        scorer = EfficiencyScorer()
        score = scorer.calculate(cycle_data)
    """
    
    # Target cycle time in ms
    TARGET_CYCLE_TIME_MS = 100.0
    MAX_ACCEPTABLE_TIME_MS = 500.0
    
    def __init__(self):
        self._history: List[float] = []
        self._cycle_times: List[float] = []
    
    def calculate(
        self,
        cycle_data: Dict[str, Any],
        target_time_ms: Optional[float] = None
    ) -> float:
        """Calculate efficiency score (0.0-1.0)."""
        target = target_time_ms or self.TARGET_CYCLE_TIME_MS
        
        factors = EfficiencyFactors()
        
        # Time efficiency
        cycle_time = cycle_data.get("cycle_time_ms", target)
        factors.time_efficiency = self._calc_time_efficiency(cycle_time, target)
        
        # Resource usage (tools, memory)
        factors.resource_usage = self._calc_resource_usage(cycle_data)
        
        # Decision speed (how quickly was action selected)
        factors.decision_speed = self._calc_decision_speed(cycle_data)
        
        # Action economy (achieving more with less)
        factors.action_economy = self._calc_action_economy(cycle_data)
        
        # Weighted average
        score = (
            factors.time_efficiency * 0.35 +
            factors.resource_usage * 0.25 +
            factors.decision_speed * 0.20 +
            factors.action_economy * 0.20
        )
        
        self._history.append(score)
        if cycle_time:
            self._cycle_times.append(cycle_time)
        
        return round(score, 3)
    
    def _calc_time_efficiency(self, actual_ms: float, target_ms: float) -> float:
        """Calculate time efficiency."""
        if actual_ms <= 0:
            return 0.5
        
        if actual_ms <= target_ms:
            return 1.0
        elif actual_ms <= target_ms * 2:
            # Linear decay
            return 1.0 - (actual_ms - target_ms) / target_ms * 0.5
        elif actual_ms <= self.MAX_ACCEPTABLE_TIME_MS:
            return 0.3
        else:
            return 0.1
    
    def _calc_resource_usage(self, data: Dict) -> float:
        """Calculate resource usage efficiency."""
        score = 0.7  # Base score
        
        # Tool usage
        tool_summary = data.get("tool_usage_summary", {})
        tools_used = tool_summary.get("tools_used", 0)
        
        if tools_used == 0:
            score += 0.1  # No tools = lightweight
        elif tools_used <= 2:
            score += 0.0  # Normal
        elif tools_used > 5:
            score -= 0.2  # Too many tools
        
        # Memory retrievals
        retrieval_count = data.get("retrieval_count", 0)
        if retrieval_count <= 3:
            score += 0.1
        elif retrieval_count > 10:
            score -= 0.1
        
        return max(0.0, min(score, 1.0))
    
    def _calc_decision_speed(self, data: Dict) -> float:
        """Calculate decision speed efficiency."""
        # Fewer candidate plans considered = faster decision
        candidates = data.get("candidate_plans", [])
        
        if not candidates:
            return 0.5
        
        num_candidates = len(candidates) if isinstance(candidates, list) else 3
        
        if num_candidates <= 2:
            return 0.9  # Quick decision
        elif num_candidates <= 4:
            return 0.7
        elif num_candidates <= 6:
            return 0.5
        else:
            return 0.3  # Too much deliberation
    
    def _calc_action_economy(self, data: Dict) -> float:
        """Calculate action economy (results per action)."""
        success = data.get("action_success")
        utility = data.get("utility", 0.5)
        
        if success is True:
            return 0.6 + utility * 0.4
        elif success is False:
            return 0.2 + utility * 0.2
        
        return 0.5 + utility * 0.3
    
    def get_average_cycle_time(self) -> Optional[float]:
        """Get average cycle time in ms."""
        if not self._cycle_times:
            return None
        return sum(self._cycle_times) / len(self._cycle_times)
    
    def get_average(self) -> float:
        """Get average efficiency score."""
        if not self._history:
            return 0.5
        return sum(self._history) / len(self._history)
    
    def reset(self) -> None:
        """Reset history."""
        self._history.clear()
        self._cycle_times.clear()

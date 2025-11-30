# core/predata/module_calculators.py
"""
Module-specific PreData Calculators for Workspace, Memory, and Self.

Author: UEM Project
Date: 30 November 2025
Version: 1.0
"""

from typing import Optional, Dict, Any, List
from collections import deque


class WorkspacePreDataCalculator:
    """Calculates workspace/consciousness PreData fields."""
    
    @staticmethod
    def compute_competition_intensity(
        winner_activation: float,
        total_activation: float,
        coalition_count: int = 1,
    ) -> float:
        """
        competition_intensity = 1 - (winner_activation / total_activation)
        
        High value = many coalitions competing closely
        Low value = clear winner
        """
        if total_activation <= 0 or coalition_count <= 1:
            return 0.0
        
        dominance_ratio = winner_activation / total_activation
        intensity = 1.0 - dominance_ratio
        
        coalition_factor = min(1.0, (coalition_count - 1) / 5)
        intensity = intensity * (0.5 + 0.5 * coalition_factor)
        
        return round(max(0.0, min(1.0, intensity)), 4)


class MemoryPreDataCalculator:
    """Calculates memory PreData fields."""
    
    DEFAULT_WM_CAPACITY = 7
    
    @staticmethod
    def compute_working_memory_load(
        item_count: int,
        capacity: int = 7,
    ) -> float:
        """working_memory_load = len(wm_items) / WM_CAPACITY"""
        if capacity <= 0:
            return 1.0
        return round(item_count / capacity, 4)
    
    @staticmethod
    def compute_memory_relevance(
        similarity_scores: List[float],
    ) -> Optional[float]:
        """Average relevance of retrieved memories."""
        if not similarity_scores:
            return None
        return round(sum(similarity_scores) / len(similarity_scores), 4)


class SelfPreDataCalculator:
    """Calculates self-evaluation PreData fields."""
    
    def __init__(self):
        self._success_history: deque = deque(maxlen=20)
        self._prediction_errors: deque = deque(maxlen=20)
    
    def record_outcome(self, success: bool, prediction_error: float = 0.0) -> None:
        """Record outcome for confidence calculation."""
        self._success_history.append(1.0 if success else 0.0)
        self._prediction_errors.append(abs(prediction_error))
    
    def compute_confidence_score(self) -> Optional[float]:
        """confidence = success_rate * consistency_factor"""
        if len(self._success_history) < 3:
            return None
        
        success_rate = sum(self._success_history) / len(self._success_history)
        
        if len(self._prediction_errors) >= 3:
            avg_error = sum(self._prediction_errors) / len(self._prediction_errors)
            consistency = 1.0 - min(1.0, avg_error)
        else:
            consistency = 1.0
        
        return round(success_rate * consistency, 4)
    
    @staticmethod
    def compute_resource_usage(
        cpu_time_ms: Optional[float] = None,
        memory_mb: Optional[float] = None,
        api_calls: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Compute resource usage dictionary."""
        usage = {}
        if cpu_time_ms is not None:
            usage['cpu_time_ms'] = round(cpu_time_ms, 2)
        if memory_mb is not None:
            usage['memory_mb'] = round(memory_mb, 2)
        if api_calls is not None:
            usage['api_calls'] = api_calls
        return usage if usage else None
    
    def reset(self) -> None:
        self._success_history.clear()
        self._prediction_errors.clear()


# Singletons
_workspace_calc: Optional[WorkspacePreDataCalculator] = None
_memory_calc: Optional[MemoryPreDataCalculator] = None
_self_calc: Optional[SelfPreDataCalculator] = None


def get_workspace_calculator() -> WorkspacePreDataCalculator:
    global _workspace_calc
    if _workspace_calc is None:
        _workspace_calc = WorkspacePreDataCalculator()
    return _workspace_calc


def get_memory_calculator() -> MemoryPreDataCalculator:
    global _memory_calc
    if _memory_calc is None:
        _memory_calc = MemoryPreDataCalculator()
    return _memory_calc


def get_self_calculator() -> SelfPreDataCalculator:
    global _self_calc
    if _self_calc is None:
        _self_calc = SelfPreDataCalculator()
    return _self_calc


__all__ = [
    'WorkspacePreDataCalculator',
    'MemoryPreDataCalculator',
    'SelfPreDataCalculator',
    'get_workspace_calculator',
    'get_memory_calculator',
    'get_self_calculator',
]

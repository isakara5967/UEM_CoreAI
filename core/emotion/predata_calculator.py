# core/emotion/predata_calculator.py
"""
Emotion PreData Calculator - Computes derived metrics for PreData logging.

Calculates:
- valence_delta: Change in valence from previous cycle
- arousal_volatility: Standard deviation of recent arousal values
- engagement: Combined arousal and attention metric
- mood_baseline: Long-term moving average of valence

Author: UEM Project
Date: 30 November 2025
Version: 1.0
"""

from collections import deque
from dataclasses import dataclass
from typing import Optional, Dict, Any
import math


@dataclass
class EmotionPreDataConfig:
    """Configuration for PreData calculations."""
    volatility_window: int = 10
    mood_window: int = 50
    engagement_arousal_weight: float = 0.6
    engagement_attention_weight: float = 0.4


class EmotionPreDataCalculator:
    """
    Calculates derived emotion metrics for PreData logging.
    
    Usage:
        calc = EmotionPreDataCalculator()
        predata = calc.compute(valence=0.5, arousal=0.6, attention_focus=0.7)
    """
    
    def __init__(self, config: Optional[EmotionPreDataConfig] = None):
        self.config = config or EmotionPreDataConfig()
        self._valence_history: deque = deque(maxlen=self.config.mood_window)
        self._arousal_history: deque = deque(maxlen=self.config.volatility_window)
        self._previous_valence: Optional[float] = None
        self._cycle_count: int = 0
    
    def compute(
        self,
        valence: float,
        arousal: float,
        attention_focus: Optional[float] = None,
        dominance: Optional[float] = None,
    ) -> Dict[str, Optional[float]]:
        """Compute all emotion PreData fields for current cycle."""
        self._cycle_count += 1
        
        valence_delta = self._compute_valence_delta(valence)
        arousal_volatility = self._compute_arousal_volatility(arousal)
        engagement = self._compute_engagement(arousal, attention_focus)
        mood_baseline = self._compute_mood_baseline(valence)
        
        self._update_history(valence, arousal)
        
        return {
            'valence_delta': valence_delta,
            'arousal_volatility': arousal_volatility,
            'engagement': engagement,
            'mood_baseline': mood_baseline,
        }
    
    def _compute_valence_delta(self, current_valence: float) -> Optional[float]:
        """valence_delta = current.valence - previous.valence"""
        if self._previous_valence is None:
            return None
        return round(current_valence - self._previous_valence, 4)
    
    def _compute_arousal_volatility(self, current_arousal: float) -> Optional[float]:
        """arousal_volatility = std(last_N_arousal_values)"""
        temp_history = list(self._arousal_history) + [current_arousal]
        if len(temp_history) < 3:
            return None
        
        n = len(temp_history)
        mean = sum(temp_history) / n
        variance = sum((x - mean) ** 2 for x in temp_history) / n
        return round(math.sqrt(variance), 4)
    
    def _compute_engagement(
        self,
        arousal: float,
        attention_focus: Optional[float] = None,
    ) -> float:
        """engagement = arousal * w_arousal + attention * w_attention"""
        if attention_focus is None:
            return round(arousal, 4)
        
        engagement = (
            arousal * self.config.engagement_arousal_weight +
            attention_focus * self.config.engagement_attention_weight
        )
        return round(max(0.0, min(1.0, engagement)), 4)
    
    def _compute_mood_baseline(self, current_valence: float) -> Optional[float]:
        """mood_baseline = moving_avg(valence, window=50)"""
        temp_history = list(self._valence_history) + [current_valence]
        if len(temp_history) < 5:
            return None
        return round(sum(temp_history) / len(temp_history), 4)
    
    def _update_history(self, valence: float, arousal: float) -> None:
        self._valence_history.append(valence)
        self._arousal_history.append(arousal)
        self._previous_valence = valence
    
    def reset(self) -> None:
        self._valence_history.clear()
        self._arousal_history.clear()
        self._previous_valence = None
        self._cycle_count = 0
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'cycle_count': self._cycle_count,
            'valence_history_size': len(self._valence_history),
            'arousal_history_size': len(self._arousal_history),
        }


# Singleton
_default_calculator: Optional[EmotionPreDataCalculator] = None


def get_emotion_predata_calculator() -> EmotionPreDataCalculator:
    global _default_calculator
    if _default_calculator is None:
        _default_calculator = EmotionPreDataCalculator()
    return _default_calculator


def compute_emotion_predata(
    valence: float,
    arousal: float,
    attention_focus: Optional[float] = None,
) -> Dict[str, Optional[float]]:
    """Convenience function using singleton."""
    return get_emotion_predata_calculator().compute(valence, arousal, attention_focus)


__all__ = [
    'EmotionPreDataCalculator',
    'EmotionPreDataConfig',
    'get_emotion_predata_calculator',
    'compute_emotion_predata',
]

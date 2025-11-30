"""Trend analysis for emotional and behavioral patterns."""
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from collections import deque
import statistics


class TrendDirection(Enum):
    """Trend direction."""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    VOLATILE = "volatile"


class TrendAnalyzer:
    """
    Analyzes trends in time-series metrics.
    
    Used for:
    - valence_trend
    - arousal_trend
    - Performance trends
    
    Usage:
        analyzer = TrendAnalyzer(window_size=10)
        analyzer.add(0.5)
        analyzer.add(0.6)
        trend = analyzer.get_trend()
    """
    
    def __init__(
        self,
        window_size: int = 10,
        stability_threshold: float = 0.1,
        volatility_threshold: float = 0.3
    ):
        self._window_size = window_size
        self._stability_threshold = stability_threshold
        self._volatility_threshold = volatility_threshold
        self._values: deque = deque(maxlen=window_size)
        self._all_values: List[float] = []
    
    def add(self, value: float) -> None:
        """Add a value to the series."""
        self._values.append(value)
        self._all_values.append(value)
    
    def get_trend(self) -> TrendDirection:
        """Determine current trend direction."""
        if len(self._values) < 3:
            return TrendDirection.STABLE
        
        values = list(self._values)
        
        # Calculate slope using simple linear regression
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Calculate volatility (standard deviation)
        try:
            volatility = statistics.stdev(values)
        except statistics.StatisticsError:
            volatility = 0
        
        # Determine trend
        if volatility > self._volatility_threshold:
            return TrendDirection.VOLATILE
        elif slope > self._stability_threshold:
            return TrendDirection.RISING
        elif slope < -self._stability_threshold:
            return TrendDirection.FALLING
        else:
            return TrendDirection.STABLE
    
    def get_trend_value(self) -> str:
        """Get trend as string value."""
        return self.get_trend().value
    
    def get_slope(self) -> float:
        """Calculate trend slope."""
        if len(self._values) < 2:
            return 0.0
        
        values = list(self._values)
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def get_volatility(self) -> float:
        """Calculate volatility (standard deviation)."""
        if len(self._values) < 2:
            return 0.0
        
        try:
            return statistics.stdev(self._values)
        except statistics.StatisticsError:
            return 0.0
    
    def get_average(self) -> float:
        """Get average value in window."""
        if not self._values:
            return 0.0
        return sum(self._values) / len(self._values)
    
    def get_min_max(self) -> Tuple[float, float]:
        """Get min and max in window."""
        if not self._values:
            return (0.0, 0.0)
        return (min(self._values), max(self._values))
    
    def get_range(self) -> float:
        """Get value range in window."""
        min_val, max_val = self.get_min_max()
        return max_val - min_val
    
    def get_summary(self) -> Dict[str, Any]:
        """Get trend analysis summary."""
        min_val, max_val = self.get_min_max()
        return {
            "trend": self.get_trend_value(),
            "slope": round(self.get_slope(), 4),
            "volatility": round(self.get_volatility(), 4),
            "average": round(self.get_average(), 4),
            "min": min_val,
            "max": max_val,
            "range": round(self.get_range(), 4),
            "sample_count": len(self._values)
        }
    
    def reset(self) -> None:
        """Reset analyzer."""
        self._values.clear()
        self._all_values.clear()

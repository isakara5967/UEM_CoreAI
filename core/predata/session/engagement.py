"""User engagement level tracking."""
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta


class EngagementLevel(Enum):
    """Engagement level buckets."""
    DISENGAGED = "disengaged"   # Minimal interaction
    LOW = "low"                  # Brief responses
    MEDIUM = "medium"            # Normal engagement
    HIGH = "high"                # Active participation
    VERY_HIGH = "very_high"      # Deep engagement


@dataclass
class EngagementSignals:
    """Signals used to determine engagement."""
    message_length: int = 0
    response_time_ms: Optional[float] = None
    question_count: int = 0
    detail_level: float = 0.0
    follow_up: bool = False
    code_provided: bool = False
    context_provided: bool = False


class EngagementTracker:
    """
    Tracks user engagement level throughout session.
    
    Usage:
        tracker = EngagementTracker()
        level = tracker.update(message="...", response_time_ms=1500)
    """
    
    def __init__(self):
        self._history: List[EngagementLevel] = []
        self._signals_history: List[EngagementSignals] = []
        self._last_message_time: Optional[datetime] = None
    
    def update(
        self,
        message: str,
        response_time_ms: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> EngagementLevel:
        """Update engagement based on new interaction."""
        signals = self._extract_signals(message, response_time_ms, context)
        self._signals_history.append(signals)
        
        level = self._calculate_level(signals)
        self._history.append(level)
        
        self._last_message_time = datetime.now(timezone.utc)
        return level
    
    def _extract_signals(
        self,
        message: str,
        response_time_ms: Optional[float],
        context: Optional[Dict[str, Any]]
    ) -> EngagementSignals:
        """Extract engagement signals from message."""
        signals = EngagementSignals()
        
        if message:
            signals.message_length = len(message)
            signals.question_count = message.count('?')
            
            # Detail level based on length and structure
            if len(message) > 200:
                signals.detail_level = 0.8
            elif len(message) > 100:
                signals.detail_level = 0.6
            elif len(message) > 50:
                signals.detail_level = 0.4
            else:
                signals.detail_level = 0.2
            
            # Code detection
            if '```' in message or '    ' in message:
                signals.code_provided = True
                signals.detail_level += 0.2
        
        signals.response_time_ms = response_time_ms
        
        if context:
            signals.follow_up = context.get("is_follow_up", False)
            signals.context_provided = context.get("has_context", False)
        
        return signals
    
    def _calculate_level(self, signals: EngagementSignals) -> EngagementLevel:
        """Calculate engagement level from signals."""
        score = 0.0
        
        # Message length contribution
        if signals.message_length > 300:
            score += 0.3
        elif signals.message_length > 100:
            score += 0.2
        elif signals.message_length > 30:
            score += 0.1
        elif signals.message_length < 10:
            score -= 0.2
        
        # Response time (faster = more engaged)
        if signals.response_time_ms:
            if signals.response_time_ms < 5000:
                score += 0.15
            elif signals.response_time_ms < 15000:
                score += 0.1
            elif signals.response_time_ms > 60000:
                score -= 0.1
        
        # Other signals
        score += signals.question_count * 0.05
        score += signals.detail_level * 0.2
        
        if signals.follow_up:
            score += 0.1
        if signals.code_provided:
            score += 0.15
        if signals.context_provided:
            score += 0.1
        
        # Map to levels
        if score >= 0.6:
            return EngagementLevel.VERY_HIGH
        elif score >= 0.4:
            return EngagementLevel.HIGH
        elif score >= 0.2:
            return EngagementLevel.MEDIUM
        elif score >= 0.0:
            return EngagementLevel.LOW
        else:
            return EngagementLevel.DISENGAGED
    
    @property
    def current_level(self) -> EngagementLevel:
        """Get most recent engagement level."""
        if not self._history:
            return EngagementLevel.MEDIUM
        return self._history[-1]
    
    def get_average_level(self) -> EngagementLevel:
        """Get average engagement level."""
        if not self._history:
            return EngagementLevel.MEDIUM
        
        level_values = {
            EngagementLevel.DISENGAGED: 0,
            EngagementLevel.LOW: 1,
            EngagementLevel.MEDIUM: 2,
            EngagementLevel.HIGH: 3,
            EngagementLevel.VERY_HIGH: 4,
        }
        
        avg = sum(level_values[l] for l in self._history) / len(self._history)
        
        if avg >= 3.5:
            return EngagementLevel.VERY_HIGH
        elif avg >= 2.5:
            return EngagementLevel.HIGH
        elif avg >= 1.5:
            return EngagementLevel.MEDIUM
        elif avg >= 0.5:
            return EngagementLevel.LOW
        else:
            return EngagementLevel.DISENGAGED
    
    def get_trend(self) -> str:
        """Get engagement trend."""
        if len(self._history) < 3:
            return "insufficient_data"
        
        level_values = {
            EngagementLevel.DISENGAGED: 0,
            EngagementLevel.LOW: 1,
            EngagementLevel.MEDIUM: 2,
            EngagementLevel.HIGH: 3,
            EngagementLevel.VERY_HIGH: 4,
        }
        
        recent = [level_values[l] for l in self._history[-3:]]
        older = [level_values[l] for l in self._history[-6:-3]] if len(self._history) >= 6 else [level_values[l] for l in self._history[:3]]
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        diff = recent_avg - older_avg
        if diff > 0.5:
            return "increasing"
        elif diff < -0.5:
            return "decreasing"
        return "stable"
    
    def reset(self) -> None:
        """Reset tracker."""
        self._history.clear()
        self._signals_history.clear()
        self._last_message_time = None

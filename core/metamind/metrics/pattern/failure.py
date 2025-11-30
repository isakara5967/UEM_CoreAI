"""Failure pattern tracking."""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class FailureEvent:
    """Record of a failure."""
    cycle_id: int
    action_name: str
    reason: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class FailureTracker:
    """
    Tracks failure patterns and streaks.
    
    Used to detect:
    - Consecutive failures (failure_streak)
    - Recovery attempts
    - Repeated failure patterns
    
    Usage:
        tracker = FailureTracker()
        tracker.record(success=False, action="explore")
        streak = tracker.current_streak
    """
    
    def __init__(self, streak_alert_threshold: int = 3):
        self._current_streak = 0
        self._max_streak = 0
        self._recovery_attempts = 0
        self._failures: List[FailureEvent] = []
        self._total_actions = 0
        self._streak_alert_threshold = streak_alert_threshold
        self._in_recovery = False
    
    def record(
        self,
        success: bool,
        action_name: str = "",
        cycle_id: int = 0,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record action outcome.
        Returns status dict with streak info.
        """
        self._total_actions += 1
        
        if success:
            # Success breaks streak
            was_in_streak = self._current_streak > 0
            self._current_streak = 0
            self._in_recovery = False
            
            return {
                "success": True,
                "streak_broken": was_in_streak,
                "current_streak": 0,
                "recovery_complete": was_in_streak
            }
        else:
            # Failure continues/starts streak
            self._current_streak += 1
            self._max_streak = max(self._max_streak, self._current_streak)
            
            self._failures.append(FailureEvent(
                cycle_id=cycle_id,
                action_name=action_name,
                reason=reason
            ))
            
            # Check if this is a recovery attempt
            if self._in_recovery:
                self._recovery_attempts += 1
            
            # Enter recovery mode after threshold
            if self._current_streak >= self._streak_alert_threshold:
                self._in_recovery = True
            
            return {
                "success": False,
                "current_streak": self._current_streak,
                "max_streak": self._max_streak,
                "alert": self._current_streak >= self._streak_alert_threshold,
                "in_recovery": self._in_recovery
            }
    
    @property
    def current_streak(self) -> int:
        """Get current failure streak."""
        return self._current_streak
    
    @property
    def max_streak(self) -> int:
        """Get maximum failure streak."""
        return self._max_streak
    
    @property
    def recovery_attempts(self) -> int:
        """Get number of recovery attempts."""
        return self._recovery_attempts
    
    def get_failure_rate(self) -> float:
        """Get overall failure rate."""
        if self._total_actions == 0:
            return 0.0
        return len(self._failures) / self._total_actions
    
    def get_recent_failures(self, n: int = 5) -> List[FailureEvent]:
        """Get N most recent failures."""
        return self._failures[-n:]
    
    def get_failure_actions(self) -> Dict[str, int]:
        """Get count of failures by action."""
        counts: Dict[str, int] = {}
        for f in self._failures:
            counts[f.action_name] = counts.get(f.action_name, 0) + 1
        return counts
    
    def get_most_failed_action(self) -> Optional[str]:
        """Get action with most failures."""
        counts = self.get_failure_actions()
        if not counts:
            return None
        return max(counts, key=counts.get)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get failure tracking summary."""
        return {
            "current_streak": self._current_streak,
            "max_streak": self._max_streak,
            "total_failures": len(self._failures),
            "total_actions": self._total_actions,
            "failure_rate": self.get_failure_rate(),
            "recovery_attempts": self._recovery_attempts,
            "in_recovery": self._in_recovery,
            "most_failed_action": self.get_most_failed_action()
        }
    
    def reset(self) -> None:
        """Reset tracker."""
        self._current_streak = 0
        self._max_streak = 0
        self._recovery_attempts = 0
        self._failures.clear()
        self._total_actions = 0
        self._in_recovery = False

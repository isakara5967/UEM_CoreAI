"""Session stage detection."""
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass


class SessionStage(Enum):
    """Session lifecycle stages."""
    INIT = "init"           # First interaction
    EARLY = "early"         # Building context (cycles 1-5)
    MID = "mid"             # Active engagement (cycles 6-20)
    LATE = "late"           # Wrapping up (cycles 21+)
    CLOSING = "closing"     # Explicit end signals


@dataclass
class StageTransition:
    """Records a stage transition."""
    from_stage: SessionStage
    to_stage: SessionStage
    cycle_id: int
    reason: str


class SessionStageDetector:
    """
    Detects current session stage based on interaction patterns.
    
    Usage:
        detector = SessionStageDetector()
        stage = detector.detect(cycle_count=10, signals={...})
    """
    
    # Default thresholds
    EARLY_THRESHOLD = 5
    MID_THRESHOLD = 20
    
    # Closing signals
    CLOSING_KEYWORDS = [
        "goodbye", "bye", "thanks", "thank you", "that's all",
        "done", "finished", "end", "close", "quit", "exit",
        "teşekkürler", "görüşürüz", "hoşçakal", "tamam", "bitti"
    ]
    
    def __init__(
        self,
        early_threshold: int = 5,
        mid_threshold: int = 20
    ):
        self.early_threshold = early_threshold
        self.mid_threshold = mid_threshold
        self._current_stage = SessionStage.INIT
        self._transitions: list[StageTransition] = []
        self._cycle_count = 0
    
    def detect(
        self,
        cycle_count: Optional[int] = None,
        user_message: Optional[str] = None,
        signals: Optional[Dict[str, Any]] = None
    ) -> SessionStage:
        """Detect current session stage."""
        if cycle_count is not None:
            self._cycle_count = cycle_count
        else:
            self._cycle_count += 1
        
        previous_stage = self._current_stage
        
        # Check for closing signals first
        if user_message and self._has_closing_signal(user_message):
            self._current_stage = SessionStage.CLOSING
        elif signals and signals.get("explicit_end"):
            self._current_stage = SessionStage.CLOSING
        # Stage by cycle count
        elif self._cycle_count <= 1:
            self._current_stage = SessionStage.INIT
        elif self._cycle_count <= self.early_threshold:
            self._current_stage = SessionStage.EARLY
        elif self._cycle_count <= self.mid_threshold:
            self._current_stage = SessionStage.MID
        else:
            self._current_stage = SessionStage.LATE
        
        # Record transition
        if previous_stage != self._current_stage:
            self._transitions.append(StageTransition(
                from_stage=previous_stage,
                to_stage=self._current_stage,
                cycle_id=self._cycle_count,
                reason=f"cycle_{self._cycle_count}"
            ))
        
        return self._current_stage
    
    def _has_closing_signal(self, message: str) -> bool:
        """Check if message contains closing signals."""
        message_lower = message.lower()
        return any(kw in message_lower for kw in self.CLOSING_KEYWORDS)
    
    @property
    def current_stage(self) -> SessionStage:
        return self._current_stage
    
    @property
    def transitions(self) -> list[StageTransition]:
        return self._transitions.copy()
    
    def reset(self) -> None:
        """Reset detector for new session."""
        self._current_stage = SessionStage.INIT
        self._transitions.clear()
        self._cycle_count = 0

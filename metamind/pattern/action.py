"""Action pattern analysis."""
from typing import Optional, Dict, Any, List
from collections import Counter, deque
from dataclasses import dataclass


@dataclass
class ActionPattern:
    """Detected action pattern."""
    pattern: tuple
    count: int
    frequency: float


class ActionAnalyzer:
    """
    Analyzes action patterns and diversity.
    
    Detects:
    - Action repetition
    - Action diversity
    - Common sequences
    - Stuck patterns
    
    Usage:
        analyzer = ActionAnalyzer()
        analyzer.record("explore")
        analyzer.record("explore")
        is_repeated = analyzer.is_repeated()
    """
    
    def __init__(self, window_size: int = 10):
        self._window_size = window_size
        self._actions: deque = deque(maxlen=window_size)
        self._all_actions: List[str] = []
        self._action_counts: Counter = Counter()
    
    def record(self, action_name: str) -> None:
        """Record an action."""
        self._actions.append(action_name)
        self._all_actions.append(action_name)
        self._action_counts[action_name] += 1
    
    def is_repeated(self, threshold: int = 3) -> bool:
        """Check if current action is repeated consecutively."""
        if len(self._actions) < threshold:
            return False
        
        recent = list(self._actions)[-threshold:]
        return len(set(recent)) == 1
    
    def get_repeated_action(self) -> Optional[str]:
        """Get currently repeated action if any."""
        if self.is_repeated():
            return self._actions[-1]
        return None
    
    def get_diversity_score(self) -> float:
        """
        Calculate action diversity score.
        1.0 = all different actions, 0.0 = all same action
        """
        if len(self._actions) <= 1:
            return 1.0
        
        unique = len(set(self._actions))
        total = len(self._actions)
        
        return unique / total
    
    def get_dominant_action(self) -> Optional[str]:
        """Get most frequent action in window."""
        if not self._actions:
            return None
        
        counter = Counter(self._actions)
        return counter.most_common(1)[0][0]
    
    def get_action_distribution(self) -> Dict[str, float]:
        """Get action frequency distribution in window."""
        if not self._actions:
            return {}
        
        counter = Counter(self._actions)
        total = len(self._actions)
        
        return {
            action: count / total
            for action, count in counter.items()
        }
    
    def detect_sequences(self, length: int = 2) -> List[ActionPattern]:
        """Detect repeated action sequences."""
        if len(self._all_actions) < length * 2:
            return []
        
        # Extract all sequences of given length
        sequences = []
        for i in range(len(self._all_actions) - length + 1):
            seq = tuple(self._all_actions[i:i + length])
            sequences.append(seq)
        
        # Count sequences
        counter = Counter(sequences)
        total = len(sequences)
        
        # Return patterns that appear more than once
        patterns = [
            ActionPattern(
                pattern=seq,
                count=count,
                frequency=count / total
            )
            for seq, count in counter.items()
            if count > 1
        ]
        
        return sorted(patterns, key=lambda p: p.count, reverse=True)
    
    def is_stuck(self, threshold: int = 5) -> bool:
        """Check if stuck in same action."""
        return self.is_repeated(threshold)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get action analysis summary."""
        return {
            "total_actions": len(self._all_actions),
            "unique_actions": len(set(self._all_actions)),
            "diversity_score": self.get_diversity_score(),
            "dominant_action": self.get_dominant_action(),
            "is_repeated": self.is_repeated(),
            "repeated_action": self.get_repeated_action(),
            "is_stuck": self.is_stuck(),
            "distribution": self.get_action_distribution()
        }
    
    def reset(self) -> None:
        """Reset analyzer."""
        self._actions.clear()
        self._all_actions.clear()
        self._action_counts.clear()

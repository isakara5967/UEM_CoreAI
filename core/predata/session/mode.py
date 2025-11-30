"""Interaction mode classification."""
from enum import Enum
from typing import Optional, Dict, Any, List
import re


class InteractionMode(Enum):
    """Types of user interaction modes."""
    CHAT = "chat"               # Casual conversation
    TASK = "task"               # Specific task completion
    EXPLORATION = "exploration" # Learning/exploring
    DEBUGGING = "debugging"     # Problem solving
    CREATION = "creation"       # Content creation
    ANALYSIS = "analysis"       # Data/content analysis
    UNKNOWN = "unknown"


class InteractionModeClassifier:
    """
    Classifies the current interaction mode.
    
    Usage:
        classifier = InteractionModeClassifier()
        mode = classifier.classify("Can you help me fix this bug in my code?")
    """
    
    MODE_PATTERNS = {
        InteractionMode.CHAT: [
            r'\b(hi|hello|hey|howdy|merhaba|selam)\b',
            r'\b(how are you|what\'s up|nasılsın)\b',
            r'\b(thanks|thank you|teşekkür)\b',
            r'^(ok|okay|tamam|anladım)$',
        ],
        InteractionMode.TASK: [
            r'\b(write|create|make|build|generate|implement)\b',
            r'\b(yaz|oluştur|yap|üret)\b',
            r'\b(need|want|require|must)\b',
            r'\b(please|lütfen)\b.*\b(help|yardım)\b',
        ],
        InteractionMode.EXPLORATION: [
            r'\b(what is|what are|what\'s|nedir|ne demek)\b',
            r'\b(explain|describe|tell me about|anlat|açıkla)\b',
            r'\b(how does|how do|nasıl)\b',
            r'\b(why|neden|niçin)\b',
            r'\b(learn|understand|öğren|anla)\b',
        ],
        InteractionMode.DEBUGGING: [
            r'\b(error|bug|issue|problem|fix|debug)\b',
            r'\b(hata|sorun|düzelt|çalışmıyor)\b',
            r'\b(not working|doesn\'t work|broken)\b',
            r'\b(exception|traceback|stack trace)\b',
            r'\b(why is|why does|why doesn\'t)\b.*\b(work|fail)\b',
        ],
        InteractionMode.CREATION: [
            r'\b(write|compose|draft|create)\b.*\b(story|article|post|email|essay)\b',
            r'\b(design|draw|generate)\b.*\b(image|logo|ui|interface)\b',
            r'\b(blog|content|copy|script)\b',
        ],
        InteractionMode.ANALYSIS: [
            r'\b(analyze|analyse|review|evaluate|assess)\b',
            r'\b(compare|contrast|difference)\b',
            r'\b(summarize|summary|özet)\b',
            r'\b(data|statistics|metrics|numbers)\b',
            r'\b(pros and cons|advantages|disadvantages)\b',
        ],
    }
    
    def __init__(self):
        self._compiled = {
            mode: [re.compile(p, re.I) for p in patterns]
            for mode, patterns in self.MODE_PATTERNS.items()
        }
        self._mode_history: List[InteractionMode] = []
    
    def classify(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> InteractionMode:
        """Classify the interaction mode."""
        if not user_message:
            return InteractionMode.UNKNOWN
        
        scores = {mode: 0 for mode in InteractionMode}
        
        # Pattern matching
        for mode, patterns in self._compiled.items():
            for pattern in patterns:
                matches = len(pattern.findall(user_message))
                scores[mode] += matches
        
        # Context signals
        if context:
            if context.get("has_code"):
                scores[InteractionMode.DEBUGGING] += 1
                scores[InteractionMode.TASK] += 1
            if context.get("has_question"):
                scores[InteractionMode.EXPLORATION] += 1
            if context.get("has_data"):
                scores[InteractionMode.ANALYSIS] += 1
        
        # Find best match
        best_mode = max(scores, key=scores.get)
        
        # If no patterns matched, infer from message structure
        if scores[best_mode] == 0:
            if '?' in user_message:
                best_mode = InteractionMode.EXPLORATION
            elif len(user_message) > 100:
                best_mode = InteractionMode.TASK
            else:
                best_mode = InteractionMode.CHAT
        
        self._mode_history.append(best_mode)
        return best_mode
    
    def get_dominant_mode(self) -> InteractionMode:
        """Get most frequent mode in session."""
        if not self._mode_history:
            return InteractionMode.UNKNOWN
        
        from collections import Counter
        counter = Counter(self._mode_history)
        return counter.most_common(1)[0][0]
    
    def get_mode_distribution(self) -> Dict[str, float]:
        """Get distribution of modes."""
        if not self._mode_history:
            return {}
        
        from collections import Counter
        counter = Counter(self._mode_history)
        total = len(self._mode_history)
        
        return {
            mode.value: count / total
            for mode, count in counter.items()
        }
    
    def reset(self) -> None:
        """Reset history."""
        self._mode_history.clear()

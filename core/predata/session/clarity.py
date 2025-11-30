"""User goal clarity scoring."""
from typing import Optional, Dict, Any, List
import re


class GoalClarityScorer:
    """
    Scores how clear the user's goal/intent is.
    
    Clarity indicators:
    - Specific vs vague language
    - Question structure
    - Context provided
    - Explicit instructions
    
    Usage:
        scorer = GoalClarityScorer()
        score = scorer.score("Please help me write a Python function that sorts a list")
    """
    
    # Vague indicators (reduce clarity)
    VAGUE_PATTERNS = [
        r'\b(something|anything|stuff|things?|whatever)\b',
        r'\b(maybe|perhaps|possibly|might|could be)\b',
        r'\b(sort of|kind of|kinda|sorta)\b',
        r'\b(etc|and so on|and more)\b',
        r'\b(idk|dunno|not sure)\b',
        r'\?{2,}',  # Multiple question marks
    ]
    
    # Clear indicators (increase clarity)
    CLEAR_PATTERNS = [
        r'\b(specifically|exactly|precisely)\b',
        r'\b(must|should|need to|have to|required)\b',
        r'\b(step[s]?\s*\d|first|second|then|finally)\b',
        r'\b(for example|e\.g\.|such as)\b',
        r'```',  # Code blocks
        r'\b\d+\s*(items?|steps?|points?)\b',  # Numbered items
    ]
    
    def __init__(self):
        self._vague_compiled = [re.compile(p, re.I) for p in self.VAGUE_PATTERNS]
        self._clear_compiled = [re.compile(p, re.I) for p in self.CLEAR_PATTERNS]
        self._history: List[float] = []
    
    def score(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Score goal clarity (0.0 = very vague, 1.0 = crystal clear).
        """
        if not user_message or not user_message.strip():
            return 0.0
        
        score = 0.5  # Base score
        
        # Length factor
        length = len(user_message)
        if length < 10:
            score -= 0.2
        elif length > 50:
            score += 0.1
        elif length > 200:
            score += 0.15
        
        # Vague patterns (subtract)
        vague_count = sum(len(p.findall(user_message)) for p in self._vague_compiled)
        score -= min(vague_count * 0.1, 0.3)
        
        # Clear patterns (add)
        clear_count = sum(len(p.findall(user_message)) for p in self._clear_compiled)
        score += min(clear_count * 0.1, 0.3)
        
        # Question structure
        if '?' in user_message:
            # Single clear question is good
            question_count = user_message.count('?')
            if question_count == 1:
                score += 0.05
            elif question_count > 3:
                score -= 0.1  # Too many questions = unclear
        
        # Context bonus
        if context:
            if context.get("has_code"):
                score += 0.1
            if context.get("has_examples"):
                score += 0.1
            if context.get("has_constraints"):
                score += 0.1
        
        # Clamp and store
        final_score = max(0.0, min(1.0, score))
        self._history.append(final_score)
        
        return round(final_score, 3)
    
    def get_average(self) -> float:
        """Get average clarity across session."""
        if not self._history:
            return 0.5
        return sum(self._history) / len(self._history)
    
    def get_trend(self) -> str:
        """Get clarity trend (improving/declining/stable)."""
        if len(self._history) < 3:
            return "insufficient_data"
        
        recent = self._history[-3:]
        older = self._history[-6:-3] if len(self._history) >= 6 else self._history[:3]
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        diff = recent_avg - older_avg
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        return "stable"
    
    def reset(self) -> None:
        """Reset history."""
        self._history.clear()

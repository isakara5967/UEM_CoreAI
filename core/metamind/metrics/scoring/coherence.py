"""Coherence scoring - measures consistency and logical flow."""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class CoherenceFactors:
    """Factors contributing to coherence score."""
    goal_action_alignment: float = 0.5
    emotion_behavior_consistency: float = 0.5
    plan_execution_match: float = 0.5
    memory_relevance: float = 0.5
    temporal_consistency: float = 0.5


class CoherenceScorer:
    """
    Calculates coherence score for cognitive cycles.
    
    Coherence measures how well different cognitive components
    work together consistently.
    
    Usage:
        scorer = CoherenceScorer()
        score = scorer.calculate(cycle_data)
    """
    
    def __init__(self):
        self._history: List[float] = []
        self._weights = {
            "goal_action_alignment": 0.25,
            "emotion_behavior_consistency": 0.20,
            "plan_execution_match": 0.25,
            "memory_relevance": 0.15,
            "temporal_consistency": 0.15,
        }
    
    def calculate(
        self,
        cycle_data: Dict[str, Any],
        previous_cycle: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate coherence score (0.0-1.0)."""
        factors = CoherenceFactors()
        
        # Goal-Action Alignment
        factors.goal_action_alignment = self._calc_goal_action_alignment(cycle_data)
        
        # Emotion-Behavior Consistency
        factors.emotion_behavior_consistency = self._calc_emotion_behavior(cycle_data)
        
        # Plan-Execution Match
        factors.plan_execution_match = self._calc_plan_execution(cycle_data)
        
        # Memory Relevance
        factors.memory_relevance = self._calc_memory_relevance(cycle_data)
        
        # Temporal Consistency (needs previous cycle)
        if previous_cycle:
            factors.temporal_consistency = self._calc_temporal_consistency(
                cycle_data, previous_cycle
            )
        
        # Weighted average
        score = (
            factors.goal_action_alignment * self._weights["goal_action_alignment"] +
            factors.emotion_behavior_consistency * self._weights["emotion_behavior_consistency"] +
            factors.plan_execution_match * self._weights["plan_execution_match"] +
            factors.memory_relevance * self._weights["memory_relevance"] +
            factors.temporal_consistency * self._weights["temporal_consistency"]
        )
        
        self._history.append(score)
        return round(score, 3)
    
    def _calc_goal_action_alignment(self, data: Dict) -> float:
        """How well does action align with goals?"""
        action = data.get("action_name")
        goals = data.get("goal_progress", {})
        utility = data.get("utility", 0.5)
        
        if not action:
            return 0.5
        
        # Higher utility suggests better alignment
        score = 0.3 + utility * 0.7
        
        # Bonus if goals are progressing
        if goals and any(v > 0 for v in goals.values() if isinstance(v, (int, float))):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calc_emotion_behavior(self, data: Dict) -> float:
        """Is behavior consistent with emotional state?"""
        valence = data.get("valence", 0.0)
        arousal = data.get("arousal", 0.5)
        action = data.get("action_name", "")
        
        # Define expected behaviors for emotional states
        negative_valence_actions = ["flee", "avoid", "wait", "retreat"]
        positive_valence_actions = ["approach", "explore", "help", "engage"]
        high_arousal_actions = ["flee", "attack", "rush"]
        
        score = 0.5
        
        if valence < -0.3 and action in negative_valence_actions:
            score += 0.3
        elif valence > 0.3 and action in positive_valence_actions:
            score += 0.3
        elif arousal > 0.7 and action in high_arousal_actions:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calc_plan_execution(self, data: Dict) -> float:
        """Did execution match the plan?"""
        planned_action = data.get("action_name")
        success = data.get("action_success")
        ethmor_decision = data.get("ethmor_decision", "allow")
        
        if planned_action is None:
            return 0.5
        
        score = 0.5
        
        # Success indicates good plan-execution match
        if success is True:
            score += 0.4
        elif success is False:
            score -= 0.2
        
        # ETHMOR block indicates plan wasn't executable
        if ethmor_decision == "block":
            score -= 0.3
        
        return max(0.0, min(score, 1.0))
    
    def _calc_memory_relevance(self, data: Dict) -> float:
        """Was retrieved memory relevant?"""
        relevance = data.get("memory_relevance", 0.5)
        retrieval_count = data.get("retrieval_count", 0)
        
        if retrieval_count == 0:
            return 0.5  # No memory access, neutral
        
        return relevance
    
    def _calc_temporal_consistency(
        self, 
        current: Dict, 
        previous: Dict
    ) -> float:
        """Is current state consistent with previous?"""
        score = 0.5
        
        # Check valence continuity (sudden jumps = inconsistent)
        prev_valence = previous.get("valence", 0)
        curr_valence = current.get("valence", 0)
        valence_diff = abs(curr_valence - prev_valence)
        
        if valence_diff < 0.2:
            score += 0.3
        elif valence_diff > 0.6:
            score -= 0.2
        
        # Check action continuity
        prev_action = previous.get("action_name")
        curr_action = current.get("action_name")
        
        if prev_action == curr_action:
            score += 0.1  # Consistency, but might indicate stuck
        
        return max(0.0, min(score, 1.0))
    
    def get_average(self) -> float:
        """Get average coherence score."""
        if not self._history:
            return 0.5
        return sum(self._history) / len(self._history)
    
    def reset(self) -> None:
        """Reset history."""
        self._history.clear()

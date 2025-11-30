"""
Behavior clustering - groups similar behavioral patterns.
v1: Simple rule-based clustering (placeholder for future ML).
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass


class BehaviorCluster(Enum):
    """Predefined behavior clusters."""
    EXPLORER = "explorer"           # High action diversity, curious
    CAUTIOUS = "cautious"           # Low risk, many waits
    AGGRESSIVE = "aggressive"       # High arousal, attack-heavy
    SOCIAL = "social"               # Help/approach focused
    STUCK = "stuck"                 # Repetitive actions
    BALANCED = "balanced"           # Mixed behaviors
    UNKNOWN = "unknown"


@dataclass
class ClusterAssignment:
    """Cluster assignment result."""
    cluster: BehaviorCluster
    confidence: float
    features: Dict[str, float]


class BehaviorClusterer:
    """
    Assigns behavior clusters based on action patterns.
    
    v1: Rule-based heuristics
    v2+: ML-based clustering (future)
    
    Usage:
        clusterer = BehaviorClusterer()
        clusterer.add_action("explore", {"arousal": 0.5})
        assignment = clusterer.get_cluster()
    """
    
    def __init__(self, window_size: int = 20):
        self._window_size = window_size
        self._actions: List[str] = []
        self._features: List[Dict[str, float]] = []
    
    def add_action(
        self,
        action_name: str,
        features: Optional[Dict[str, float]] = None
    ) -> None:
        """Add an action to the window."""
        self._actions.append(action_name)
        self._features.append(features or {})
        
        # Keep window size
        if len(self._actions) > self._window_size:
            self._actions.pop(0)
            self._features.pop(0)
    
    def get_cluster(self) -> ClusterAssignment:
        """Determine current behavior cluster."""
        if len(self._actions) < 5:
            return ClusterAssignment(
                cluster=BehaviorCluster.UNKNOWN,
                confidence=0.0,
                features={}
            )
        
        # Calculate features
        features = self._calculate_features()
        
        # Rule-based assignment
        cluster, confidence = self._assign_cluster(features)
        
        return ClusterAssignment(
            cluster=cluster,
            confidence=confidence,
            features=features
        )
    
    def _calculate_features(self) -> Dict[str, float]:
        """Calculate clustering features."""
        from collections import Counter
        
        total = len(self._actions)
        counts = Counter(self._actions)
        
        # Action frequencies
        explore_freq = counts.get("explore", 0) / total
        wait_freq = counts.get("wait", 0) / total
        attack_freq = counts.get("attack", 0) / total
        help_freq = counts.get("help", 0) / total
        approach_freq = counts.get("approach", 0) / total
        flee_freq = counts.get("flee", 0) / total
        
        # Diversity (unique actions / total)
        diversity = len(counts) / total
        
        # Repetition (max single action frequency)
        max_freq = max(counts.values()) / total
        
        # Average arousal (if available)
        arousals = [f.get("arousal", 0.5) for f in self._features if "arousal" in f]
        avg_arousal = sum(arousals) / len(arousals) if arousals else 0.5
        
        return {
            "explore_freq": explore_freq,
            "wait_freq": wait_freq,
            "attack_freq": attack_freq,
            "help_freq": help_freq,
            "approach_freq": approach_freq,
            "flee_freq": flee_freq,
            "diversity": diversity,
            "max_freq": max_freq,
            "avg_arousal": avg_arousal,
        }
    
    def _assign_cluster(
        self,
        features: Dict[str, float]
    ) -> tuple[BehaviorCluster, float]:
        """Assign cluster based on features."""
        
        # STUCK: Very low diversity, high repetition
        if features["diversity"] < 0.15 and features["max_freq"] > 0.7:
            return BehaviorCluster.STUCK, 0.9
        
        # AGGRESSIVE: High attack + high arousal
        if features["attack_freq"] > 0.3 and features["avg_arousal"] > 0.6:
            return BehaviorCluster.AGGRESSIVE, 0.8
        
        # CAUTIOUS: High wait + flee, low arousal
        if features["wait_freq"] + features["flee_freq"] > 0.5:
            return BehaviorCluster.CAUTIOUS, 0.75
        
        # SOCIAL: High help + approach
        if features["help_freq"] + features["approach_freq"] > 0.4:
            return BehaviorCluster.SOCIAL, 0.75
        
        # EXPLORER: High explore + high diversity
        if features["explore_freq"] > 0.3 and features["diversity"] > 0.4:
            return BehaviorCluster.EXPLORER, 0.8
        
        # BALANCED: Default
        return BehaviorCluster.BALANCED, 0.6
    
    def get_cluster_id(self) -> str:
        """Get cluster ID string for logging."""
        return self.get_cluster().cluster.value
    
    def reset(self) -> None:
        """Reset clusterer."""
        self._actions.clear()
        self._features.clear()

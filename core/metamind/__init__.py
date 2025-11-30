"""
MetaMind - Meta-cognitive system for UEM.

Contains two subsystems:
- social/: Theory of Mind, empathy, social cognition
- metrics/: Self-monitoring, pattern analysis, alerts
"""
from .metamind_core import MetaMindCore

# Social exports
from .social import (
    EmotionalEmpathyUnit,
    CognitiveEmpathyUnit,
    SocialContextUnit,
    RelationalMappingUnit,
    EthicalSocialFilterUnit,
    HumanStatePredictorUnit,
    SocialSimulationEngine,
)

# Metrics exports
from .metrics import (
    CoherenceScorer,
    EfficiencyScorer,
    QualityScorer,
    TrustAggregator,
    FailureTracker,
    ActionAnalyzer,
    TrendAnalyzer,
    AlertManager,
    Alert,
    AlertSeverity,
    AlertCategory,
    BehaviorClusterer,
)

__all__ = [
    "MetaMindCore",
    # Social
    "EmotionalEmpathyUnit",
    "CognitiveEmpathyUnit",
    "SocialContextUnit",
    "RelationalMappingUnit",
    "EthicalSocialFilterUnit",
    "HumanStatePredictorUnit",
    "SocialSimulationEngine",
    # Metrics
    "CoherenceScorer",
    "EfficiencyScorer",
    "QualityScorer",
    "TrustAggregator",
    "FailureTracker",
    "ActionAnalyzer",
    "TrendAnalyzer",
    "AlertManager",
    "Alert",
    "AlertSeverity",
    "AlertCategory",
    "BehaviorClusterer",
]

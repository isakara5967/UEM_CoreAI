"""
MetaMind - Meta-cognitive analysis and metrics derivation.
Version: 1.0 (Phase D)
"""

from .scoring import (
    CoherenceScorer,
    EfficiencyScorer,
    QualityScorer,
    TrustAggregator,
)
from .pattern import (
    FailureTracker,
    ActionAnalyzer,
    TrendAnalyzer,
)
from .alerts import (
    AlertManager,
    Alert,
    AlertSeverity,
    AlertCategory,
)

__version__ = "1.0.0"
__all__ = [
    # Scoring
    "CoherenceScorer",
    "EfficiencyScorer",
    "QualityScorer",
    "TrustAggregator",
    # Pattern
    "FailureTracker",
    "ActionAnalyzer",
    "TrendAnalyzer",
    # Alerts
    "AlertManager",
    "Alert",
    "AlertSeverity",
    "AlertCategory",
]

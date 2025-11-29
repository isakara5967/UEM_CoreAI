"""
UEM PreData - Data collection for cognitive cycle analysis.
Version: 1.0 (Phase B + C)
"""

from .collector import PreDataCollector, PreData

# Data Quality
from .data_quality import (
    ModalityDetector,
    NoiseEstimator,
    TrustScorer,
    QualityFlagger,
    LanguageDetector,
)

# Tooling
from .tooling import (
    ToolTracker,
    ToolUsage,
    EnvironmentProfiler,
    PolicyManager,
    AdversarialDetector,
)

# Session
from .session import (
    SessionStageDetector,
    SessionStage,
    GoalClarityScorer,
    InteractionModeClassifier,
    InteractionMode,
    EngagementTracker,
    EngagementLevel,
    ExperimentManager,
)

__version__ = "1.0.0"
__all__ = [
    # Core
    "PreDataCollector",
    "PreData",
    # Data Quality
    "ModalityDetector",
    "NoiseEstimator",
    "TrustScorer",
    "QualityFlagger",
    "LanguageDetector",
    # Tooling
    "ToolTracker",
    "ToolUsage",
    "EnvironmentProfiler",
    "PolicyManager",
    "AdversarialDetector",
    # Session
    "SessionStageDetector",
    "SessionStage",
    "GoalClarityScorer",
    "InteractionModeClassifier",
    "InteractionMode",
    "EngagementTracker",
    "EngagementLevel",
    "ExperimentManager",
]

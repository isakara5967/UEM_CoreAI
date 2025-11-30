# core/predata/__init__.py
"""
UEM PreData - Data collection for cognitive cycle analysis.
Version: 1.1 (Phase B + C + Calculators)
"""

# === Core Collector ===
from .collector import PreDataCollector, PreData

# === NEW: Multi-Agent Calculators (v1.0) ===
from .calculators import (
    # Config
    EMPATHY_WEIGHT,
    RESONANCE_WEIGHT,
    CONFIDENCE_WEIGHT,
    RELATIONSHIP_CONFLICT_WEIGHT,
    GOAL_CONFLICT_WEIGHT,
    COORDINATION_MODES,
    # Data classes
    EmpathyData,
    MultiAgentResult,
    # Single calculations
    calculate_empathy_score,
    calculate_empathy_score_from_result,
    calculate_conflict_score,
    calculate_conflict_score_from_result,
    estimate_goal_overlap,
    calculate_agent_count,
    calculate_coordination_mode,
    calculate_coordination_mode_single,
    # Aggregation
    aggregate_empathy_scores,
    aggregate_conflict_scores,
    aggregate_coordination_modes,
    # Unified
    calculate_all_multiagent_fields,
)

# === Module Calculators ===
from .module_calculators import (
    WorkspacePreDataCalculator,
    MemoryPreDataCalculator,
    SelfPreDataCalculator,
    get_workspace_calculator,
    get_memory_calculator,
    get_self_calculator,
)

# === Data Quality ===
from .data_quality import (
    ModalityDetector,
    NoiseEstimator,
    TrustScorer,
    QualityFlagger,
    LanguageDetector,
)

# === Tooling ===
from .tooling import (
    ToolTracker,
    ToolUsage,
    EnvironmentProfiler,
    PolicyManager,
    AdversarialDetector,
)

# === Session ===
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

# === Multi-Agent Coordinator ===
from .multi_agent import MultiAgentCoordinator, CoordinationMode

__version__ = "1.1.0"
__all__ = [
    # Core
    "PreDataCollector",
    "PreData",
    # Calculators (NEW)
    "EMPATHY_WEIGHT",
    "RESONANCE_WEIGHT",
    "CONFIDENCE_WEIGHT",
    "RELATIONSHIP_CONFLICT_WEIGHT",
    "GOAL_CONFLICT_WEIGHT",
    "COORDINATION_MODES",
    "EmpathyData",
    "MultiAgentResult",
    "calculate_empathy_score",
    "calculate_empathy_score_from_result",
    "calculate_conflict_score",
    "calculate_conflict_score_from_result",
    "estimate_goal_overlap",
    "calculate_agent_count",
    "calculate_coordination_mode",
    "calculate_coordination_mode_single",
    "aggregate_empathy_scores",
    "aggregate_conflict_scores",
    "aggregate_coordination_modes",
    "calculate_all_multiagent_fields",
    # Module Calculators
    "WorkspacePreDataCalculator",
    "MemoryPreDataCalculator",
    "SelfPreDataCalculator",
    "get_workspace_calculator",
    "get_memory_calculator",
    "get_self_calculator",
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
    # Multi-Agent
    "MultiAgentCoordinator",
    "CoordinationMode",
]

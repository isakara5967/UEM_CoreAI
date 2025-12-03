"""
MetaMind v1.9 - Unified Meta-Cognitive Analysis System
======================================================

MetaMind, UEM ajanının meta-bilişsel yeteneklerini sağlar:
- Episode-based zaman yönetimi (100 cycle = 1 episode)
- 6 meta-state değişkeni (global_health, emotional_stability, vb.)
- Pattern mining (action sequences, emotion trends)
- Anomaly detection
- Human-readable insights

Modüller:
- types: Domain types (MetaState, Episode, MetaEvent, vb.)
- storage: DB operations
- core: MetaMindCore orchestrator + scheduler
- meta_state: MetaState hesaplama
- episodes: Episode lifecycle
- adapters: Mevcut scorer'ları wrap
- analyzers: Cycle analysis, pattern mining
- evaluation: Episode-level değerlendirme
- pipelines: Social health (STUB)
- insights: Human-readable raporlar

Kullanım:
    from core.metamind import MetaMindCore, MetaState, Episode
    
    metamind = MetaMindCore(config_path="config/metamind.yaml")
    metamind.initialize(run_id)
    
    # Her cycle sonunda
    meta_state = metamind.on_cycle_end(cycle_id, cycle_data)
    
    # Run sonunda
    metamind.on_run_end_sync()

⚠️ Alice Notları:
- Episode window (100) config'ten gelmeli, hardcode YASAK
- Her metrik confidence ile loglanmalı
- Social pipeline STUB - v2.0'da implement edilecek
"""

# ============================================================
# VERSION
# ============================================================

__version__ = "1.9.0"

# ============================================================
# TYPES - Domain models
# ============================================================

from .types import (
    # Enums
    EventType,
    Severity,
    PatternType,
    InsightType,
    InsightScope,
    BoundaryReason,
    JobMode,
    # Dataclasses
    MetaEvent,
    MetaPattern,
    MetaInsight,
    Episode,
    MetricWithConfidence,
    MetaState,
    Job,
    MetricsSnapshot,
)

# ============================================================
# STORAGE - DB operations
# ============================================================

from .storage import (
    MetaMindStorage,
    create_metamind_storage,
)

# ============================================================
# CORE - Main orchestrator
# ============================================================

from .core import (
    MetaMindCore,
    MetaMindConfig,
    create_metamind_core,
)

# ============================================================
# META STATE - Calculation
# ============================================================

from .meta_state import (
    MetaStateCalculator,
    MetaStateConfig,
    create_meta_state_calculator,
)

# ============================================================
# EPISODES - Lifecycle management
# ============================================================

from .episodes import (
    EpisodeManager,
    EpisodeConfig,
    create_episode_manager,
)

# ============================================================
# ADAPTERS - Scorer wrappers
# ============================================================

from .adapters import (
    MetricsAdapter,
    create_metrics_adapter,
)

# ============================================================
# ANALYZERS - Cycle & pattern analysis
# ============================================================

from .analyzers import (
    MicroCycleAnalyzer,
    PatternMiner,
    create_cycle_analyzer,
    create_pattern_miner,
)

# ============================================================
# EVALUATION - Episode-level analysis
# ============================================================

from .evaluation import (
    EpisodeEvaluator,
    EpisodeHealthReport,
    create_episode_evaluator,
)

# ============================================================
# PIPELINES - Specialized pipelines
# ============================================================

from .pipelines import (
    SocialHealthPipeline,
    SocialHealthMetrics,
    create_social_pipeline,
)

# ============================================================
# INSIGHTS - Human-readable reports
# ============================================================

from .insights import (
    InsightGenerator,
    create_insight_generator,
)

# ============================================================
# METRICS - Existing scorers (unchanged)
# ============================================================

# Mevcut metrics modülü değişmedi, backward compatibility
from .metrics import (
    CoherenceScorer,
    EfficiencyScorer,
    QualityScorer,
    TrustAggregator,
    FailureTracker,
    ActionAnalyzer,
    TrendAnalyzer,
    AlertManager,
    BehaviorClusterer,
)

# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Version
    '__version__',
    
    # Types - Enums
    'EventType',
    'Severity',
    'PatternType',
    'InsightType',
    'InsightScope',
    'BoundaryReason',
    'JobMode',
    
    # Types - Dataclasses
    'MetaEvent',
    'MetaPattern',
    'MetaInsight',
    'Episode',
    'MetricWithConfidence',
    'MetaState',
    'Job',
    'MetricsSnapshot',
    
    # Storage
    'MetaMindStorage',
    'create_metamind_storage',
    
    # Core
    'MetaMindCore',
    'MetaMindConfig',
    'create_metamind_core',
    
    # MetaState
    'MetaStateCalculator',
    'MetaStateConfig',
    'create_meta_state_calculator',
    
    # Episodes
    'EpisodeManager',
    'EpisodeConfig',
    'create_episode_manager',
    
    # Adapters
    'MetricsAdapter',
    'create_metrics_adapter',
    
    # Analyzers
    'MicroCycleAnalyzer',
    'PatternMiner',
    'create_cycle_analyzer',
    'create_pattern_miner',
    
    # Evaluation
    'EpisodeEvaluator',
    'EpisodeHealthReport',
    'create_episode_evaluator',
    
    # Pipelines
    'SocialHealthPipeline',
    'SocialHealthMetrics',
    'create_social_pipeline',
    
    # Insights
    'InsightGenerator',
    'create_insight_generator',
    
    # Metrics (existing)
    'CoherenceScorer',
    'EfficiencyScorer',
    'QualityScorer',
    'TrustAggregator',
    'FailureTracker',
    'ActionAnalyzer',
    'TrendAnalyzer',
    'AlertManager',
    'BehaviorClusterer',
]

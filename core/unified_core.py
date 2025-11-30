# core/unified_core.py
"""
Unified UEM Core - All modules integrated

9-phase cognitive cycle:
1. PERCEPTION    - World → PerceptionResult
2. MEMORY        - Retrieve relevant memories
3. SELF UPDATE   - Update state_vector, deltas
4. APPRAISAL     - Emotional evaluation
5. EMPATHY       - Social context (if OTHER detected)
6. PLANNING      - Select action via Planner
7. ETHMOR        - (handled inside Planner)
8. EXECUTION     - Execute action
9. LEARNING      - Update memory, somatic markers

Author: UEM Project
Date: 26 November 2025
"""

from __future__ import annotations

# Logger Integration (Phase E)
try:
    from core.logger_integration import CoreLoggerIntegration
    LOGGER_INTEGRATION_AVAILABLE = True
except ImportError:
    LOGGER_INTEGRATION_AVAILABLE = False
    CoreLoggerIntegration = None

# PreData Calculators (Phase 1 Integration)
try:
    from core.emotion.predata_calculator import EmotionPreDataCalculator
    from core.planning.predata_calculator import PlannerPreDataCalculator
    from core.perception.predata_calculator import PerceptionPreDataCalculator
    from core.predata.calculators import calculate_all_multiagent_fields
    from core.predata.module_calculators import (
        WorkspacePreDataCalculator,
        MemoryPreDataCalculator,
        SelfPreDataCalculator,
    )
    PREDATA_CALCULATORS_AVAILABLE = True
except ImportError:
    PREDATA_CALCULATORS_AVAILABLE = False
    EmotionPreDataCalculator = None
    PlannerPreDataCalculator = None
    PerceptionPreDataCalculator = None

# Data Quality modules
try:
    from core.predata.data_quality import (
        ModalityDetector,
        NoiseEstimator,
        TrustScorer,
        QualityFlagger,
        LanguageDetector,
    )
    DATA_QUALITY_AVAILABLE = True
except ImportError:
    DATA_QUALITY_AVAILABLE = False
    ModalityDetector = None
    NoiseEstimator = None
    TrustScorer = None
    QualityFlagger = None
    LanguageDetector = None

# Session tracking modules
try:
    from core.predata.session import (
        SessionStageDetector,
        GoalClarityScorer,
        InteractionModeClassifier,
        EngagementTracker,
        ExperimentManager,
    )
    SESSION_AVAILABLE = True
except ImportError:
    SESSION_AVAILABLE = False

# Tooling/Environment modules
try:
    from core.predata.tooling import (
        ToolTracker,
        EnvironmentProfiler,
        PolicyManager,
        AdversarialDetector,
    )
    TOOLING_AVAILABLE = True
except ImportError:
    TOOLING_AVAILABLE = False

# Multi-Agent modules
try:
    from core.multi_agent import MultiAgentCoordinator, CoordinationMode
    MULTI_AGENT_AVAILABLE = True
except ImportError:
    MULTI_AGENT_AVAILABLE = False

# MetaMind modules (scoring, pattern, alerts)
try:
    from core.metamind.metrics import (
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
    METAMIND_AVAILABLE = True
except ImportError:
    METAMIND_AVAILABLE = False

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from core.unified_types import (
    MemoryContext,
    SelfState,
    AppraisalResult,
    ActionResult,
    CycleMetrics,
)

# Core modules
from core.planning.planner_v2 import PlannerV2
from core.planning.types import PlanningContext, ActionPlan

# Conditional imports with fallbacks
try:
    from core.perception.perception_core import PerceptionCore
    from core.perception.types import WorldSnapshot, PerceptionResult
    PERCEPTION_AVAILABLE = True
except ImportError:
    PERCEPTION_AVAILABLE = False
    PerceptionCore = None

try:
    from core.memory.memory_interface import create_memory_interface, MemoryInterface
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    create_memory_interface = None

try:
    from core.self.self_core import SelfCore
    SELF_AVAILABLE = True
except ImportError:
    SELF_AVAILABLE = False
    SelfCore = None

try:
    from core.emotion.somatic_marker_system import SomaticMarkerSystem
    SOMATIC_AVAILABLE = True
except ImportError:
    SOMATIC_AVAILABLE = False
    SomaticMarkerSystem = None

try:
    from core.emotion import EmotionCore
    EMOTION_AVAILABLE = True
except ImportError:
    EMOTION_AVAILABLE = False
    EmotionCore = None

try:
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
    EMPATHY_AVAILABLE = True
except ImportError:
    EMPATHY_AVAILABLE = False
    EmpathyOrchestrator = None

try:
    from core.ethmor import EthmorSystem
    ETHMOR_AVAILABLE = True
except ImportError:
    ETHMOR_AVAILABLE = False
    EthmorSystem = None

# Consciousness / Global Workspace (Sprint 0B)
try:
    from core.consciousness.global_workspace import (
        WorkspaceManager,
        BroadcastMessage,
        ContentType,
        WorkspaceSubscriber,
        create_workspace_manager,
    )
    CONSCIOUSNESS_AVAILABLE = True
except ImportError:
    CONSCIOUSNESS_AVAILABLE = False
    WorkspaceManager = None
    BroadcastMessage = None

try:
    from core.integrated_uem_core import WorldState
    WORLDSTATE_AVAILABLE = True
except ImportError:
    WORLDSTATE_AVAILABLE = False
    # Fallback WorldState
    from dataclasses import dataclass, field
    
    @dataclass
    class WorldState:
        tick: int = 0
        danger_level: float = 0.0
        objects: List[Dict[str, Any]] = field(default_factory=list)
        agents: List[Dict[str, Any]] = field(default_factory=list)
        symbols: List[str] = field(default_factory=list)
        player_health: float = 1.0
        player_energy: float = 1.0


# ============================================================================
# WORKSPACE SUBSCRIBERS (Sprint 0B)
# ============================================================================

class PerceptionSubscriber:
    """Perception modülü için workspace subscriber."""
    
    def __init__(self, core: "UnifiedUEMCore"):
        self.core = core
        self.last_broadcast: Optional[BroadcastMessage] = None
    
    @property
    def subscriber_name(self) -> str:
        return "PerceptionSubscriber"
    
    async def receive_broadcast(self, message: "BroadcastMessage") -> None:
        self.last_broadcast = message
        self.core.logger.debug(f"[Perception] Received broadcast: {message.content_type}")


class MemorySubscriber:
    """Memory modülü için workspace subscriber."""
    
    def __init__(self, core: "UnifiedUEMCore"):
        self.core = core
        self.last_broadcast: Optional[BroadcastMessage] = None
    
    @property
    def subscriber_name(self) -> str:
        return "MemorySubscriber"
    
    async def receive_broadcast(self, message: "BroadcastMessage") -> None:
        self.last_broadcast = message
        self.core.logger.debug(f"[Memory] Received broadcast: {message.content_type}")


class PlanningSubscriber:
    """Planning modülü için workspace subscriber."""
    
    def __init__(self, core: "UnifiedUEMCore"):
        self.core = core
        self.last_broadcast: Optional[BroadcastMessage] = None
    
    @property
    def subscriber_name(self) -> str:
        return "PlanningSubscriber"
    
    async def receive_broadcast(self, message: "BroadcastMessage") -> None:
        self.last_broadcast = message
        if message.content_type.name == "URGENCY":
            self.core.logger.info("[Planning] URGENCY received - priority boost")


# ============================================================================
# UNIFIED UEM CORE
# ============================================================================

class UnifiedUEMCore:
    """
    Unified UEM Core - All modules integrated.
    
    Integrates:
    - PerceptionCore
    - MemoryInterface v2
    - SelfCore
    - EmotionCore (Appraisal)
    - SomaticMarkerSystem
    - EmpathyOrchestrator
    - Planner v1
    - EthmorSystem
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        storage_type: str = "memory",
        world_interface: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        collect_metrics: bool = False,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config = config or {}
        self.tick: int = 0
        
        # IO / Infrastructure
        self.world_interface = world_interface
        self.event_bus = event_bus
        self.collect_metrics = collect_metrics
        self.logger = logger or logging.getLogger("UEM.Core")
        
        # Initialize core systems
        self._init_perception()
        self._init_memory(storage_type)
        self._init_self()
        self._init_emotion()
        self._init_somatic()
        self._init_empathy()
        self._init_ethmor()
        self._init_planner()
        self._init_workspace()
        
        # Runtime state
        self.current_emotion: Dict[str, float] = {
            "valence": 0.0,
            "arousal": 0.5,
            "dominance": 0.0,
        }
        self.last_action: Optional[ActionPlan] = None
        self.last_result: Optional[ActionResult] = None
        self.last_metrics: Optional[CycleMetrics] = None
        self.metrics_history: List[CycleMetrics] = []  # Sprint 0C: son 100 cycle
        

        # Logger Integration (Phase E)
        self.log_integration = None
        self._run_id: Optional[str] = None
        self._logging_active: bool = False
        if LOGGER_INTEGRATION_AVAILABLE:
            self.log_integration = CoreLoggerIntegration(enabled=True)
            self.logger.debug("[UnifiedCore] LoggerIntegration loaded")


        # PreData Calculators (Phase 1 Integration)
        self._emotion_predata = None
        self._planner_predata = None
        self._perception_predata = None
        self._self_predata = None
        self._current_predata: Dict[str, Any] = {}
        
        if PREDATA_CALCULATORS_AVAILABLE:
            self._emotion_predata = EmotionPreDataCalculator()
            self._planner_predata = PlannerPreDataCalculator()
            self._perception_predata = PerceptionPreDataCalculator()
            self._self_predata = SelfPreDataCalculator()
            self.logger.debug("[UnifiedCore] PreData calculators loaded")
        
        # Data Quality analyzers
        self._modality_detector = None
        self._noise_estimator = None
        self._trust_scorer = None
        self._quality_flagger = None
        self._language_detector = None
        
        if DATA_QUALITY_AVAILABLE:
            self._modality_detector = ModalityDetector()
            self._noise_estimator = NoiseEstimator()
            self._trust_scorer = TrustScorer()
            self._quality_flagger = QualityFlagger()
            self._language_detector = LanguageDetector()
            self.logger.debug("[UnifiedCore] Data Quality analyzers loaded")
        
        # Session tracking
        self._session_stage = None
        self._goal_clarity = None
        self._interaction_mode = None
        self._engagement_tracker = None
        self._experiment_manager = None
        
        if SESSION_AVAILABLE:
            self._session_stage = SessionStageDetector()
            self._goal_clarity = GoalClarityScorer()
            self._interaction_mode = InteractionModeClassifier()
            self._engagement_tracker = EngagementTracker()
            self._experiment_manager = ExperimentManager()
            self.logger.debug("[UnifiedCore] Session tracking loaded")
        
        # Tooling/Environment
        self._tool_tracker = None
        self._env_profiler = None
        self._policy_manager = None
        self._adversarial_detector = None
        
        if TOOLING_AVAILABLE:
            self._tool_tracker = ToolTracker()
            self._env_profiler = EnvironmentProfiler()
            self._policy_manager = PolicyManager()
            self._adversarial_detector = AdversarialDetector()
            self.logger.debug("[UnifiedCore] Tooling modules loaded")
        
        # Multi-Agent
        self._ma_coordinator = None
        if MULTI_AGENT_AVAILABLE:
            self._ma_coordinator = MultiAgentCoordinator()
            self.logger.debug("[UnifiedCore] Multi-Agent coordinator loaded")
        
        # MetaMind (scoring, pattern, alerts)
        self._coherence_scorer = None
        self._efficiency_scorer = None
        self._quality_scorer = None
        self._trust_aggregator = None
        self._failure_tracker = None
        self._action_analyzer = None
        self._valence_trend = None
        self._arousal_trend = None
        self._alert_manager = None
        self._behavior_clusterer = None
        self._metamind_summary: Dict[str, Any] = {}
        
        if METAMIND_AVAILABLE:
            self._coherence_scorer = CoherenceScorer()
            self._efficiency_scorer = EfficiencyScorer()
            self._quality_scorer = QualityScorer()
            self._trust_aggregator = TrustAggregator()
            self._failure_tracker = FailureTracker()
            self._action_analyzer = ActionAnalyzer()
            self._valence_trend = TrendAnalyzer()
            self._arousal_trend = TrendAnalyzer()
            self._alert_manager = AlertManager()
            self._behavior_clusterer = BehaviorClusterer()
            self.logger.debug("[UnifiedCore] MetaMind modules loaded")
        
        self.logger.info("[UnifiedCore] Initialized successfully")
    
    # ========================================================================
    # LOGGING CONTROL
    # ========================================================================
    
    async def start_logging(self, run_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Start DB logging for this session."""
        if self.log_integration is None:
            return None
        
        self._run_id = await self.log_integration.start(run_config)
        self._logging_active = self._run_id is not None
        if self._logging_active:
            self.logger.info(f"[UnifiedCore] DB logging started: {self._run_id}")
        return self._run_id
    
    async def stop_logging(self, summary: Optional[Dict[str, Any]] = None) -> None:
        """Stop DB logging."""
        if self.log_integration and self._logging_active:
            await self.log_integration.stop(summary)
            self.logger.info(f"[UnifiedCore] DB logging stopped: {self._run_id}")
            self._logging_active = False
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    def _init_perception(self) -> None:
        if PERCEPTION_AVAILABLE:
            self.perception = PerceptionCore(config={}, world_interface=None)
            self.logger.debug("[UnifiedCore] PerceptionCore loaded")
        else:
            self.perception = None
            self.logger.warning("[UnifiedCore] PerceptionCore not available")
    
    def _init_memory(self, storage_type: str) -> None:
        if MEMORY_AVAILABLE:
            self.memory = create_memory_interface(storage_type=storage_type)
            self.logger.debug(f"[UnifiedCore] MemoryInterface loaded ({storage_type})")
        else:
            self.memory = None
            self.logger.warning("[UnifiedCore] MemoryInterface not available")
    
    def _init_self(self) -> None:
        if SELF_AVAILABLE:
            self.self_core = SelfCore(
                memory_system=self.memory,
                emotion_system=self,  # We provide valence property
            )
            self.logger.debug("[UnifiedCore] SelfCore loaded")
        else:
            self.self_core = None
            self.logger.warning("[UnifiedCore] SelfCore not available")
    
    def _init_emotion(self) -> None:
        if EMOTION_AVAILABLE:
            self.emotion_core = EmotionCore(event_bus=self.event_bus)
            self.logger.debug("[UnifiedCore] EmotionCore loaded")
        else:
            self.emotion_core = None
            self.logger.warning("[UnifiedCore] EmotionCore not available")
    
    def _init_somatic(self) -> None:
        if SOMATIC_AVAILABLE:
            self.somatic_system = SomaticMarkerSystem()
            self.logger.debug("[UnifiedCore] SomaticMarkerSystem loaded")
        else:
            self.somatic_system = None
            self.logger.warning("[UnifiedCore] SomaticMarkerSystem not available")
    
    def _init_empathy(self) -> None:
        if EMPATHY_AVAILABLE:
            self.empathy = EmpathyOrchestrator(
                memory_interface=self.memory,
                emotion_system=self,  # We provide valence property
            )
            self.logger.debug("[UnifiedCore] EmpathyOrchestrator loaded")
        else:
            self.empathy = None
            self.logger.warning("[UnifiedCore] EmpathyOrchestrator not available")
    
    def _init_ethmor(self) -> None:
        if ETHMOR_AVAILABLE:
            self.ethmor = EthmorSystem()
            self.logger.debug("[UnifiedCore] EthmorSystem loaded")
        else:
            self.ethmor = None
            self.logger.warning("[UnifiedCore] EthmorSystem not available")
    
    def _init_planner(self) -> None:
        self.planner = PlannerV2(
            ethmor_system=self.ethmor,
            logger=self.logger.getChild("Planner"),
        )

    def _init_workspace(self) -> None:
        """Initialize GlobalWorkspace (Sprint 0B)."""
        if CONSCIOUSNESS_AVAILABLE:
            self.workspace_manager = create_workspace_manager(
                logger=self.logger.getChild("Workspace"),
            )
            self._perception_subscriber = PerceptionSubscriber(self)
            self._memory_subscriber = MemorySubscriber(self)
            self._planning_subscriber = PlanningSubscriber(self)
            self.workspace_manager.register_subscriber(self._perception_subscriber)
            self.workspace_manager.register_subscriber(self._memory_subscriber)
            self.workspace_manager.register_subscriber(self._planning_subscriber)
            self._last_conscious = None
            self.logger.debug("[UnifiedCore] WorkspaceManager loaded with 3 subscribers")
        else:
            self.workspace_manager = None
            self._last_conscious = None
            self.logger.warning("[UnifiedCore] WorkspaceManager not available")
        self.logger.debug("[UnifiedCore] Planner loaded")
    
    # ========================================================================
    # PROPERTIES (for module compatibility)
    # ========================================================================
    
    @property
    def valence(self) -> float:
        """For EmpathyOrchestrator and SelfCore compatibility."""
        return self.current_emotion.get("valence", 0.0)
    
    @property
    def arousal(self) -> float:
        """For module compatibility."""
        return self.current_emotion.get("arousal", 0.5)

    def get_conscious_content(self):
        """Get the last conscious broadcast (Sprint 0B API)."""
        return getattr(self, "_last_conscious", None)

    def get_metrics_summary(self, last_n: int = 10) -> Dict[str, Any]:
        """Get summary of recent metrics (Sprint 0C API for MetaMind)."""
        if not self.metrics_history:
            return {"error": "No metrics collected"}
        
        recent = self.metrics_history[-last_n:]
        
        success_count = sum(1 for m in recent if m.action_success)
        avg_time = sum(m.total_time_ms for m in recent) / len(recent)
        avg_valence = sum(m.emotion_valence for m in recent) / len(recent)
        avg_arousal = sum(m.emotion_arousal for m in recent) / len(recent)
        
        action_dist = {}
        for m in recent:
            if m.action_taken:
                action_dist[m.action_taken] = action_dist.get(m.action_taken, 0) + 1
        
        conscious_dist = {}
        for m in recent:
            if m.conscious_type:
                conscious_dist[m.conscious_type] = conscious_dist.get(m.conscious_type, 0) + 1
        
        return {
            "total_cycles": len(recent),
            "success_rate": success_count / len(recent) if recent else 0,
            "avg_cycle_time_ms": avg_time,
            "avg_valence": avg_valence,
            "avg_arousal": avg_arousal,
            "action_distribution": action_dist,
            "conscious_distribution": conscious_dist,
        }
    
    # ========================================================================
    # MAIN COGNITIVE CYCLE
    # ========================================================================
    
    async def cycle(self, world_state: WorldState) -> ActionResult:
        """
        Execute one cognitive cycle (Phase 1-9).
        
        Args:
            world_state: Current world state
            
        Returns:
            ActionResult with outcome
        """
        self.tick += 1
        
        # Reset PreData for new cycle
        self._current_predata = {}
        
        # Logger Integration: cycle start
        if self.log_integration:
            self.log_integration.on_cycle_start(tick=self.tick, cycle_id=self.tick)
            # Start cycle in DB (required for foreign key)
            if self._logging_active:
                try:
                    await self.log_integration.logger.start_cycle(
                        self._run_id, cycle_id=self.tick, tick=self.tick
                    )
                except Exception:
                    pass
        start = time.perf_counter()
        phase_times: Dict[str, float] = {}
        
        try:
            # Phase 1: PERCEPTION
            t0 = time.perf_counter()
            perception_result = self._phase_perception(world_state)
            
            # PreData: perception
            perception_predata = {}
            if self._perception_predata is not None:
                perception_predata = self._perception_predata.compute(
                    objects=getattr(world_state, 'objects', []),
                    agents=getattr(world_state, 'agents', []),
                    danger_level=getattr(world_state, 'danger_level', 0.0),
                    symbols=getattr(world_state, 'symbols', []),
                )
                self._current_predata.update(perception_predata)
            
            # Data Quality: compute input quality metrics
            dq_predata = {}
            if DATA_QUALITY_AVAILABLE and self._modality_detector is not None:
                try:
                    # Build input data representation
                    input_data = {
                        'objects': getattr(world_state, 'objects', []),
                        'agents': getattr(world_state, 'agents', []),
                        'symbols': getattr(world_state, 'symbols', []),
                        'events': getattr(world_state, 'events', []),
                    }
                    
                    # Extract text for language detection
                    text_content = ' '.join(getattr(world_state, 'symbols', []) or [])
                    
                    # Detect language (may return tuple or string)
                    lang_result = self._language_detector.detect(text_content) if text_content else 'unknown'
                    if isinstance(lang_result, tuple):
                        lang_result = lang_result[0]  # Extract language code from tuple
                    
                    # Compute Data Quality fields
                    dq_predata = {
                        'input_modality_mix': self._modality_detector.detect(input_data),
                        'input_noise_level': self._noise_estimator.estimate(input_data),
                        'source_trust_score': self._trust_scorer.score(input_data, source='world_state'),
                        'data_quality_flags': self._quality_flagger.check(input_data),
                        'input_language': lang_result,
                    }
                    self._current_predata.update(dq_predata)
                except Exception as e:
                    self.logger.debug(f"[DataQuality] Skipped: {e}")
            
            # Logger Integration: perception
            if self.log_integration:
                self.log_integration.on_perception(
                    novelty_score=perception_predata.get('novelty_score'),
                    attention_focus=perception_predata.get('attention_focus'),
                )
            phase_times["perception"] = (time.perf_counter() - t0) * 1000

            # Phase 2: WORKSPACE (Sprint 0B - conscious broadcast)
            t0 = time.perf_counter()
            conscious_message = await self._phase_workspace(perception_result, world_state)
            
            # PreData: workspace
            if conscious_message is not None and PREDATA_CALCULATORS_AVAILABLE:
                coalition_strength = conscious_message.coalition.activation if conscious_message.coalition else 0.0
                competition_intensity = WorkspacePreDataCalculator.compute_competition_intensity(
                    winner_activation=coalition_strength,
                    total_activation=coalition_strength * 1.2,  # Approximate
                    coalition_count=1,
                )
                workspace_predata = {
                    'coalition_strength': coalition_strength,
                    'competition_intensity': competition_intensity,
                    'conscious_threshold': getattr(self.workspace_manager, 'threshold', 0.4),
                    'broadcast_content': conscious_message.content_type.name if conscious_message else None,
                }
                self._current_predata.update(workspace_predata)
            phase_times["workspace"] = (time.perf_counter() - t0) * 1000

            
            # Phase 3: MEMORY
            t0 = time.perf_counter()
            memory_context = self._phase_memory(perception_result)
            
            # PreData: memory
            if PREDATA_CALCULATORS_AVAILABLE:
                retrieval_count = len(memory_context.similar_experiences) + len(memory_context.recent_events)
                similarity_scores = [exp.get('similarity', 0.5) for exp in memory_context.similar_experiences] if memory_context.similar_experiences else []
                memory_predata = {
                    'retrieval_count': retrieval_count,
                    'memory_relevance': MemoryPreDataCalculator.compute_memory_relevance(similarity_scores),
                    'working_memory_load': MemoryPreDataCalculator.compute_working_memory_load(retrieval_count),
                }
                self._current_predata.update(memory_predata)
            phase_times["memory"] = (time.perf_counter() - t0) * 1000
            
            # Phase 4: SELF
            t0 = time.perf_counter()
            self_state = self._phase_self(perception_result, memory_context, world_state)
            
            # PreData: self
            if self._self_predata is not None:
                confidence = self._self_predata.compute_confidence_score()
                self_predata = {
                    'confidence_score': confidence,
                    'resource_usage': SelfPreDataCalculator.compute_resource_usage(
                        cpu_time_ms=phase_times.get("perception", 0) + phase_times.get("memory", 0),
                    ),
                }
                self._current_predata.update(self_predata)
            phase_times["self"] = (time.perf_counter() - t0) * 1000
            
            # Phase 5: APPRAISAL
            t0 = time.perf_counter()
            appraisal_result = self._phase_appraisal(perception_result, self_state, world_state)
            
            # PreData: emotion
            emotion_predata = {}
            if self._emotion_predata is not None:
                emotion_predata = self._emotion_predata.compute(
                    valence=appraisal_result.valence,
                    arousal=appraisal_result.arousal,
                )
                self._current_predata.update(emotion_predata)
            
            # Logger Integration: emotion
            if self.log_integration:
                self.log_integration.on_emotion(
                    valence=appraisal_result.valence,
                    arousal=appraisal_result.arousal,
                    label=appraisal_result.emotion_label,
                    valence_delta=emotion_predata.get('valence_delta'),
                    mood_baseline=emotion_predata.get('mood_baseline'),
                )
            phase_times["appraisal"] = (time.perf_counter() - t0) * 1000
            
            # Phase 6: EMPATHY
            t0 = time.perf_counter()
            empathy_result = self._phase_empathy(perception_result, world_state)
            phase_times["empathy"] = (time.perf_counter() - t0) * 1000
            
            # Phase 7: PLANNING (includes ETHMOR check)
            t0 = time.perf_counter()
            action_plan = self._phase_planning(
                self_state, appraisal_result, perception_result, empathy_result
            )
            
            # PreData: planning
            planning_predata = {}
            if self._planner_predata is not None:
                self._planner_predata.reset()
                # Add selected action as candidate
                self._planner_predata.add_candidate(
                    action_plan.action,
                    action_plan.utility,
                    action_plan.reasoning[0] if action_plan.reasoning else "",
                )
                planning_predata = self._planner_predata.get_predata()
                self._current_predata.update(planning_predata)
            
            # PreData: ETHMOR (from action_plan metadata)
            ethmor_predata = {
                'ethmor_decision': getattr(action_plan, 'ethmor_decision', 'ALLOW'),
                'triggered_rules': getattr(action_plan, 'triggered_rules', []),
                'risk_level': getattr(action_plan, 'risk_level', 0.0),
                'intervention_type': getattr(action_plan, 'intervention_type', None),
                'ethical_confidence': getattr(action_plan, 'ethical_confidence', 1.0),
            }
            self._current_predata.update(ethmor_predata)
            
            # Logger Integration: planning
            if self.log_integration:
                self.log_integration.on_planning(
                    action=action_plan.action,
                    utility=action_plan.utility,
                    candidates=planning_predata.get('candidate_plans'),
                    utility_breakdown=planning_predata.get('utility_breakdown'),
                )
                # Logger Integration: ethmor
                self.log_integration.on_ethmor(
                    decision=ethmor_predata['ethmor_decision'],
                    triggered_rules=ethmor_predata['triggered_rules'],
                    risk_level=ethmor_predata['risk_level'],
                    ethical_confidence=ethmor_predata['ethical_confidence'],
                )
            phase_times["planning"] = (time.perf_counter() - t0) * 1000
            
            # Phase 8: EXECUTION
            t0 = time.perf_counter()
            action_result = await self._phase_execution(action_plan)
            
            # Logger Integration: cycle end + DB write
            if self.log_integration and self._logging_active:
                try:
                    # Write PreData event to DB (serialize payload)
                    import json
                    def serialize_predata(obj):
                        """Convert non-JSON-serializable objects."""
                        if hasattr(obj, 'to_dict'):
                            return obj.to_dict()
                        elif hasattr(obj, '__dict__'):
                            return obj.__dict__
                        elif hasattr(obj, 'value'):
                            return obj.value
                        return str(obj)
                    
                    serializable_predata = {}
                    for k, v in self._current_predata.items():
                        try:
                            json.dumps(v)
                            serializable_predata[k] = v
                        except (TypeError, ValueError):
                            serializable_predata[k] = serialize_predata(v)
                    
                    await self.log_integration.logger.log_event(
                        run_id=self._run_id,
                        cycle_id=self.tick,
                        module_name="predata",
                        event_type="cycle_predata",
                        payload=serializable_predata,
                        emotion_valence=appraisal_result.valence if appraisal_result else None,
                        action_name=action_plan.action if action_plan else None,
                        ethmor_decision=self._current_predata.get('ethmor_decision'),
                        success_flag_explicit=action_result.success,
                        cycle_time_ms=sum(phase_times.values()),
                        input_quality_score=self._current_predata.get('input_quality_score'),
                        input_language=self._current_predata.get('input_language'),
                        output_language=self._current_predata.get('output_language'),
                    )
                    
                    # Write MetaMind summary to DB
                    if self._metamind_summary:
                        await self.log_integration.logger.log_event(
                            run_id=self._run_id,
                            cycle_id=self.tick,
                            module_name="metamind",
                            event_type="cycle_summary",
                            payload=self._metamind_summary,
                        )
                    
                    # End cycle in logger
                    await self.log_integration.on_cycle_end(success=action_result.success)
                except Exception as e:
                    self.logger.debug(f"[DBWrite] Error: {e}")
            phase_times["execution"] = (time.perf_counter() - t0) * 1000
            
            # Phase 9: LEARNING
            t0 = time.perf_counter()
            await self._phase_learning(self_state, action_plan, action_result)
            
            # PreData: record outcome for self confidence
            if self._self_predata is not None:
                self._self_predata.record_outcome(
                    success=action_result.success,
                    prediction_error=abs(action_result.outcome_valence - action_plan.utility) if action_plan else 0.0,
                )
            
            # PreData: ltm_write_count (memory stored in learning phase)
            ltm_write_count = 1 if action_result.success else 0  # Simplified: 1 event per cycle
            self._current_predata['ltm_write_count'] = ltm_write_count
            
            # Session PreData
            if SESSION_AVAILABLE and self._session_stage is not None:
                try:
                    session_predata = {
                        'session_stage': self._session_stage.get_stage(self.tick),
                        'user_goal_clarity': self._goal_clarity.get_average() if self._goal_clarity else None,
                        'interaction_mode': self._interaction_mode.get_dominant_mode() if self._interaction_mode else None,
                        'user_engagement_level': self._engagement_tracker.current_level() if self._engagement_tracker else None,
                        'experiment_tag': None,  # Set externally
                        'ab_bucket': None,  # Set externally
                    }
                    self._current_predata.update(session_predata)
                except Exception:
                    pass
            
            # Tooling PreData
            if TOOLING_AVAILABLE and self._tool_tracker is not None:
                try:
                    tooling_predata = {
                        'tool_usage_summary': self._tool_tracker.get_summary() if self._tool_tracker else None,
                        'environment_profile': self._env_profiler.to_dict() if self._env_profiler else None,
                        'policy_set_id': self._policy_manager.current_policy_set if self._policy_manager else None,
                        'policy_conflict_score': 0.0,
                        'adversarial_input_score': self._adversarial_detector.get_score(str(world_state)) if self._adversarial_detector else 0.0,
                    }
                    self._current_predata.update(tooling_predata)
                except Exception:
                    pass
            
            # Multi-Agent PreData (v1.0 - Real Calculations)
            try:
                # Get entities from perception if available
                other_entities = getattr(perception_result, "entities", []) if perception_result else []
                empathy_results = getattr(self, "_empathy_results", []) or []
                
                ma_fields = calculate_all_multiagent_fields(
                    other_entities=other_entities,
                    empathy_results=empathy_results,
                    goal_overlap=0.0  # V1.0: placeholder
                )
                self._current_predata.update({
                    "empathy_score": ma_fields["empathy_score"],
                    "ma_agent_count": ma_fields["ma_agent_count"],
                    "ma_coordination_mode": ma_fields["ma_coordination_mode"],
                    "ma_conflict_score": ma_fields["ma_conflict_score"],
                })
            except Exception:
                # Fallback to defaults
                self._current_predata.update({
                    "empathy_score": 0.0,
                    "ma_agent_count": 1,
                    "ma_coordination_mode": "single",
                    "ma_conflict_score": 0.0,
                })
            
            # === MetaMind Analysis ===
            if METAMIND_AVAILABLE and self._coherence_scorer is not None:
                try:
                    # Prepare data for MetaMind
                    cycle_data = {
                        'valence': appraisal_result.valence if appraisal_result else 0.0,
                        'arousal': appraisal_result.arousal if appraisal_result else 0.0,
                        'action': action_plan.action if action_plan else None,
                        'success': action_result.success if action_result else False,
                        'utility': action_plan.utility if action_plan else 0.0,
                        'cycle_time_ms': sum(phase_times.values()),
                        **self._current_predata,
                    }
                    
                    # Scoring (use compute method)
                    coherence = self._coherence_scorer.compute(cycle_data) if hasattr(self._coherence_scorer, 'compute') else 0.5
                    efficiency = self._efficiency_scorer.compute(cycle_data) if hasattr(self._efficiency_scorer, 'compute') else 0.5
                    quality = self._quality_scorer.compute(cycle_data) if hasattr(self._quality_scorer, 'compute') else 0.5
                    trust = self._trust_aggregator.compute(cycle_data) if hasattr(self._trust_aggregator, 'compute') else 0.5
                    
                    # Pattern tracking
                    self._failure_tracker.record(action_result.success if action_result else False)
                    self._action_analyzer.record(action_plan.action if action_plan else 'none')
                    self._valence_trend.add(appraisal_result.valence if appraisal_result else 0.0)
                    self._arousal_trend.add(appraisal_result.arousal if appraisal_result else 0.0)
                    
                    # Get derived metrics
                    failure_streak = self._failure_tracker.current_streak
                    action_diversity = self._action_analyzer.get_diversity_score()
                    valence_trend = self._valence_trend.get_trend_value()
                    arousal_trend = self._arousal_trend.get_trend_value()
                    
                    # Clustering (every 10 cycles)
                    cluster_id = None
                    if self.tick % 10 == 0:
                        cluster_id = self._behavior_clusterer.assign_cluster(cycle_data)
                    
                    # Alerts
                    alerts = self._alert_manager.check(cycle_data, cycle_id=self.tick)
                    
                    # Store MetaMind summary
                    self._metamind_summary = {
                        'coherence_score': coherence,
                        'efficiency_score': efficiency,
                        'outcome_quality_score': quality,
                        'trust_score_avg': trust,
                        'failure_streak': failure_streak,
                        'action_diversity_score': action_diversity,
                        'valence_trend': valence_trend,
                        'arousal_trend': arousal_trend,
                        'behavior_cluster_id': cluster_id,
                        'alert_count': len(alerts),
                    }
                    
                except Exception as e:
                    self.logger.debug(f"[MetaMind] Error: {e}")
            
            # === Remaining 6 PreData Fields ===
            
            # 1. output_language (same as input for now)
            self._current_predata['output_language'] = self._current_predata.get('input_language', 'unknown')
            
            # 2. primary_language (run-level, but tracked per cycle)
            self._current_predata['primary_language'] = self._current_predata.get('input_language', 'unknown')
            
            # 3. cycle_complexity (based on phase count and processing)
            cycle_complexity = {
                'phase_count': len(phase_times),
                'total_time_ms': sum(phase_times.values()),
                'memory_retrievals': self._current_predata.get('retrieval_count', 0),
                'has_empathy': hasattr(self, '_empathy_active') and self._empathy_active,
                'coalition_formed': self._current_predata.get('coalition_strength', 0) > 0.3,
            }
            self._current_predata['cycle_complexity'] = cycle_complexity
            
            # 4. decision_trace (action selection reasoning)
            decision_trace = {
                'selected_action': action_plan.action if action_plan else None,
                'utility': action_plan.utility if action_plan else 0.0,
                'alternatives_count': len(self._current_predata.get('candidate_plans', [])),
                'ethmor_decision': self._current_predata.get('ethmor_decision', 'ALLOW'),
                'somatic_bias': self._current_predata.get('somatic_bias', 0.0),
            }
            self._current_predata['decision_trace'] = decision_trace
            
            # 5. input_quality_score (derived from DQ fields)
            noise = self._current_predata.get('input_noise_level', 0.0)
            trust = self._current_predata.get('source_trust_score', 1.0)
            flags = self._current_predata.get('data_quality_flags', [])
            flag_penalty = len([f for f in flags if f != 'clean']) * 0.1
            input_quality_score = max(0.0, min(1.0, (1.0 - noise) * trust - flag_penalty))
            self._current_predata['input_quality_score'] = round(input_quality_score, 3)
            
            # 6. empathy_score (placeholder - 0.5 default, will be computed by empathy module)
            self._current_predata['empathy_score'] = getattr(self, '_last_empathy_score', 0.5)
            
            phase_times["learning"] = (time.perf_counter() - t0) * 1000
            
        except Exception as e:
            self.logger.error(f"[Cycle {self.tick}] Exception: {e}", exc_info=True)
            action_result = ActionResult(
                action_name="wait",
                target=None,
                success=False,
                outcome_type="error_fallback",
                outcome_valence=-0.1,
                actual_effect=(0.0, 0.0, 0.0),
                reasoning=["error_fallback"],
            )
        
        # Metrics (Sprint 0C: extended)
        total_ms = (time.perf_counter() - start) * 1000
        if self.collect_metrics:
            conscious_type = None
            conscious_activation = None
            if self._last_conscious:
                conscious_type = self._last_conscious.content_type.name
                conscious_activation = self._last_conscious.coalition.activation
            
            self.last_metrics = CycleMetrics(
                tick=self.tick,
                total_time_ms=total_ms,
                phase_times=phase_times,
                action_taken=action_result.action_name,
                action_success=action_result.success,
                emotion_valence=self.current_emotion.get("valence", 0.0),
                emotion_arousal=self.current_emotion.get("arousal", 0.5),
                emotion_label=self.current_emotion.get("label", "neutral"),
                conscious_type=conscious_type,
                conscious_activation=conscious_activation,
            )
            # Sprint 0C: History
            self.metrics_history.append(self.last_metrics)
            if len(self.metrics_history) > 100:
                self.metrics_history.pop(0)
        
        self.last_result = action_result
        
        # Event publishing
        if self.event_bus:
            try:
                await self.event_bus.publish("cycle.completed", {
                    "tick": self.tick,
                    "action": action_result.action_name,
                    "success": action_result.success,
                })
            except Exception as e:
                self.logger.warning(f"[Cycle {self.tick}] Event publish failed: {e}")
        
        self.logger.info(
            f"[Cycle {self.tick}] Completed: {action_result.action_name} "
            f"({total_ms:.1f}ms)"
        )
        
        return action_result
    
    def cycle_sync(self, world_state: WorldState) -> ActionResult:
        """Synchronous wrapper for cycle()."""
        return asyncio.run(self.cycle(world_state))
    
    # ========================================================================
    # PHASE IMPLEMENTATIONS
    # ========================================================================

    async def _phase_workspace(self, perception_result, world_state):
        """Phase 2: GlobalWorkspace - conscious broadcast (Sprint 0B)."""
        self.logger.debug(f"[Cycle {self.tick}] Phase: workspace")
        if self.workspace_manager is None:
            return None
        try:
            workspace_context = {
                "perception": {
                    "danger_level": getattr(world_state, "danger_level", 0.0),
                    "symbols": getattr(world_state, "symbols", []),
                    "objects": getattr(world_state, "objects", []),
                },
                "emotion": self.current_emotion,
                "agent_state": {
                    "health": getattr(world_state, "player_health", 1.0),
                    "energy": getattr(world_state, "player_energy", 1.0),
                },
                "active_goals": [],
            }
            message = await self.workspace_manager.cycle(workspace_context)
            self._last_conscious = message
            if message:
                self.logger.debug(f"[Workspace] Broadcast: {message.content_type.name} (activation={message.coalition.activation:.2f})")
            return message
        except Exception as e:
            self.logger.warning(f"[Workspace] Failed: {e}")
            return None

    
    def _phase_perception(self, world_state: WorldState) -> Any:
        """Phase 1: Process world state through perception."""
        self.logger.debug(f"[Cycle {self.tick}] Phase: perception")
        
        if self.perception is not None:
            try:
                return self.perception.process(world_state)
            except Exception as e:
                self.logger.warning(f"[Perception] Failed: {e}")
        
        # Fallback: return world_state as-is
        return world_state
    
    def _phase_memory(self, perception_result: Any) -> MemoryContext:
        """Phase 2: Retrieve relevant memories."""
        self.logger.debug(f"[Cycle {self.tick}] Phase: memory")
        
        similar_experiences = []
        recent_events = []
        
        if self.memory is not None:
            try:
                # Get current state vector for similarity search
                state_vec = None
                if self.self_core is not None:
                    state_vec = self.self_core.get_state_vector()
                
                if state_vec is not None:
                    similar_experiences = self.memory.get_similar_experiences(
                        state_vector=state_vec,
                        tolerance=0.3,
                        limit=10,
                    )
                
                recent_events = self.memory.get_recent_events(n=5)
            except Exception as e:
                self.logger.warning(f"[Memory] Retrieval failed: {e}")
        
        return MemoryContext(
            similar_experiences=similar_experiences,
            recent_events=recent_events,
        )
    
    def _phase_self(
        self,
        perception_result: Any,
        memory_context: MemoryContext,
        world_state: WorldState,
    ) -> SelfState:
        """Phase 3: Update self state."""
        self.logger.debug(f"[Cycle {self.tick}] Phase: self")
        
        state_vector = (0.5, 0.5, 0.5)  # Default
        state_delta = (0.0, 0.0, 0.0)
        goals = []
        
        if self.self_core is not None:
            try:
                # Build world snapshot dict
                world_snapshot = {
                    'player_health': getattr(world_state, 'player_health', 1.0),
                    'player_energy': getattr(world_state, 'player_energy', 1.0),
                    'danger_level': getattr(world_state, 'danger_level', 0.0),
                }
                
                self.self_core.update(dt=0.1, world_snapshot=world_snapshot)
                
                sv = self.self_core.get_state_vector()
                if sv is not None:
                    state_vector = sv
                
                sd = self.self_core.get_state_delta()
                if sd is not None:
                    state_delta = sd
                
                if hasattr(self.self_core, 'get_goals'):
                    goals = self.self_core.get_goals() or []
                    
            except Exception as e:
                self.logger.warning(f"[Self] Update failed: {e}")
        
        return SelfState(
            state_vector=state_vector,
            state_delta=state_delta,
            goals=goals,
        )
    
    def _phase_appraisal(
        self,
        perception_result: Any,
        self_state: SelfState,
        world_state: WorldState,
    ) -> AppraisalResult:
        """Phase 4: Emotional appraisal via EmotionCore."""
        self.logger.debug(f"[Cycle {self.tick}] Phase: appraisal")
        
        # Use EmotionCore.evaluate() if available
        if self.emotion_core is not None:
            try:
                result = self.emotion_core.evaluate(
                    world_snapshot=world_state,
                    state_vector=self_state.state_vector,
                )
                
                valence = result.get('valence', 0.0)
                arousal = result.get('arousal', 0.5)
                dominance = result.get('dominance', 0.0)
                emotion_label = result.get('emotion_label', 'neutral')
                
                self.current_emotion = {
                    "valence": valence,
                    "arousal": arousal,
                    "dominance": dominance,
                    "label": emotion_label,
                }
                
                return AppraisalResult(
                    valence=valence,
                    arousal=arousal,
                    dominance=dominance,
                    emotion_label=emotion_label,
                )
            except Exception as e:
                self.logger.warning(f"[Appraisal] EmotionCore.evaluate failed: {e}")
        
        # Fallback: inline appraisal (if EmotionCore unavailable)
        danger = getattr(world_state, 'danger_level', 0.0)
        health = getattr(world_state, 'player_health', 1.0)
        
        valence = -danger * 0.5 + (health - 0.5) * 0.3
        valence = max(-1.0, min(1.0, valence))
        
        arousal = 0.5 + danger * 0.4
        arousal = max(0.0, min(1.0, arousal))
        
        dominance = (health - danger) * 0.3
        dominance = max(-1.0, min(1.0, dominance))
        
        if valence < -0.3 and arousal > 0.6:
            emotion_label = "fear"
        elif valence < -0.3 and arousal < 0.4:
            emotion_label = "sadness"
        elif valence > 0.3 and arousal > 0.5:
            emotion_label = "excitement"
        elif valence > 0.3:
            emotion_label = "content"
        else:
            emotion_label = "neutral"
        
        self.current_emotion = {
            "valence": valence,
            "arousal": arousal,
            "label": emotion_label,
            "dominance": dominance,
        }
        
        return AppraisalResult(
            valence=valence,
            arousal=arousal,
            dominance=dominance,
            emotion_label=emotion_label,
        )


    def _phase_empathy(
        self,
        perception_result: Any,
        world_state: WorldState,
    ) -> Optional[Any]:
        """
        Phase 6: Empathy computation for ALL agents present.
        
        V1.1 Update (30 Kasım 2025):
        - Tüm ajanlar için empati hesapla
        - self._empathy_results listesine kaydet
        - İlk sonucu döndür (backward compatibility)
        """
        self.logger.debug(f"[Cycle {self.tick}] Phase: empathy")
        
        # Reset empathy results for this cycle
        self._empathy_results = []
        
        if self.empathy is None:
            return None
        
        # Check for agents from world_state or perception_result
        agents = getattr(world_state, 'agents', [])
        if not agents:
            # Try perception_result.entities
            agents = getattr(perception_result, 'entities', [])
        if not agents:
            # Try perception_result.agents
            agents = getattr(perception_result, 'agents', [])
        
        if not agents:
            return None
        
        first_result = None
        
        try:
            if EMPATHY_AVAILABLE:
                for idx, agent in enumerate(agents):
                    try:
                        # Build OtherEntity from agent data
                        if isinstance(agent, dict):
                            other_entity = OtherEntity(
                                entity_id=agent.get('id', f'agent_{idx}'),
                                state_vector=agent.get('state_vector', (0.5, 0.5, 0.5)),
                                valence=agent.get('valence', 0.0),
                                relationship=agent.get('relation', agent.get('relationship', 0.0)),
                            )
                        else:
                            # Agent is an object
                            other_entity = OtherEntity(
                                entity_id=getattr(agent, 'id', getattr(agent, 'entity_id', f'agent_{idx}')),
                                state_vector=getattr(agent, 'state_vector', (0.5, 0.5, 0.5)),
                                valence=getattr(agent, 'valence', 0.0),
                                relationship=getattr(agent, 'relation', getattr(agent, 'relationship', 0.0)),
                            )
                        
                        # Compute empathy for this agent
                        empathy_result = self.empathy.compute(other_entity)
                        self._empathy_results.append(empathy_result)
                        
                        if first_result is None:
                            first_result = empathy_result
                        
                        self.logger.debug(
                            f"[Empathy] Agent {other_entity.entity_id}: "
                            f"level={empathy_result.empathy_level:.2f}, "
                            f"resonance={empathy_result.resonance:.2f}"
                        )
                    except Exception as e:
                        self.logger.warning(f"[Empathy] Failed for agent {idx}: {e}")
                        continue
                
                self.logger.debug(f"[Empathy] Computed for {len(self._empathy_results)} agents")
        except Exception as e:
            self.logger.warning(f"[Empathy] Failed: {e}")
        
        return first_result
    
    def _phase_planning(
        self,
        self_state: SelfState,
        appraisal_result: AppraisalResult,
        perception_result: Any,
        empathy_result: Optional[Any],
    ) -> ActionPlan:
        """Phase 6: Planning (includes ETHMOR check)."""
        self.logger.debug(f"[Cycle {self.tick}] Phase: planning")
        
        # Build world snapshot for planner
        world_snapshot = perception_result
        if hasattr(perception_result, 'snapshot'):
            world_snapshot = perception_result.snapshot
        
        # Build planning context
        context = PlanningContext(
            state_vector=self_state.state_vector,
            goals=self_state.goals,
            appraisal_result=appraisal_result,
            somatic_markers=self.somatic_system,
            world_snapshot=world_snapshot,
            available_actions=["flee", "approach", "help", "attack", "explore", "wait"],
            empathy_result=empathy_result,
        )
        
        # Execute planning pipeline
        action_plan = self.planner.plan(context)
        self.last_action = action_plan
        
        self.logger.info(
            f"[Cycle {self.tick}] Action: {action_plan.action} "
            f"(util={action_plan.utility:.3f}, conf={action_plan.confidence:.2f})"
        )
        
        return action_plan
    
    async def _phase_execution(self, action_plan: ActionPlan) -> ActionResult:
        """Phase 7: Execute action."""
        self.logger.debug(f"[Cycle {self.tick}] Phase: execution")
        
        if self.world_interface is not None:
            try:
                outcome = await self.world_interface.execute(action_plan)
                if isinstance(outcome, ActionResult):
                    return outcome
                return ActionResult(**outcome)
            except Exception as e:
                self.logger.warning(f"[Execution] World interface failed: {e}")
        
        # Simulate outcome
        return self._simulate_outcome(action_plan)
    
    def _simulate_outcome(self, action: ActionPlan) -> ActionResult:
        """Simulate action outcome when no world interface."""
        # Simple simulation based on action type
        outcome_map = {
            "flee": ("escaped", 0.2),
            "approach": ("approached", 0.1),
            "help": ("helped", 0.3),
            "attack": ("attacked", -0.1),
            "explore": ("explored", 0.1),
            "wait": ("waited", 0.0),
        }
        
        outcome_type, outcome_valence = outcome_map.get(
            action.action, ("simulated", 0.0)
        )
        
        return ActionResult(
            action_name=action.action,
            target=action.target,
            success=True,
            outcome_type=outcome_type,
            outcome_valence=outcome_valence,
            actual_effect=action.predicted_effect,
            reasoning=action.reasoning,
        )
    
    async def _phase_learning(
        self,
        self_state: SelfState,
        action_plan: ActionPlan,
        action_result: ActionResult,
    ) -> None:
        """Phase 8: Learning (memory + somatic update)."""
        self.logger.debug(f"[Cycle {self.tick}] Phase: learning")
        
        # Store event in memory
        if self.memory is not None:
            try:
                event = {
                    "source": "SELF",
                    "action": action_result.action_name,
                    "target": action_result.target or "WORLD",
                    "effect": action_result.actual_effect,
                    "tick": self.tick,
                }
                self.memory.store_event(event)
                
                self.memory.store_state_snapshot({
                    "state_vector": self_state.state_vector,
                    "tick": self.tick,
                })
            except Exception as e:
                self.logger.warning(f"[Learning] Memory store failed: {e}")
        
        # Update somatic markers
        if self.somatic_system is not None:
            try:
                self.somatic_system.record_outcome(
                    action_name=action_result.action_name,
                    outcome_valence=action_result.outcome_valence,
                    outcome_description=action_result.outcome_type,
                )
            except Exception as e:
                self.logger.warning(f"[Learning] Somatic update failed: {e}")
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get core statistics."""
        stats = {
            "tick": self.tick,
            "current_emotion": self.current_emotion,
            "last_action": self.last_action.action if self.last_action else None,
        }
        
        if self.last_metrics:
            stats["last_metrics"] = self.last_metrics.to_dict()
        
        if self.planner:
            stats["planner"] = self.planner.get_stats()
        
        return stats
    
    def reset(self) -> None:
        """Reset core state."""
        self.tick = 0
        self.current_emotion = {"valence": 0.0, "arousal": 0.5, "dominance": 0.0, "label": "neutral"}
        self.last_action = None
        self.last_result = None
        self.last_metrics = None
        
        if self.planner:
            self.planner.reset_stats()
        
        self.logger.info("[UnifiedCore] Reset completed")


# ============================================================================
# FACTORY
# ============================================================================

def create_unified_core(
    storage_type: str = "memory",
    with_event_bus: bool = False,
    collect_metrics: bool = False,
    logger: Optional[logging.Logger] = None,
) -> UnifiedUEMCore:
    """Factory function to create UnifiedUEMCore."""
    event_bus = None  # TODO: Create event bus if with_event_bus
    
    return UnifiedUEMCore(
        storage_type=storage_type,
        event_bus=event_bus,
        collect_metrics=collect_metrics,
        logger=logger or logging.getLogger("UEM"),
    )

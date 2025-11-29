"""
Main PreData collector - aggregates data from all sources.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone


@dataclass
class PreData:
    """
    Complete PreData snapshot for a cognitive cycle.
    Contains all 51 fields organized by category.
    """
    # Metadata
    cycle_id: int
    tick: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # === CORE COGNITIVE (27 fields) ===
    # Planner
    utility_breakdown: Optional[Dict] = None
    candidate_plans: Optional[List] = None
    somatic_bias: Optional[float] = None
    
    # ETHMOR
    triggered_rules: Optional[List] = None
    risk_level: Optional[float] = None
    intervention_type: Optional[str] = None
    ethical_confidence: Optional[float] = None
    
    # Emotion
    engagement: Optional[float] = None
    valence_delta: Optional[float] = None
    arousal_volatility: Optional[float] = None
    emotion_label: Optional[str] = None
    mood_baseline: Optional[float] = None
    
    # Perception
    novelty_score: Optional[float] = None
    salience_map: Optional[Dict] = None
    temporal_context: Optional[Dict] = None
    attention_focus: Optional[str] = None
    perception_confidence: Optional[float] = None
    
    # Workspace
    coalition_strength: Optional[float] = None
    broadcast_content: Optional[Dict] = None
    competition_intensity: Optional[float] = None
    conscious_threshold: Optional[float] = None
    
    # Memory
    retrieval_count: Optional[int] = None
    memory_relevance: Optional[float] = None
    consolidation_flag: Optional[bool] = None
    
    # Self
    self_state_vector: Optional[Dict] = None
    goal_progress: Optional[Dict] = None
    introspection_depth: Optional[int] = None
    
    # === DATA QUALITY (6 fields) ===
    input_modality_mix: Optional[Dict] = None
    input_noise_level: Optional[float] = None
    source_trust_score: Optional[float] = None
    data_quality_flags: Optional[List] = None
    input_language: Optional[str] = None
    output_language: Optional[str] = None
    
    # === USER/SESSION (6 fields) ===
    session_stage: Optional[str] = None
    user_goal_clarity: Optional[float] = None
    interaction_mode: Optional[str] = None
    user_engagement_level: Optional[str] = None
    experiment_tag: Optional[str] = None
    ab_bucket: Optional[str] = None
    
    # === TOOLING/ENVIRONMENT (5 fields) ===
    tool_usage_summary: Optional[Dict] = None
    environment_profile: Optional[Dict] = None
    policy_set_id: Optional[str] = None
    policy_conflict_score: Optional[float] = None
    adversarial_input_score: Optional[float] = None
    
    # === MULTI-AGENT (3 fields - placeholder) ===
    ma_agent_count: Optional[int] = None
    ma_coordination_mode: Optional[str] = None
    ma_conflict_score: Optional[float] = None
    
    # === EXECUTION (4 fields) ===
    action_name: Optional[str] = None
    action_success: Optional[bool] = None
    cycle_time_ms: Optional[float] = None
    causal_factors: Optional[List] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in self.__dict__.items() if v is not None}
    
    def get_core_fields(self) -> Dict[str, Any]:
        """Get only core cognitive fields."""
        core_keys = [
            'utility_breakdown', 'candidate_plans', 'somatic_bias',
            'triggered_rules', 'risk_level', 'intervention_type', 'ethical_confidence',
            'engagement', 'valence_delta', 'arousal_volatility', 'emotion_label', 'mood_baseline',
            'novelty_score', 'salience_map', 'temporal_context', 'attention_focus', 'perception_confidence',
            'coalition_strength', 'broadcast_content', 'competition_intensity', 'conscious_threshold',
            'retrieval_count', 'memory_relevance', 'consolidation_flag',
            'self_state_vector', 'goal_progress', 'introspection_depth',
        ]
        return {k: getattr(self, k) for k in core_keys if getattr(self, k) is not None}


class PreDataCollector:
    """
    Collects and aggregates PreData from cognitive cycle phases.
    
    Usage:
        collector = PreDataCollector()
        collector.start_cycle(tick=1)
        collector.add_perception(novelty_score=0.7, ...)
        collector.add_emotion(valence=0.5, ...)
        predata = collector.finalize()
    """
    
    def __init__(self):
        self._current: Optional[PreData] = None
        self._cycle_count = 0
    
    def start_cycle(self, tick: int, cycle_id: Optional[int] = None) -> None:
        """Start collecting data for a new cycle."""
        self._cycle_count += 1
        self._current = PreData(
            cycle_id=cycle_id or self._cycle_count,
            tick=tick
        )
    
    def add_perception(self, **kwargs) -> None:
        """Add perception phase data."""
        if not self._current:
            return
        for key in ['novelty_score', 'salience_map', 'temporal_context', 
                    'attention_focus', 'perception_confidence']:
            if key in kwargs:
                setattr(self._current, key, kwargs[key])
    
    def add_emotion(self, **kwargs) -> None:
        """Add emotion phase data."""
        if not self._current:
            return
        for key in ['engagement', 'valence_delta', 'arousal_volatility',
                    'emotion_label', 'mood_baseline']:
            if key in kwargs:
                setattr(self._current, key, kwargs[key])
        # Also accept 'valence' as alias for emotion tracking
        if 'valence' in kwargs:
            self._current.valence_delta = kwargs.get('valence_delta', kwargs.get('valence'))
    
    def add_workspace(self, **kwargs) -> None:
        """Add workspace phase data."""
        if not self._current:
            return
        for key in ['coalition_strength', 'broadcast_content',
                    'competition_intensity', 'conscious_threshold']:
            if key in kwargs:
                setattr(self._current, key, kwargs[key])
    
    def add_planning(self, **kwargs) -> None:
        """Add planning phase data."""
        if not self._current:
            return
        for key in ['utility_breakdown', 'candidate_plans', 'somatic_bias', 'action_name']:
            if key in kwargs:
                setattr(self._current, key, kwargs[key])
        if 'action' in kwargs:
            self._current.action_name = kwargs['action']
        if 'utility' in kwargs and 'utility_breakdown' not in kwargs:
            self._current.utility_breakdown = {'total': kwargs['utility']}
    
    def add_ethmor(self, **kwargs) -> None:
        """Add ETHMOR phase data."""
        if not self._current:
            return
        for key in ['triggered_rules', 'risk_level', 'intervention_type', 'ethical_confidence']:
            if key in kwargs:
                setattr(self._current, key, kwargs[key])
        if 'decision' in kwargs:
            self._current.intervention_type = kwargs['decision']
    
    def add_memory(self, **kwargs) -> None:
        """Add memory phase data."""
        if not self._current:
            return
        for key in ['retrieval_count', 'memory_relevance', 'consolidation_flag']:
            if key in kwargs:
                setattr(self._current, key, kwargs[key])
    
    def add_self(self, **kwargs) -> None:
        """Add self phase data."""
        if not self._current:
            return
        for key in ['self_state_vector', 'goal_progress', 'introspection_depth']:
            if key in kwargs:
                setattr(self._current, key, kwargs[key])
    
    def add_execution(self, **kwargs) -> None:
        """Add execution phase data."""
        if not self._current:
            return
        for key in ['action_success', 'cycle_time_ms', 'causal_factors']:
            if key in kwargs:
                setattr(self._current, key, kwargs[key])
        if 'success' in kwargs:
            self._current.action_success = kwargs['success']
    
    def add_data_quality(self, **kwargs) -> None:
        """Add data quality fields."""
        if not self._current:
            return
        for key in ['input_modality_mix', 'input_noise_level', 'source_trust_score',
                    'data_quality_flags', 'input_language', 'output_language']:
            if key in kwargs:
                setattr(self._current, key, kwargs[key])
    
    def add_tooling(self, **kwargs) -> None:
        """Add tooling/environment fields."""
        if not self._current:
            return
        for key in ['tool_usage_summary', 'environment_profile', 'policy_set_id',
                    'policy_conflict_score', 'adversarial_input_score']:
            if key in kwargs:
                setattr(self._current, key, kwargs[key])
    
    def finalize(self) -> Optional[PreData]:
        """Finalize and return the collected PreData."""
        result = self._current
        self._current = None
        return result
    
    @property
    def current(self) -> Optional[PreData]:
        """Get current PreData being collected."""
        return self._current

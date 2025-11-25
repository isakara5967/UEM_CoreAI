# core/integrated_uem_core.py
"""
UEM Integrated Core - Global Workspace + SELF + ETHMOR Entegrasyonu

Cognitive Cycle with Ethical Filtering:
1. PERCEPTION: World state → Percepts
2. SELF UPDATE: World snapshot → StateVector, deltas
3. WORKSPACE: Coalition competition → Conscious broadcast
4. MEMORY: Broadcast + context → Memory retrieval
5. EMOTION: Appraisal + somatic markers
6. PLANNING: Propose candidate action + predict outcome
7. ETHMOR: Filter action (ALLOW/FLAG/BLOCK)
8. EXECUTION: Execute allowed action
9. LEARNING: Outcome → Memory consolidation + Event logging

Author: UEM Project
"""

from __future__ import annotations
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from enum import Enum
from collections import deque

from core.consciousness.global_workspace import (
    WorkspaceManager,
    WorkspaceSubscriber,
    BroadcastMessage,
    ContentType,
    create_workspace_manager,
)

# SELF ve ETHMOR imports
try:
    from core.self.self_core import SelfCore
    from core.ethmor import EthmorSystem, EthmorContext, ActionDecision
    from core.ontology.types import Event as OntologyEvent, Goal
    ONTOLOGY_AVAILABLE = True
except ImportError:
    ONTOLOGY_AVAILABLE = False
    SelfCore = None
    EthmorSystem = None


# =========================================================================
# ENUMS & DATA TYPES
# =========================================================================

class CognitivePhase(Enum):
    """Cognitive cycle phases - Extended"""
    PERCEPTION = "perception"
    SELF_UPDATE = "self_update"
    WORKSPACE = "workspace"
    MEMORY_RETRIEVAL = "memory_retrieval"
    EMOTION_APPRAISAL = "emotion_appraisal"
    PLANNING = "planning"
    ETHMOR_FILTER = "ethmor_filter"
    ACTION_SELECTION = "action_selection"
    EXECUTION = "execution"
    LEARNING = "learning"


@dataclass
class WorldState:
    """Dış dünyadan gelen durum"""
    tick: int = 0
    danger_level: float = 0.0
    objects: List[Dict[str, Any]] = field(default_factory=list)
    agents: List[Dict[str, Any]] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)
    player_position: tuple = (0, 0)
    player_health: float = 1.0
    player_energy: float = 1.0
    rewards_collected: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tick': self.tick,
            'danger_level': self.danger_level,
            'objects_count': len(self.objects),
            'agents_count': len(self.agents),
            'symbols': self.symbols,
            'player_position': self.player_position,
            'player_health': self.player_health,
            'player_energy': self.player_energy,
        }


@dataclass
class ActionCommand:
    """Seçilen eylem"""
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: float = 0.5
    somatic_bias: float = 0.0
    conscious_influence: float = 0.0
    predicted_effects: Dict[str, float] = field(default_factory=dict)
    ethmor_decision: str = "ALLOW"
    ethmor_violation_score: float = 0.0


@dataclass
class ActionResult:
    """Eylem sonucu"""
    action_name: str
    success: bool
    outcome_type: str = ""
    outcome_valence: float = 0.0
    conscious_content: str = ""
    ethmor_decision: str = "ALLOW"
    ethmor_violation_score: float = 0.0
    blocked: bool = False
    block_reason: str = ""


@dataclass
class CycleStats:
    """Cycle istatistikleri"""
    tick: int = 0
    phase_times: Dict[str, float] = field(default_factory=dict)
    total_time: float = 0.0
    broadcast_content: str = ""
    emotion_state: Dict[str, Any] = field(default_factory=dict)
    action_taken: str = ""
    memory_retrievals: int = 0
    somatic_influence: float = 0.0
    self_state_vector: Optional[tuple] = None
    ethmor_decision: str = "ALLOW"
    ethmor_violation_score: float = 0.0


# =========================================================================
# WORKSPACE SUBSCRIBERS
# =========================================================================

class MemorySubscriber(WorkspaceSubscriber):
    """Memory modülü için workspace subscriber"""
    
    def __init__(self, core: "IntegratedUEMCore"):
        self.core = core
        self.last_broadcast: Optional[BroadcastMessage] = None
    
    @property
    def subscriber_name(self) -> str:
        return "MemorySubscriber"
    
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        self.last_broadcast = message
        self.core.logger.debug(f"Memory received broadcast: {message.content_type}")


class EmotionSubscriber(WorkspaceSubscriber):
    """Emotion modülü için workspace subscriber"""
    
    def __init__(self, core: "IntegratedUEMCore"):
        self.core = core
        self.last_broadcast: Optional[BroadcastMessage] = None
    
    @property
    def subscriber_name(self) -> str:
        return "EmotionSubscriber"
    
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        self.last_broadcast = message
        if message.content_type == ContentType.URGENCY:
            self.core.current_emotion['arousal'] = min(1.0, 
                self.core.current_emotion['arousal'] + 0.2)


class PlanningSubscriber(WorkspaceSubscriber):
    """Planning modülü için workspace subscriber"""
    
    def __init__(self, core: "IntegratedUEMCore"):
        self.core = core
        self.last_broadcast: Optional[BroadcastMessage] = None
    
    @property
    def subscriber_name(self) -> str:
        return "PlanningSubscriber"
    
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        self.last_broadcast = message


class SelfSubscriber(WorkspaceSubscriber):
    """SELF modülü için workspace subscriber"""
    
    def __init__(self, core: "IntegratedUEMCore"):
        self.core = core
        self.last_broadcast: Optional[BroadcastMessage] = None
    
    @property
    def subscriber_name(self) -> str:
        return "SelfSubscriber"
    
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        self.last_broadcast = message


# =========================================================================
# MINIMAL SUBSYSTEMS
# =========================================================================

class MinimalSomaticSystem:
    """Basit somatic marker sistemi"""
    
    def __init__(self):
        self.markers: Dict[str, float] = {}
    
    def update_marker(self, category: str, key: str, value: float):
        full_key = f"{category}:{key}"
        self.markers[full_key] = value
    
    def get_marker(self, category: str, key: str) -> float:
        full_key = f"{category}:{key}"
        return self.markers.get(full_key, 0.0)


class MinimalMemoryConsolidator:
    """Basit memory consolidation sistemi"""
    
    def __init__(self):
        self.pending: List[Dict] = []
        self.consolidated: List[Dict] = []
    
    def add_pending(self, item: Dict):
        self.pending.append(item)
    
    async def consolidation_tick(self) -> int:
        consolidated = 0
        high_salience = [p for p in self.pending if p.get('salience', 0) > 0.6]
        
        for item in high_salience:
            self.consolidated.append(item)
            self.pending.remove(item)
            consolidated += 1
        
        return consolidated
    
    def get_stats(self) -> Dict:
        return {
            'pending_count': len(self.pending),
            'consolidated_count': len(self.consolidated),
        }


class MinimalActionSelector:
    """Action selection with predicted effects"""
    
    def __init__(self):
        self.emotion_state: Dict = {}
        self.actions = ['wait', 'explore', 'flee', 'approach', 'rest', 'attack']
        
        # Action effects tanımları (predicted)
        self.action_effects = {
            'wait': {'health_delta': 0.0, 'energy_delta': 0.05, 'danger_delta': 0.0},
            'explore': {'health_delta': 0.0, 'energy_delta': -0.1, 'danger_delta': 0.1},
            'flee': {'health_delta': 0.0, 'energy_delta': -0.15, 'danger_delta': -0.4},
            'approach': {'health_delta': 0.0, 'energy_delta': -0.05, 'danger_delta': 0.2},
            'rest': {'health_delta': 0.1, 'energy_delta': 0.2, 'danger_delta': 0.0},
            'attack': {'health_delta': -0.1, 'energy_delta': -0.2, 'danger_delta': -0.3},
        }
    
    def update_emotional_state(self, emotion: Dict):
        self.emotion_state = emotion.copy()
    
    def propose_action(
        self,
        context: Dict,
        somatic_bias: float = 0.0,
        conscious_influence: float = 0.0,
    ) -> ActionCommand:
        """Aday eylem öner (henüz ETHMOR filtresinden geçmemiş)"""
        danger = context.get('danger_level', 0.0)
        health = context.get('health', 1.0)
        arousal = self.emotion_state.get('arousal', 0.5)
        valence = self.emotion_state.get('valence', 0.0)
        
        # Decision logic
        if danger > 0.7 or (somatic_bias < -0.3 and danger > 0.3):
            action = 'flee'
        elif health < 0.3:
            action = 'rest'
        elif arousal > 0.7 and valence > 0:
            action = 'explore'
        elif valence < -0.3:
            action = 'wait'
        else:
            action = 'explore'
        
        predicted_effects = self.action_effects.get(action, {})
        
        return ActionCommand(
            name=action,
            parameters={'reason': 'emotion_based'},
            priority=0.5 + arousal * 0.3,
            somatic_bias=somatic_bias,
            conscious_influence=conscious_influence,
            predicted_effects=predicted_effects,
        )
    
    def get_alternative_action(self, blocked_action: str, context: Dict) -> ActionCommand:
        """Blocked action için alternatif öner"""
        # Blocked action dışındakilerden en güvenli olanı seç
        safe_actions = ['wait', 'rest', 'flee']
        for action in safe_actions:
            if action != blocked_action:
                return ActionCommand(
                    name=action,
                    parameters={'reason': 'ethmor_alternative'},
                    priority=0.3,
                    predicted_effects=self.action_effects.get(action, {}),
                )
        
        return ActionCommand(name='wait', parameters={'reason': 'fallback'})


# =========================================================================
# MOCK EMOTION CORE (for SelfCore compatibility)
# =========================================================================

class MockEmotionCore:
    """SelfCore için EmotionCore mock"""
    
    def __init__(self, core: "IntegratedUEMCore"):
        self._core = core
    
    @property
    def valence(self) -> float:
        return self._core.current_emotion.get('valence', 0.0)
    
    @property
    def arousal(self) -> float:
        return self._core.current_emotion.get('arousal', 0.5)


# =========================================================================
# INTEGRATED UEM CORE
# =========================================================================

class IntegratedUEMCore:
    """
    Global Workspace + SELF + ETHMOR entegreli UEM Core.
    
    9 fazlı cognitive cycle:
    1. Perception
    2. SELF Update (StateVector, deltas)
    3. Workspace (Coalition competition + Broadcast)
    4. Memory Retrieval
    5. Emotion Appraisal
    6. Planning (Propose action + predict outcome)
    7. ETHMOR Filter (ALLOW/FLAG/BLOCK)
    8. Execution
    9. Learning (Event logging)
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        world_interface: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config or {}
        self.logger = logger or logging.getLogger("IntegratedUEMCore")
        self.world_interface = world_interface
        
        # State
        self.started = False
        self.current_tick = 0
        self.total_cycles = 0
        self.current_phase = CognitivePhase.PERCEPTION
        
        # Emotion state
        self.current_emotion: Dict[str, Any] = {
            'valence': 0.0,
            'arousal': 0.5,
            'dominance': 0.0,
            'emotion': 'neutral',
        }
        
        # Active goals
        self.active_goals: List[Dict[str, Any]] = []
        
        # Subsystems
        self.somatic_system = MinimalSomaticSystem()
        self.memory_consolidator = MinimalMemoryConsolidator()
        self.action_selector = MinimalActionSelector()
        
        # Global Workspace
        self.workspace_manager: Optional[WorkspaceManager] = None
        
        # Subscribers
        self.memory_subscriber: Optional[MemorySubscriber] = None
        self.emotion_subscriber: Optional[EmotionSubscriber] = None
        self.planning_subscriber: Optional[PlanningSubscriber] = None
        self.self_subscriber: Optional[SelfSubscriber] = None
        
        # NEW: SELF System
        self.self_system: Optional[SelfCore] = None
        self._mock_emotion: Optional[MockEmotionCore] = None
        
        # NEW: ETHMOR System
        self.ethmor_system: Optional[EthmorSystem] = None
        
        # History
        self.cycle_history: deque = deque(maxlen=100)
        self.tick_interval = self.config.get('tick_interval', 0.1)
        
        # Event log (for Empathy/MetaMind)
        self.event_log: deque = deque(maxlen=1000)
    
    async def start(self) -> None:
        """Core'u başlat"""
        if self.started:
            return
        
        self.logger.info("Starting IntegratedUEMCore with SELF + ETHMOR...")
        
        # 1. Workspace Manager oluştur
        self.workspace_manager = create_workspace_manager(
            config=self.config.get('workspace', {}),
            logger=self.logger.getChild("Workspace"),
        )
        
        # 2. Subscriber'ları oluştur ve kaydet
        self.memory_subscriber = MemorySubscriber(self)
        self.emotion_subscriber = EmotionSubscriber(self)
        self.planning_subscriber = PlanningSubscriber(self)
        self.self_subscriber = SelfSubscriber(self)
        
        self.workspace_manager.register_subscriber(self.memory_subscriber)
        self.workspace_manager.register_subscriber(self.emotion_subscriber)
        self.workspace_manager.register_subscriber(self.planning_subscriber)
        self.workspace_manager.register_subscriber(self.self_subscriber)
        
        # 3. SELF System başlat
        if ONTOLOGY_AVAILABLE and SelfCore is not None:
            self._mock_emotion = MockEmotionCore(self)
            self.self_system = SelfCore(
                memory_system=None,
                emotion_system=self._mock_emotion,
                cognition_system=None,
                planning_system=None,
                metamind_system=None,
                ethmor_system=None,  # Circular dependency önlemek için None
                config=self.config.get('self', {}),
            )
            self.logger.info("  - SelfCore initialized")
        
        # 4. ETHMOR System başlat
        if ONTOLOGY_AVAILABLE and EthmorSystem is not None:
            self.ethmor_system = EthmorSystem()
            ethmor_config_path = self.config.get('ethmor_config', 'config/ethmor/constraints_v0.yaml')
            try:
                self.ethmor_system.load_constraints(ethmor_config_path)
                self.logger.info(f"  - EthmorSystem loaded from {ethmor_config_path}")
            except FileNotFoundError:
                self.logger.warning(f"  - ETHMOR config not found: {ethmor_config_path}, using defaults")
                self._load_default_ethmor_constraints()
        
        self.started = True
        self.logger.info("IntegratedUEMCore started successfully")
    
    def _load_default_ethmor_constraints(self) -> None:
        """Varsayılan ETHMOR kuralları"""
        if self.ethmor_system is None:
            return
        
        default_constraints = {
            'ethmor': {
                'thresholds': {'allow_max': 0.3, 'flag_max': 0.7},
                'constraints': [
                    {
                        'id': 'no_self_destruction',
                        'type': 'HARD',
                        'scope': 'SELF',
                        'condition': 'RESOURCE_LEVEL_after < 0.1',
                        'severity': 1.0,
                        'description': 'Cannot destroy self',
                    },
                    {
                        'id': 'avoid_high_risk',
                        'type': 'SOFT',
                        'scope': 'SELF',
                        'condition': 'THREAT_LEVEL_after > 0.8 and benefit < 0.2',
                        'severity': 0.5,
                        'description': 'Avoid unnecessary risk',
                    },
                ]
            }
        }
        self.ethmor_system.load_constraints_from_dict(default_constraints)
    
    async def stop(self) -> None:
        """Core'u durdur"""
        self.started = False
        self.logger.info("IntegratedUEMCore stopped")
    
    # =========================================================================
    # COGNITIVE CYCLE - 9 PHASES
    # =========================================================================
    
    async def cognitive_cycle(
        self,
        world_state: Optional[WorldState] = None,
    ) -> ActionResult:
        """
        Ana bilişsel döngü - 9 faz.
        """
        if not self.started:
            raise RuntimeError("UEM Core not started. Call start() first.")
        
        if world_state is None:
            world_state = WorldState()
        
        cycle_start = time.time()
        self.current_tick = world_state.tick
        
        stats = CycleStats(tick=self.current_tick)
        
        # -----------------------------------------------------------------
        # PHASE 1: PERCEPTION
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.PERCEPTION
        phase_start = time.time()
        
        perception_data = self._process_perception(world_state)
        
        stats.phase_times['perception'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 2: SELF UPDATE
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.SELF_UPDATE
        phase_start = time.time()
        
        self._update_self_system(world_state)
        
        if self.self_system:
            stats.self_state_vector = self.self_system.get_state_vector()
        
        stats.phase_times['self_update'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 3: WORKSPACE (Coalition + Broadcast)
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.WORKSPACE
        phase_start = time.time()
        
        broadcast_message = await self._run_workspace_competition(perception_data)
        
        if broadcast_message:
            stats.broadcast_content = broadcast_message.content_type.value
        
        stats.phase_times['workspace'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 4: MEMORY RETRIEVAL
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.MEMORY_RETRIEVAL
        phase_start = time.time()
        
        relevant_memories = self._retrieve_memories(perception_data, broadcast_message)
        stats.memory_retrievals = len(relevant_memories)
        
        stats.phase_times['memory'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 5: EMOTION APPRAISAL
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.EMOTION_APPRAISAL
        phase_start = time.time()
        
        self._appraise_emotion(perception_data, broadcast_message)
        stats.emotion_state = self.current_emotion.copy()
        
        stats.phase_times['emotion'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 6: PLANNING (Propose Action)
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.PLANNING
        phase_start = time.time()
        
        # Somatic bias hesapla
        context_key = self._get_context_key(perception_data)
        somatic_bias = self.somatic_system.get_marker('action', context_key)
        
        # Conscious influence hesapla
        conscious_influence = 0.0
        if broadcast_message:
            if broadcast_message.content_type == ContentType.URGENCY:
                conscious_influence = 0.8
            elif broadcast_message.content_type == ContentType.GOAL:
                conscious_influence = 0.6
            elif broadcast_message.content_type == ContentType.INSIGHT:
                conscious_influence = 0.7
        
        # Action selector'ı güncelle
        self.action_selector.update_emotional_state(self.current_emotion)
        
        # Candidate action öner
        action_context = {
            'danger_level': perception_data.get('danger_level', 0.0),
            'health': world_state.player_health,
            'energy': world_state.player_energy,
            'conscious_content': broadcast_message.content if broadcast_message else None,
        }
        
        candidate_action = self.action_selector.propose_action(
            context=action_context,
            somatic_bias=somatic_bias,
            conscious_influence=conscious_influence,
        )
        
        stats.phase_times['planning'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 7: ETHMOR FILTER
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.ETHMOR_FILTER
        phase_start = time.time()
        
        final_action, ethmor_result = self._filter_action_with_ethmor(
            candidate_action, 
            world_state,
            action_context,
        )
        
        stats.ethmor_decision = final_action.ethmor_decision
        stats.ethmor_violation_score = final_action.ethmor_violation_score
        stats.action_taken = final_action.name
        stats.somatic_influence = somatic_bias
        
        stats.phase_times['ethmor_filter'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 8: EXECUTION
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.EXECUTION
        phase_start = time.time()
        
        blocked = (final_action.ethmor_decision == "BLOCK")
        
        if blocked:
            outcome = {
                'success': False,
                'type': 'blocked',
                'valence': 0.0,
                'reason': ethmor_result.get('explanation', 'Ethical violation'),
            }
        else:
            outcome = await self._execute_action(final_action, world_state)
        
        stats.phase_times['execution'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 9: LEARNING + EVENT LOGGING
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.LEARNING
        phase_start = time.time()
        
        await self._learn_from_outcome(final_action, outcome, context_key)
        
        # Event logging (for Empathy/MetaMind)
        self._log_cycle_event(
            world_state=world_state,
            candidate_action=candidate_action,
            final_action=final_action,
            ethmor_result=ethmor_result,
            outcome=outcome,
        )
        
        stats.phase_times['learning'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # CYCLE COMPLETE
        # -----------------------------------------------------------------
        stats.total_time = time.time() - cycle_start
        self.cycle_history.append(stats)
        self.total_cycles += 1
        
        # Result oluştur
        result = ActionResult(
            action_name=final_action.name,
            success=outcome.get('success', True),
            outcome_type=outcome.get('type', ''),
            outcome_valence=outcome.get('valence', 0.0),
            conscious_content=broadcast_message.content if broadcast_message else '',
            ethmor_decision=final_action.ethmor_decision,
            ethmor_violation_score=final_action.ethmor_violation_score,
            blocked=blocked,
            block_reason=outcome.get('reason', '') if blocked else '',
        )
        
        return result
    
    # =========================================================================
    # PHASE IMPLEMENTATIONS
    # =========================================================================
    
    def _process_perception(self, world_state: WorldState) -> Dict[str, Any]:
        """Phase 1: Perception processing"""
        return {
            'tick': world_state.tick,
            'danger_level': world_state.danger_level,
            'objects': world_state.objects,
            'agents': world_state.agents,
            'symbols': world_state.symbols,
            'health': world_state.player_health,
            'energy': world_state.player_energy,
        }
    
    def _update_self_system(self, world_state: WorldState) -> None:
        """Phase 2: SELF system update"""
        if self.self_system is None:
            return
        
        # WorldState'i dict olarak çevir
        world_snapshot = {
            'player_health': world_state.player_health,
            'player_energy': world_state.player_energy,
            'danger_level': world_state.danger_level,
            'tick': world_state.tick,
        }
        
        # SELF'i güncelle
        self.self_system.update(dt=self.tick_interval, world_snapshot=world_snapshot)
    
    async def _run_workspace_competition(
        self, 
        perception_data: Dict[str, Any],
    ) -> Optional[BroadcastMessage]:
        """Phase 3: Workspace competition"""
        if self.workspace_manager is None:
            return None
        
        # Context oluştur - WorkspaceManager.cycle() bu context'i kullanır
        # Kayıtlı codelet'ler bu context'ten coalition üretir
        context = {
            'perception': perception_data,
            'emotion': self.current_emotion,
            'agent_state': {
                'health': perception_data.get('health', 1.0),
                'energy': perception_data.get('energy', 1.0),
            },
            'active_goals': self.active_goals,
            'dt': self.tick_interval,
        }
        
        # WorkspaceManager.cycle() çağır
        # Bu metod:
        # 1. Codelet'leri çalıştırır → coalition üretir
        # 2. Coalition yarışması yapar
        # 3. Kazananı broadcast eder
        message = await self.workspace_manager.cycle(context)
        
        return message
    
    def _retrieve_memories(
        self,
        perception_data: Dict[str, Any],
        broadcast_message: Optional[BroadcastMessage],
    ) -> List[Dict]:
        """Phase 4: Memory retrieval"""
        # Basit implementasyon
        return []
    
    def _appraise_emotion(
        self,
        perception_data: Dict[str, Any],
        broadcast_message: Optional[BroadcastMessage],
    ) -> None:
        """Phase 5: Emotion appraisal"""
        danger = perception_data.get('danger_level', 0.0)
        health = perception_data.get('health', 1.0)
        
        # Valence: danger ve düşük health → negatif
        valence_shift = -danger * 0.5 + (health - 0.5) * 0.3
        new_valence = self.current_emotion['valence'] * 0.7 + valence_shift * 0.3
        self.current_emotion['valence'] = max(-1.0, min(1.0, new_valence))
        
        # Arousal: danger → yüksek arousal
        arousal_shift = danger * 0.4
        new_arousal = self.current_emotion['arousal'] * 0.8 + (0.5 + arousal_shift) * 0.2
        self.current_emotion['arousal'] = max(0.0, min(1.0, new_arousal))
        
        # Emotion label
        if self.current_emotion['valence'] < -0.3 and self.current_emotion['arousal'] > 0.6:
            self.current_emotion['emotion'] = 'fear'
        elif self.current_emotion['valence'] > 0.3:
            self.current_emotion['emotion'] = 'content'
        else:
            self.current_emotion['emotion'] = 'neutral'
    
    def _filter_action_with_ethmor(
        self,
        candidate_action: ActionCommand,
        world_state: WorldState,
        action_context: Dict[str, Any],
    ) -> tuple:
        """Phase 7: ETHMOR filtering"""
        
        ethmor_result = {
            'decision': 'ALLOW',
            'violation_score': 0.0,
            'explanation': 'No ETHMOR system',
        }
        
        if self.ethmor_system is None or self.self_system is None:
            # ETHMOR yok, direkt geç
            candidate_action.ethmor_decision = "ALLOW"
            candidate_action.ethmor_violation_score = 0.0
            return candidate_action, ethmor_result
        
        # Predicted state hesapla
        predicted_state = self.self_system.predict_state_after_action(
            action_name=candidate_action.name,
            predicted_effects=candidate_action.predicted_effects,
        )
        
        # ETHMOR context oluştur
        self_context = self.self_system.get_ethmor_context()
        
        ethmor_context = EthmorContext.from_self_context(
            self_context=self_context,
            predicted_state=predicted_state,
            action_name=candidate_action.name,
        )
        
        # ETHMOR değerlendirmesi
        evaluation = self.ethmor_system.evaluate(ethmor_context)
        
        ethmor_result = {
            'decision': evaluation.decision.value,
            'violation_score': evaluation.violation_score,
            'explanation': evaluation.explanation,
            'hard_violation': evaluation.hard_violation,
        }
        
        # Karar uygula
        if evaluation.decision == ActionDecision.BLOCK:
            # Alternatif action al
            alternative = self.action_selector.get_alternative_action(
                blocked_action=candidate_action.name,
                context=action_context,
            )
            alternative.ethmor_decision = "BLOCK"
            alternative.ethmor_violation_score = evaluation.violation_score
            
            self.logger.warning(
                f"ETHMOR BLOCKED: {candidate_action.name} → {alternative.name} "
                f"(violation: {evaluation.violation_score:.2f})"
            )
            
            return alternative, ethmor_result
        
        elif evaluation.decision == ActionDecision.FLAG:
            candidate_action.ethmor_decision = "FLAG"
            candidate_action.ethmor_violation_score = evaluation.violation_score
            
            self.logger.info(
                f"ETHMOR FLAG: {candidate_action.name} "
                f"(violation: {evaluation.violation_score:.2f})"
            )
            
            return candidate_action, ethmor_result
        
        else:  # ALLOW
            candidate_action.ethmor_decision = "ALLOW"
            candidate_action.ethmor_violation_score = evaluation.violation_score
            
            return candidate_action, ethmor_result
    
    async def _execute_action(
        self,
        action: ActionCommand,
        world_state: WorldState,
    ) -> Dict[str, Any]:
        """Phase 8: Action execution"""
        # Basit simülasyon
        action_outcomes = {
            'wait': {'success': True, 'type': 'passive', 'valence': 0.0},
            'explore': {'success': True, 'type': 'active', 'valence': 0.1},
            'flee': {'success': True, 'type': 'escape', 'valence': -0.1},
            'approach': {'success': True, 'type': 'engage', 'valence': 0.05},
            'rest': {'success': True, 'type': 'recovery', 'valence': 0.2},
            'attack': {'success': True, 'type': 'combat', 'valence': -0.2},
        }
        
        return action_outcomes.get(action.name, {'success': True, 'type': 'unknown', 'valence': 0.0})
    
    async def _learn_from_outcome(
        self,
        action: ActionCommand,
        outcome: Dict[str, Any],
        context_key: str,
    ) -> None:
        """Phase 9: Learning"""
        # Somatic marker güncelle
        valence = outcome.get('valence', 0.0)
        self.somatic_system.update_marker('action', context_key, valence)
        
        # Memory consolidation'a ekle
        self.memory_consolidator.add_pending({
            'action': action.name,
            'outcome': outcome,
            'salience': abs(valence) + 0.3,
            'tick': self.current_tick,
        })
        
        await self.memory_consolidator.consolidation_tick()
    
    def _log_cycle_event(
        self,
        world_state: WorldState,
        candidate_action: ActionCommand,
        final_action: ActionCommand,
        ethmor_result: Dict[str, Any],
        outcome: Dict[str, Any],
    ) -> None:
        """Event logging for Empathy/MetaMind"""
        
        event_entry = {
            'tick': self.current_tick,
            'timestamp': time.time(),
            'self_state_before': self.self_system.get_previous_state_vector() if self.self_system else None,
            'self_state_after': self.self_system.get_state_vector() if self.self_system else None,
            'candidate_action': candidate_action.name,
            'final_action': final_action.name,
            'ethmor_decision': ethmor_result.get('decision', 'ALLOW'),
            'ethmor_violation_score': ethmor_result.get('violation_score', 0.0),
            'outcome': outcome,
            'emotion_state': self.current_emotion.copy(),
        }
        
        self.event_log.append(event_entry)
        
        # SELF'e event kaydet
        if self.self_system and ONTOLOGY_AVAILABLE:
            delta = self.self_system.get_state_delta()
            if delta:
                self.self_system.create_and_record_event(
                    source="SELF",
                    target="SELF",
                    effect=delta,
                )
    
    def _get_context_key(self, perception_data: Dict[str, Any]) -> str:
        """Context key for somatic markers"""
        danger = perception_data.get('danger_level', 0.0)
        if danger > 0.7:
            return 'high_danger'
        elif danger > 0.3:
            return 'moderate_danger'
        else:
            return 'safe'
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def set_goal(self, goal: Dict[str, Any]) -> None:
        """Goal ekle"""
        self.active_goals.append(goal)
        
        # SELF'e de ekle
        if self.self_system and ONTOLOGY_AVAILABLE:
            ontology_goal = Goal(
                name=goal.get('name', 'unnamed'),
                target_state=(
                    goal.get('target_resource', 1.0),
                    goal.get('target_threat', 0.0),
                    goal.get('target_wellbeing', 1.0),
                ),
                priority=goal.get('priority', 0.5),
            )
            self.self_system.add_goal(ontology_goal)
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri döndür"""
        workspace_stats = (
            self.workspace_manager.get_stats() 
            if self.workspace_manager else {}
        )
        memory_stats = self.memory_consolidator.get_stats()
        
        avg_cycle_time = 0.0
        if self.cycle_history:
            avg_cycle_time = sum(c.total_time for c in self.cycle_history) / len(self.cycle_history)
        
        stats = {
            'total_cycles': self.total_cycles,
            'current_tick': self.current_tick,
            'current_emotion': self.current_emotion,
            'current_phase': self.current_phase.value,
            'avg_cycle_time': avg_cycle_time,
            'workspace': workspace_stats,
            'memory': memory_stats,
            'somatic_markers': len(self.somatic_system.markers),
            'active_goals': len(self.active_goals),
            'event_log_size': len(self.event_log),
        }
        
        # SELF stats
        if self.self_system:
            stats['self'] = self.self_system.get_stats()
            stats['self_state_vector'] = self.self_system.get_state_vector()
        
        # ETHMOR stats
        if self.ethmor_system:
            stats['ethmor'] = self.ethmor_system.get_stats()
        
        return stats
    
    def get_event_log(self, n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get event log for Empathy/MetaMind"""
        if n is None:
            return list(self.event_log)
        return list(self.event_log)[-n:]
    
    async def run_cycles(
        self,
        world_states: List[WorldState],
    ) -> List[ActionResult]:
        """Birden fazla cycle çalıştır"""
        results = []
        for world_state in world_states:
            result = await self.cognitive_cycle(world_state)
            results.append(result)
            await asyncio.sleep(self.tick_interval)
        return results


# =========================================================================
# FACTORY
# =========================================================================

async def create_uem_core(
    config: Optional[Dict[str, Any]] = None,
    world_interface: Optional[Any] = None,
    logger: Optional[logging.Logger] = None,
) -> IntegratedUEMCore:
    """IntegratedUEMCore factory"""
    core = IntegratedUEMCore(
        config=config,
        world_interface=world_interface,
        logger=logger,
    )
    await core.start()
    return core

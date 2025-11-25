"""
UEM Integrated Core - Global Workspace Entegrasyonlu

Cognitive Cycle with Conscious Broadcast:
1. PERCEPTION: World state → Percepts
2. WORKSPACE: Coalition competition → Conscious broadcast
3. MEMORY: Broadcast + context → Memory retrieval
4. EMOTION: Appraisal + somatic markers
5. PLANNING: Conscious content + emotion → Action selection
6. EXECUTION: Action → World
7. LEARNING: Outcome → Memory consolidation + Somatic update

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
    Codelet,
    Coalition,
    create_workspace_manager,
)


# =========================================================================
# ENUMS & DATA TYPES
# =========================================================================

class CognitivePhase(Enum):
    """Cognitive cycle phases"""
    PERCEPTION = "perception"
    WORKSPACE = "workspace"
    MEMORY_RETRIEVAL = "memory_retrieval"
    EMOTION_APPRAISAL = "emotion_appraisal"
    PLANNING = "planning"
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
    conscious_influence: float = 0.0  # Workspace broadcast'ının etkisi


@dataclass
class ActionResult:
    """Eylem sonucu"""
    action_name: str
    success: bool
    outcome_type: str = ""
    outcome_valence: float = 0.0
    conscious_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CycleStats:
    """Cycle istatistikleri"""
    cycle_number: int
    phase_times: Dict[str, float] = field(default_factory=dict)
    action_taken: str = ""
    emotion_state: Dict[str, Any] = field(default_factory=dict)
    memory_retrievals: int = 0
    somatic_influence: float = 0.0
    workspace_broadcast: Optional[str] = None
    conscious_content_type: Optional[str] = None
    total_time: float = 0.0


# =========================================================================
# MODULE SUBSCRIBERS (Broadcast alıcıları)
# =========================================================================

class MemorySubscriber(WorkspaceSubscriber):
    """Memory module - broadcast'tan learning/consolidation trigger'ı alır"""
    
    def __init__(self, core: 'IntegratedUEMCore'):
        self.core = core
        self.received_broadcasts: List[BroadcastMessage] = []
    
    @property
    def subscriber_name(self) -> str:
        return "MemoryModule"
    
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        """Broadcast alındığında memory consolidation'ı trigger et"""
        self.received_broadcasts.append(message)
        
        # Önemli içerikler için memory consolidation'a ekle
        if message.content_type in [ContentType.INSIGHT, ContentType.NOVELTY]:
            if self.core.memory_consolidator:
                self.core.memory_consolidator.add_to_pending(
                    content=message.content,
                    salience=message.coalition.salience,
                    emotion_state=self.core.current_emotion,
                    source=f"broadcast_{message.content_type.value}",
                )


class EmotionSubscriber(WorkspaceSubscriber):
    """Emotion module - broadcast'tan emotional salience alır"""
    
    def __init__(self, core: 'IntegratedUEMCore'):
        self.core = core
    
    @property
    def subscriber_name(self) -> str:
        return "EmotionModule"
    
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        """Broadcast'a göre emotion state'i modüle et"""
        if message.content_type == ContentType.URGENCY:
            # Urgency → arousal artışı
            current_arousal = self.core.current_emotion.get('arousal', 0.5)
            self.core.current_emotion['arousal'] = min(1.0, current_arousal + 0.2)
        
        elif message.content_type == ContentType.EMOTION:
            # Emotion broadcast → doğrudan emotion update
            if 'valence' in message.content:
                self.core.current_emotion['valence'] = message.content['valence']
            if 'arousal' in message.content:
                self.core.current_emotion['arousal'] = message.content['arousal']


class PlanningSubscriber(WorkspaceSubscriber):
    """Planning module - broadcast conscious content alır"""
    
    def __init__(self, core: 'IntegratedUEMCore'):
        self.core = core
        self.conscious_context: Optional[BroadcastMessage] = None
    
    @property
    def subscriber_name(self) -> str:
        return "PlanningModule"
    
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        """Conscious content'i planning context'e ekle"""
        self.conscious_context = message
        
        # Goal broadcast → attention shift
        if message.content_type == ContentType.GOAL:
            goal_data = message.content.get('goal', {})
            if isinstance(goal_data, dict):
                self.core.workspace_manager.set_attention_goal(
                    goal_type='active_goal',
                    target=goal_data.get('name', 'goal'),
                    priority=goal_data.get('priority', 0.5),
                )


class SelfSubscriber(WorkspaceSubscriber):
    """Self module - meta-cognition için broadcast izleme"""
    
    def __init__(self, core: 'IntegratedUEMCore'):
        self.core = core
        self.broadcast_history: deque = deque(maxlen=50)
        self.attention_patterns: Dict[str, int] = {}
    
    @property
    def subscriber_name(self) -> str:
        return "SelfModule"
    
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        """Broadcast pattern'lerini izle (meta-cognition)"""
        self.broadcast_history.append(message)
        
        # Content type frequency tracking
        ct = message.content_type.value
        self.attention_patterns[ct] = self.attention_patterns.get(ct, 0) + 1


# =========================================================================
# MINIMAL SUBSYSTEM IMPLEMENTATIONS
# =========================================================================

class MinimalSomaticSystem:
    """Basit somatic marker sistemi"""
    
    def __init__(self):
        self.markers: Dict[str, float] = {}
        self.outcome_history: List[Dict] = []
    
    def get_marker(self, action: str, context: str) -> float:
        key = f"{action}:{context}"
        return self.markers.get(key, 0.0)
    
    def update_marker(self, action: str, context: str, valence: float, learning_rate: float = 0.3):
        key = f"{action}:{context}"
        old_value = self.markers.get(key, 0.0)
        self.markers[key] = old_value + learning_rate * (valence - old_value)
    
    def record_outcome(self, outcome_valence: float, outcome_description: str):
        self.outcome_history.append({
            'valence': outcome_valence,
            'description': outcome_description,
            'timestamp': time.time(),
        })


class MinimalMemoryConsolidator:
    """Basit memory consolidation sistemi"""
    
    def __init__(self):
        self.pending: List[Dict] = []
        self.consolidated: List[Dict] = []
    
    def add_to_pending(
        self,
        content: Any,
        salience: float,
        emotion_state: Dict,
        source: str = "",
        **kwargs
    ):
        self.pending.append({
            'content': content,
            'salience': salience,
            'emotion': emotion_state.copy(),
            'source': source,
            'timestamp': time.time(),
        })
    
    async def consolidation_tick(self) -> int:
        # Yüksek salience olanları consolidate et
        consolidated = 0
        high_salience = [p for p in self.pending if p['salience'] > 0.6]
        
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
    """Basit action selection sistemi"""
    
    def __init__(self):
        self.emotion_state: Dict = {}
        self.actions = ['wait', 'explore', 'flee', 'approach', 'rest']
    
    def update_emotional_state(self, emotion: Dict):
        self.emotion_state = emotion.copy()
    
    def select_action(
        self,
        context: Dict,
        somatic_bias: float = 0.0,
        conscious_influence: float = 0.0,
    ) -> ActionCommand:
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
        
        return ActionCommand(
            name=action,
            parameters={'reason': 'emotion_based'},
            priority=0.5 + arousal * 0.3,
            somatic_bias=somatic_bias,
            conscious_influence=conscious_influence,
        )


# =========================================================================
# INTEGRATED UEM CORE
# =========================================================================

class IntegratedUEMCore:
    """
    Global Workspace entegreli UEM Core.
    
    7 fazlı cognitive cycle:
    1. Perception
    2. Workspace (Coalition competition + Broadcast)
    3. Memory Retrieval
    4. Emotion Appraisal
    5. Planning
    6. Execution
    7. Learning
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
        
        # History
        self.cycle_history: deque = deque(maxlen=100)
        self.tick_interval = self.config.get('tick_interval', 0.1)
    
    async def start(self) -> None:
        """Core'u başlat"""
        if self.started:
            return
        
        self.logger.info("Starting IntegratedUEMCore with Global Workspace...")
        
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
        
        self.started = True
        self.logger.info("IntegratedUEMCore started successfully")
    
    async def stop(self) -> None:
        """Core'u durdur"""
        self.started = False
        self.logger.info("IntegratedUEMCore stopped")
    
    # =========================================================================
    # COGNITIVE CYCLE
    # =========================================================================
    
    async def cognitive_cycle(
        self,
        world_state: Optional[WorldState] = None,
    ) -> ActionResult:
        """
        Ana bilişsel döngü - 7 faz.
        """
        if not self.started:
            raise RuntimeError("UEM Core not started. Call start() first.")
        
        cycle_start = time.time()
        stats = CycleStats(cycle_number=self.total_cycles)
        
        # Default world state
        if world_state is None:
            world_state = WorldState(tick=self.current_tick)
        
        self.current_tick = world_state.tick
        
        # -----------------------------------------------------------------
        # PHASE 1: PERCEPTION
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.PERCEPTION
        phase_start = time.time()
        
        perception_data = self._process_perception(world_state)
        
        stats.phase_times['perception'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 2: WORKSPACE (Coalition Competition + Broadcast)
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.WORKSPACE
        phase_start = time.time()
        
        # Workspace context hazırla
        workspace_context = {
            'perception': perception_data,
            'emotion': self.current_emotion.copy(),
            'active_goals': self.active_goals,
            'agent_state': {
                'health': world_state.player_health,
                'energy': world_state.player_energy,
            },
            'relevant_memories': [],  # Memory retrieval sonrası doldurulabilir
            'dt': self.tick_interval,
        }
        
        # Workspace cycle çalıştır
        broadcast_message = await self.workspace_manager.cycle(workspace_context)
        
        if broadcast_message:
            stats.workspace_broadcast = broadcast_message.content_type.value
            stats.conscious_content_type = broadcast_message.content_type.value
            self.logger.debug(
                f"[CONSCIOUS] {broadcast_message.content_type.value}: "
                f"{broadcast_message.content}"
            )
        
        stats.phase_times['workspace'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 3: MEMORY RETRIEVAL
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.MEMORY_RETRIEVAL
        phase_start = time.time()
        
        relevant_memories = self._retrieve_memories(perception_data, broadcast_message)
        stats.memory_retrievals = len(relevant_memories)
        
        stats.phase_times['memory'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 4: EMOTION APPRAISAL
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.EMOTION_APPRAISAL
        phase_start = time.time()
        
        self._appraise_emotion(perception_data, broadcast_message)
        stats.emotion_state = self.current_emotion.copy()
        
        stats.phase_times['emotion'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 5: PLANNING / ACTION SELECTION
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
                conscious_influence = 0.8  # Urgency güçlü etki
            elif broadcast_message.content_type == ContentType.GOAL:
                conscious_influence = 0.6
            elif broadcast_message.content_type == ContentType.INSIGHT:
                conscious_influence = 0.7
        
        # Action selector'ı güncelle
        self.action_selector.update_emotional_state(self.current_emotion)
        
        # Action seç
        action_context = {
            'danger_level': perception_data.get('danger_level', 0.0),
            'health': world_state.player_health,
            'energy': world_state.player_energy,
            'conscious_content': broadcast_message.content if broadcast_message else None,
        }
        
        action_command = self.action_selector.select_action(
            context=action_context,
            somatic_bias=somatic_bias,
            conscious_influence=conscious_influence,
        )
        
        stats.action_taken = action_command.name
        stats.somatic_influence = somatic_bias
        
        stats.phase_times['planning'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 6: EXECUTION
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.EXECUTION
        phase_start = time.time()
        
        outcome = await self._execute_action(action_command, world_state)
        
        stats.phase_times['execution'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # PHASE 7: LEARNING
        # -----------------------------------------------------------------
        self.current_phase = CognitivePhase.LEARNING
        phase_start = time.time()
        
        await self._learn_from_outcome(action_command, outcome, context_key)
        
        stats.phase_times['learning'] = time.time() - phase_start
        
        # -----------------------------------------------------------------
        # CYCLE COMPLETE
        # -----------------------------------------------------------------
        stats.total_time = time.time() - cycle_start
        self.cycle_history.append(stats)
        self.total_cycles += 1
        
        # Result oluştur
        result = ActionResult(
            action_name=action_command.name,
            success=outcome.get('success', True),
            outcome_type=outcome.get('type', ''),
            outcome_valence=outcome.get('valence', 0.0),
            conscious_content=(
                broadcast_message.content_type.value 
                if broadcast_message else None
            ),
            metadata={
                'cycle': self.total_cycles,
                'emotion': self.current_emotion.copy(),
                'somatic_bias': somatic_bias,
                'conscious_influence': conscious_influence,
            },
        )
        
        self.logger.debug(
            f"Cycle {self.total_cycles} complete: {action_command.name} "
            f"({stats.total_time*1000:.1f}ms)"
        )
        
        return result
    
    # =========================================================================
    # PHASE IMPLEMENTATIONS
    # =========================================================================
    
    def _process_perception(self, world_state: WorldState) -> Dict[str, Any]:
        """Perception phase: World state → Perception data"""
        return {
            'danger_level': world_state.danger_level,
            'objects': world_state.objects,
            'agents': world_state.agents,
            'symbols': world_state.symbols,
            'position': world_state.player_position,
            'health': world_state.player_health,
            'energy': world_state.player_energy,
            'tick': world_state.tick,
        }
    
    def _retrieve_memories(
        self,
        perception_data: Dict[str, Any],
        broadcast: Optional[BroadcastMessage],
    ) -> List[Dict]:
        """Memory retrieval: Context → Relevant memories"""
        # Basit implementation - consolidated memories'den ara
        relevant = []
        
        for memory in self.memory_consolidator.consolidated:
            content = memory.get('content', {})
            if isinstance(content, dict):
                # Danger-related memories
                if perception_data.get('danger_level', 0) > 0.5:
                    if content.get('type') == 'danger' or content.get('outcome_type') == 'took_damage':
                        memory['relevance'] = 0.8
                        relevant.append(memory)
        
        return relevant[:5]  # Top 5
    
    def _appraise_emotion(
        self,
        perception_data: Dict[str, Any],
        broadcast: Optional[BroadcastMessage],
    ) -> None:
        """Emotion appraisal: Update emotion state"""
        danger = perception_data.get('danger_level', 0.0)
        health = perception_data.get('health', 1.0)
        
        # Danger → negative valence, high arousal
        if danger > 0.5:
            self.current_emotion['valence'] = -danger
            self.current_emotion['arousal'] = min(1.0, 0.5 + danger * 0.5)
            self.current_emotion['emotion'] = 'fear'
        
        # Low health → anxiety
        elif health < 0.3:
            self.current_emotion['valence'] = -0.5
            self.current_emotion['arousal'] = 0.7
            self.current_emotion['emotion'] = 'anxiety'
        
        # Normal → gradual return to neutral
        else:
            # Decay towards neutral
            self.current_emotion['valence'] *= 0.9
            self.current_emotion['arousal'] = (
                self.current_emotion['arousal'] * 0.9 + 0.5 * 0.1
            )
            
            if abs(self.current_emotion['valence']) < 0.1:
                self.current_emotion['emotion'] = 'neutral'
    
    async def _execute_action(
        self,
        action: ActionCommand,
        world_state: WorldState,
    ) -> Dict[str, Any]:
        """Execute action in world"""
        if self.world_interface:
            return await self.world_interface.execute(action, world_state)
        
        # Simulated outcome
        return {
            'success': True,
            'type': 'simulated',
            'valence': 0.0,
        }
    
    async def _learn_from_outcome(
        self,
        action: ActionCommand,
        outcome: Dict[str, Any],
        context_key: str,
    ) -> None:
        """Learning phase: Update somatic markers + memory consolidation"""
        
        valence = outcome.get('valence', 0.0)
        outcome_type = outcome.get('type', '')
        
        # 1. Somatic marker update
        self.somatic_system.update_marker(
            action=action.name,
            context=context_key,
            valence=valence,
        )
        
        # 2. Record outcome
        self.somatic_system.record_outcome(valence, outcome_type)
        
        # 3. Memory consolidation tick
        await self.memory_consolidator.consolidation_tick()
        
        # 4. Add significant outcomes to memory
        if abs(valence) > 0.5:
            self.memory_consolidator.add_to_pending(
                content={
                    'action': action.name,
                    'outcome': outcome_type,
                    'valence': valence,
                    'tick': self.current_tick,
                },
                salience=abs(valence),
                emotion_state=self.current_emotion,
                source='outcome_learning',
            )
    
    def _get_context_key(self, perception_data: Dict[str, Any]) -> str:
        """Context için basit key oluştur"""
        danger = perception_data.get('danger_level', 0.0)
        if danger > 0.7:
            return 'high_danger'
        elif danger > 0.3:
            return 'medium_danger'
        else:
            return 'safe'
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def set_goal(self, goal: Dict[str, Any]) -> None:
        """Hedef ekle"""
        self.active_goals.append(goal)
        self.active_goals.sort(key=lambda g: g.get('priority', 0.5), reverse=True)
        
        # Workspace'e attention goal olarak ekle
        if self.workspace_manager:
            self.workspace_manager.set_attention_goal(
                goal_type='user_goal',
                target='goal',
                priority=goal.get('priority', 0.5),
            )
    
    def set_emotion(
        self,
        valence: float,
        arousal: float,
        dominance: float = 0.0,
    ) -> None:
        """Emotion state'i manuel ayarla"""
        self.current_emotion = {
            'valence': max(-1, min(1, valence)),
            'arousal': max(0, min(1, arousal)),
            'dominance': max(-1, min(1, dominance)),
            'emotion': self._classify_emotion(valence, arousal),
        }
        self.action_selector.update_emotional_state(self.current_emotion)
    
    def _classify_emotion(self, valence: float, arousal: float) -> str:
        """PAD → discrete emotion"""
        if valence > 0.3 and arousal > 0.5:
            return 'excited'
        elif valence > 0.3:
            return 'happy'
        elif valence < -0.3 and arousal > 0.5:
            return 'fear'
        elif valence < -0.3:
            return 'sad'
        else:
            return 'neutral'
    
    def get_conscious_content(self) -> Optional[Dict[str, Any]]:
        """Şu anki conscious content"""
        if self.workspace_manager:
            content = self.workspace_manager.get_current_content()
            if content:
                return {
                    'type': content.content_type.value,
                    'content': content.content,
                    'activation': content.activation,
                }
        return None
    
    def get_attention_focus(self) -> Optional[str]:
        """Şu anki dikkat odağı"""
        if self.workspace_manager:
            return self.workspace_manager.get_current_focus()
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Kapsamlı istatistikler"""
        workspace_stats = (
            self.workspace_manager.get_stats() 
            if self.workspace_manager else {}
        )
        memory_stats = self.memory_consolidator.get_stats()
        
        avg_cycle_time = 0.0
        if self.cycle_history:
            avg_cycle_time = sum(c.total_time for c in self.cycle_history) / len(self.cycle_history)
        
        return {
            'total_cycles': self.total_cycles,
            'current_tick': self.current_tick,
            'current_emotion': self.current_emotion,
            'current_phase': self.current_phase.value,
            'avg_cycle_time': avg_cycle_time,
            'workspace': workspace_stats,
            'memory': memory_stats,
            'somatic_markers': len(self.somatic_system.markers),
            'active_goals': len(self.active_goals),
        }
    
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

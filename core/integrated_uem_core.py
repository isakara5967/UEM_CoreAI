"""
UEM Integrated Core - Full Cognitive Cycle

Tüm modülleri birleştiren ana orkestratör:
- EventBus: Async pub/sub iletişim
- PerceptionCore: Dünyadan girdi alma
- MemoryCore: STM, Working Memory, LTM
- MemoryConsolidator: STM → LTM transfer
- EmotionCore: PAD emotion state
- SomaticMarkerSystem: Deneyimsel öğrenme
- PlanningCore: Emotion-aware karar verme
- Action execution ve world interaction

Cognitive Cycle:
1. Perception → Event publish
2. Memory retrieval + Emotion appraisal (parallel)
3. Planning with emotion + somatic bias
4. Action selection
5. World outcome → Somatic marker update
6. Memory consolidation
"""

from __future__ import annotations
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum


# =========================================================================
# DATA TYPES
# =========================================================================

class CognitivePhase(Enum):
    """Cognitive cycle phases"""
    PERCEPTION = "perception"
    MEMORY_RETRIEVAL = "memory_retrieval"
    EMOTION_APPRAISAL = "emotion_appraisal"
    PLANNING = "planning"
    ACTION_SELECTION = "action_selection"
    EXECUTION = "execution"
    LEARNING = "learning"
    CONSOLIDATION = "consolidation"


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
class ActionResult:
    """Eylem sonucu"""
    action_name: str
    success: bool
    outcome_type: str = ""  # "took_damage", "found_reward", etc.
    outcome_valence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CycleStats:
    """Cognitive cycle istatistikleri"""
    cycle_number: int = 0
    phase_times: Dict[str, float] = field(default_factory=dict)
    total_time: float = 0.0
    action_taken: str = ""
    emotion_state: Dict[str, float] = field(default_factory=dict)
    memory_retrievals: int = 0
    somatic_influence: float = 0.0


# =========================================================================
# INTEGRATED UEM CORE
# =========================================================================

class IntegratedUEMCore:
    """
    UEM Entegre Çekirdek - Tüm modüller birleşik.
    
    Bu sınıf, aşağıdaki modülleri orchestrate eder:
    - EventBus (pub/sub)
    - PerceptionCore → perception.new_data
    - MemoryCore (STM, Working Memory)
    - LongTermMemory + MemoryConsolidator
    - EmotionCore → emotion.state_changed
    - SomaticMarkerSystem + SomaticEventHandler
    - EmotionalActionSelector
    - World interface
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        world_interface: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config or {}
        self.world_interface = world_interface
        self.logger = logger or logging.getLogger("uem.IntegratedCore")
        
        # Timing
        self.tick_interval = self.config.get('tick_interval', 0.1)
        self.current_tick = 0
        
        # State
        self.started = False
        self.current_phase = CognitivePhase.PERCEPTION
        self.current_emotion = {'valence': 0.0, 'arousal': 0.0, 'dominance': 0.0}
        
        # Statistics
        self.total_cycles = 0
        self.total_actions = 0
        self.cycle_history: List[CycleStats] = []
        
        # Components (initialized in start())
        self.event_bus = None
        self.memory_stm = None
        self.memory_ltm = None
        self.memory_consolidator = None
        self.somatic_system = None
        self.somatic_handler = None
        self.action_selector = None
        self.outcome_publisher = None
        
        # Callbacks
        self._world_action_callback: Optional[Callable] = None
    
    async def start(self) -> None:
        """Initialize all subsystems"""
        if self.started:
            self.logger.warning("[UEM] Already started")
            return
        
        self.logger.info("[UEM] Initializing Integrated Core...")
        
        # 1. Event Bus
        from core.event_bus import EventBus
        self.event_bus = EventBus('tcp://127.0.0.1:5560')
        await self.event_bus.start()
        self.logger.info("[UEM] ✓ EventBus started")
        
        # 2. Memory Systems
        from core.memory.consolidation.memory_consolidation import (
            LongTermMemory,
            MemoryConsolidator,
            MemoryType,
        )
        
        self.memory_ltm = LongTermMemory(
            max_memories=self.config.get('ltm_capacity', 5000),
            logger=self.logger.getChild("LTM"),
        )
        
        self.memory_consolidator = MemoryConsolidator(
            ltm=self.memory_ltm,
            consolidation_threshold=0.6,
            emotion_boost=0.3,
            consolidation_interval=30.0,  # 30 saniyede bir consolidation
            logger=self.logger.getChild("Consolidator"),
        )
        await self.memory_consolidator.start()
        self.logger.info("[UEM] ✓ Memory systems initialized")
        
        # 3. Somatic Marker System
        from core.emotion.somatic_marker_system import SomaticMarkerSystem
        from core.emotion.somatic_event_handler import (
            SomaticEventHandler,
            WorldOutcomePublisher,
        )
        
        self.somatic_system = SomaticMarkerSystem(
            logger=self.logger.getChild("Somatic"),
        )
        
        self.somatic_handler = SomaticEventHandler(
            somatic_system=self.somatic_system,
            event_bus=self.event_bus,
            logger=self.logger.getChild("SomaticHandler"),
        )
        await self.somatic_handler.initialize()
        
        self.outcome_publisher = WorldOutcomePublisher(
            self.event_bus,
            logger=self.logger.getChild("OutcomePublisher"),
        )
        self.logger.info("[UEM] ✓ Somatic Marker System initialized")
        
        # 4. Action Selector
        from core.planning.action_selection.somatic_action_selector import (
            SomaticEmotionalActionSelector,
        )
        
        self.action_selector = SomaticEmotionalActionSelector(
            somatic_system=self.somatic_system,
            logger=self.logger.getChild("ActionSelector"),
        )
        self.logger.info("[UEM] ✓ Action Selector initialized")
        
        # 5. Event Subscriptions
        await self._setup_subscriptions()
        
        self.started = True
        self.logger.info("[UEM] ✓ Integrated Core started successfully")
    
    async def stop(self) -> None:
        """Shutdown all subsystems"""
        if not self.started:
            return
        
        self.logger.info("[UEM] Shutting down...")
        
        if self.memory_consolidator:
            await self.memory_consolidator.stop()
        
        if self.event_bus:
            await self.event_bus.stop()
        
        self.started = False
        self.logger.info("[UEM] Shutdown complete")
    
    async def _setup_subscriptions(self) -> None:
        """Setup event subscriptions"""
        # Emotion changes → update action selector
        await self.event_bus.subscribe(
            'emotion.state_changed',
            self._on_emotion_changed
        )
        
        # World outcomes → somatic + memory
        await self.event_bus.subscribe(
            'world.outcome_received',
            self._on_world_outcome
        )
        
        self.logger.info("[UEM] Event subscriptions configured")
    
    async def _on_emotion_changed(self, event) -> None:
        """Handle emotion state changes"""
        self.current_emotion = {
            'valence': event.data.get('valence', 0),
            'arousal': event.data.get('arousal', 0),
            'dominance': event.data.get('dominance', 0),
            'emotion': event.data.get('emotion', 'neutral'),
        }
        
        # Update action selector
        if self.action_selector:
            self.action_selector.update_emotional_state(event.data)
        
        # Update consolidator emotion context
        if self.memory_consolidator:
            self.memory_consolidator.update_emotion_context(event.data)
    
    async def _on_world_outcome(self, event) -> None:
        """Handle world outcomes for learning"""
        outcome_type = event.data.get('outcome_type', '')
        valence = event.data.get('outcome_valence', 0)
        
        # Add to memory consolidation with emotion
        from core.memory.consolidation.memory_consolidation import MemoryType
        
        self.memory_consolidator.add_to_pending(
            content={
                'type': 'world_outcome',
                'outcome_type': outcome_type,
                'tick': self.current_tick,
            },
            salience=0.5 + abs(valence) * 0.5,
            emotion_state={
                'valence': valence,
                'arousal': 0.5,
                'emotion': outcome_type,
            },
            memory_type=MemoryType.EPISODIC,
            source='world_outcome',
        )
    
    # =========================================================================
    # COGNITIVE CYCLE
    # =========================================================================
    
    async def cognitive_cycle(
        self,
        world_state: Optional[WorldState] = None,
    ) -> ActionResult:
        """
        Ana bilişsel döngü.
        
        1. Perception: World state'i işle
        2. Memory: İlgili anıları getir
        3. Emotion: Durumu değerlendir
        4. Planning: Emotion + Somatic ile karar ver
        5. Execute: Eylemi gerçekleştir
        6. Learn: Sonuçtan öğren
        
        Returns:
            ActionResult: Seçilen eylem ve sonucu
        """
        if not self.started:
            raise RuntimeError("UEM Core not started. Call start() first.")
        
        cycle_start = time.time()
        stats = CycleStats(cycle_number=self.total_cycles)
        
        # Default world state
        if world_state is None:
            world_state = WorldState(tick=self.current_tick)
        
        self.current_tick = world_state.tick
        
        # ---------------------------------------------------------------------
        # PHASE 1: PERCEPTION
        # ---------------------------------------------------------------------
        self.current_phase = CognitivePhase.PERCEPTION
        phase_start = time.time()
        
        perception_data = await self._process_perception(world_state)
        
        stats.phase_times['perception'] = time.time() - phase_start
        
        # ---------------------------------------------------------------------
        # PHASE 2: MEMORY RETRIEVAL
        # ---------------------------------------------------------------------
        self.current_phase = CognitivePhase.MEMORY_RETRIEVAL
        phase_start = time.time()
        
        relevant_memories = await self._retrieve_memories(perception_data)
        stats.memory_retrievals = len(relevant_memories)
        
        stats.phase_times['memory'] = time.time() - phase_start
        
        # ---------------------------------------------------------------------
        # PHASE 3: EMOTION APPRAISAL
        # ---------------------------------------------------------------------
        self.current_phase = CognitivePhase.EMOTION_APPRAISAL
        phase_start = time.time()
        
        emotion_state = await self._appraise_emotion(perception_data)
        stats.emotion_state = emotion_state.copy()
        
        stats.phase_times['emotion'] = time.time() - phase_start
        
        # ---------------------------------------------------------------------
        # PHASE 4: PLANNING / ACTION SELECTION
        # ---------------------------------------------------------------------
        self.current_phase = CognitivePhase.ACTION_SELECTION
        phase_start = time.time()
        
        action_command = await self._select_action(perception_data, relevant_memories)
        stats.action_taken = action_command.name
        stats.somatic_influence = getattr(action_command, 'somatic_bias', 0.0)
        
        stats.phase_times['planning'] = time.time() - phase_start
        
        # ---------------------------------------------------------------------
        # PHASE 5: EXECUTION
        # ---------------------------------------------------------------------
        self.current_phase = CognitivePhase.EXECUTION
        phase_start = time.time()
        
        action_result = await self._execute_action(action_command, world_state)
        
        stats.phase_times['execution'] = time.time() - phase_start
        
        # ---------------------------------------------------------------------
        # PHASE 6: LEARNING
        # ---------------------------------------------------------------------
        self.current_phase = CognitivePhase.LEARNING
        phase_start = time.time()
        
        await self._process_outcome(action_result)
        
        stats.phase_times['learning'] = time.time() - phase_start
        
        # ---------------------------------------------------------------------
        # FINALIZE
        # ---------------------------------------------------------------------
        stats.total_time = time.time() - cycle_start
        self.cycle_history.append(stats)
        self.total_cycles += 1
        self.total_actions += 1
        
        self.logger.debug(
            "[UEM] Cycle %d: action=%s, time=%.3fs",
            self.total_cycles, stats.action_taken, stats.total_time
        )
        
        return action_result
    
    async def _process_perception(self, world_state: WorldState) -> Dict[str, Any]:
        """Process world state into perception data"""
        from core.event_bus import Event, EventPriority
        
        perception_data = {
            'tick': world_state.tick,
            'danger_level': world_state.danger_level,
            'objects_count': len(world_state.objects),
            'agents_count': len(world_state.agents),
            'symbols': world_state.symbols,
            'nearest_target': world_state.objects[0] if world_state.objects else None,
            'player_health': world_state.player_health,
            'player_energy': world_state.player_energy,
        }
        
        # Publish perception event
        event = Event(
            type='perception.new_data',
            source='integrated_core',
            data=perception_data,
            priority=EventPriority.HIGH,
        )
        await self.event_bus.publish(event)
        
        return perception_data
    
    async def _retrieve_memories(self, perception_data: Dict[str, Any]) -> List[Any]:
        """Retrieve relevant memories from LTM"""
        if not self.memory_ltm:
            return []
        
        memories = []
        
        # Retrieve by emotional similarity
        if self.current_emotion['valence'] != 0:
            emotional_memories = self.memory_ltm.retrieve_by_emotion(
                target_valence=self.current_emotion['valence'],
                tolerance=0.4,
                limit=3,
            )
            memories.extend(emotional_memories)
        
        # Retrieve recent episodic
        from core.memory.consolidation.memory_consolidation import MemoryType
        recent = self.memory_ltm.retrieve(
            memory_type=MemoryType.EPISODIC,
            limit=5,
            update_access=False,
        )
        memories.extend(recent)
        
        return memories
    
    async def _appraise_emotion(self, perception_data: Dict[str, Any]) -> Dict[str, float]:
        """Appraise situation and update emotion"""
        from core.event_bus import Event, EventPriority
        
        danger = perception_data.get('danger_level', 0)
        health = perception_data.get('player_health', 1.0)
        
        # Simple emotion appraisal
        # High danger → negative valence, high arousal
        # Low health → negative valence, high arousal
        # Rewards nearby → positive valence
        
        valence = -danger * 0.5 - (1 - health) * 0.3
        arousal = danger * 0.6 + (1 - health) * 0.2
        dominance = health * 0.5 - danger * 0.3
        
        # Clamp values
        valence = max(-1, min(1, valence))
        arousal = max(0, min(1, arousal))
        dominance = max(-1, min(1, dominance))
        
        # Determine emotion label
        emotion_label = self._classify_emotion(valence, arousal, dominance)
        
        # Publish emotion event
        emotion_data = {
            'valence': valence,
            'arousal': arousal,
            'dominance': dominance,
            'emotion': emotion_label,
        }
        
        event = Event(
            type='emotion.state_changed',
            source='integrated_core',
            data=emotion_data,
            priority=EventPriority.NORMAL,
        )
        await self.event_bus.publish(event)
        
        self.current_emotion = emotion_data
        return emotion_data
    
    def _classify_emotion(self, valence: float, arousal: float, dominance: float) -> str:
        """Classify PAD values into emotion label"""
        if valence < -0.3 and arousal > 0.5:
            return 'fear' if dominance < 0 else 'anger'
        elif valence < -0.3:
            return 'sadness'
        elif valence > 0.3 and arousal > 0.5:
            return 'excitement'
        elif valence > 0.3:
            return 'calm' if arousal < 0.3 else 'joy'
        else:
            return 'neutral'
    
    async def _select_action(
        self,
        perception_data: Dict[str, Any],
        memories: List[Any],
    ) -> Any:
        """Select action using emotion-aware + somatic selector"""
        from core.event_bus import Event, EventPriority
        from core.planning.action_selection.emotional_action_selector import WorkingMemoryState
        
        # Build WorkingMemoryState for action selector
        wm_state = WorkingMemoryState(
            tick=perception_data.get('tick', 0),
            danger_level=perception_data.get('danger_level', 0),
            nearest_target=perception_data.get('nearest_target'),
            visible_objects=perception_data.get('objects_count', 0),
            visible_agents=perception_data.get('agents_count', 0),
            symbols=perception_data.get('symbols', []),
        )
        
        # Select action
        action_command = self.action_selector.select_action(wm_state)
        
        # Get action name (could be string or enum)
        action_name = action_command.name
        
        # Publish planning event
        event = Event(
            type='planning.action_decided',
            source='integrated_core',
            data={
                'action_name': action_name,
                'action_params': {
                    'danger_level': wm_state.danger_level,
                    'symbols': wm_state.symbols,
                },
                'confidence': action_command.confidence,
                'emotional_influence': action_command.emotional_influence,
                'somatic_bias': getattr(action_command, 'somatic_bias', 0),
                'current_emotion': self.current_emotion.get('emotion', 'neutral'),
            },
            priority=EventPriority.NORMAL,
        )
        await self.event_bus.publish(event)
        
        return action_command
    
    async def _execute_action(
        self,
        action_command: Any,
        world_state: WorldState,
    ) -> ActionResult:
        """Execute action in world"""
        action_name = action_command.name
        
        # If world callback exists, call it
        if self._world_action_callback:
            result = await self._world_action_callback(action_name, world_state)
            return result
        
        # Otherwise simulate simple outcome
        result = ActionResult(
            action_name=action_name,
            success=True,
            outcome_type='action_executed',
            outcome_valence=0.0,
        )
        
        return result
    
    async def _process_outcome(self, action_result: ActionResult) -> None:
        """Process action outcome for learning"""
        # Record outcome in somatic system
        if action_result.outcome_valence != 0:
            self.somatic_system.record_outcome(
                outcome_valence=action_result.outcome_valence,
                outcome_description=action_result.outcome_type,
            )
        
        # Publish outcome event if significant
        if abs(action_result.outcome_valence) > 0.3:
            if action_result.outcome_valence > 0:
                await self.outcome_publisher.reward_found(
                    reward_type=action_result.outcome_type,
                    amount=int(action_result.outcome_valence * 100),
                )
            else:
                await self.outcome_publisher.damage_taken(
                    amount=int(abs(action_result.outcome_valence) * 100),
                    source=action_result.outcome_type,
                )
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def set_world_callback(self, callback: Callable) -> None:
        """Set callback for world action execution"""
        self._world_action_callback = callback
    
    def set_emotion(self, valence: float, arousal: float, dominance: float = 0.0) -> None:
        """Manually set emotion state"""
        self.current_emotion = {
            'valence': max(-1, min(1, valence)),
            'arousal': max(0, min(1, arousal)),
            'dominance': max(-1, min(1, dominance)),
            'emotion': self._classify_emotion(valence, arousal, dominance),
        }
        if self.action_selector:
            self.action_selector.update_emotional_state(self.current_emotion)
    
    def record_outcome(self, outcome_type: str, valence: float) -> None:
        """Manually record an outcome for learning"""
        self.somatic_system.record_outcome(
            outcome_valence=valence,
            outcome_description=outcome_type,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        somatic_stats = self.somatic_handler.get_stats() if self.somatic_handler else {}
        memory_stats = self.memory_consolidator.get_stats() if self.memory_consolidator else {}
        
        avg_cycle_time = 0.0
        if self.cycle_history:
            avg_cycle_time = sum(c.total_time for c in self.cycle_history) / len(self.cycle_history)
        
        return {
            'total_cycles': self.total_cycles,
            'total_actions': self.total_actions,
            'current_tick': self.current_tick,
            'current_emotion': self.current_emotion,
            'current_phase': self.current_phase.value,
            'avg_cycle_time': avg_cycle_time,
            'somatic': somatic_stats,
            'memory': memory_stats,
        }
    
    async def run_cycles(self, world_states: List[WorldState]) -> List[ActionResult]:
        """Run multiple cognitive cycles"""
        results = []
        for world_state in world_states:
            result = await self.cognitive_cycle(world_state)
            results.append(result)
            await asyncio.sleep(self.tick_interval)
        return results


# =========================================================================
# FACTORY FUNCTION
# =========================================================================

async def create_uem_core(
    config: Optional[Dict[str, Any]] = None,
    world_interface: Optional[Any] = None,
    logger: Optional[logging.Logger] = None,
) -> IntegratedUEMCore:
    """Create and start an IntegratedUEMCore"""
    core = IntegratedUEMCore(
        config=config,
        world_interface=world_interface,
        logger=logger,
    )
    await core.start()
    return core

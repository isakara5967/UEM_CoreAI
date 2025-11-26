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
        
        # Runtime state
        self.current_emotion: Dict[str, float] = {
            "valence": 0.0,
            "arousal": 0.5,
            "dominance": 0.0,
        }
        self.last_action: Optional[ActionPlan] = None
        self.last_result: Optional[ActionResult] = None
        self.last_metrics: Optional[CycleMetrics] = None
        
        self.logger.info("[UnifiedCore] Initialized successfully")
    
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
        start = time.perf_counter()
        phase_times: Dict[str, float] = {}
        
        try:
            # Phase 1: PERCEPTION
            t0 = time.perf_counter()
            perception_result = self._phase_perception(world_state)
            phase_times["perception"] = (time.perf_counter() - t0) * 1000
            
            # Phase 2: MEMORY
            t0 = time.perf_counter()
            memory_context = self._phase_memory(perception_result)
            phase_times["memory"] = (time.perf_counter() - t0) * 1000
            
            # Phase 3: SELF
            t0 = time.perf_counter()
            self_state = self._phase_self(perception_result, memory_context, world_state)
            phase_times["self"] = (time.perf_counter() - t0) * 1000
            
            # Phase 4: APPRAISAL
            t0 = time.perf_counter()
            appraisal_result = self._phase_appraisal(perception_result, self_state, world_state)
            phase_times["appraisal"] = (time.perf_counter() - t0) * 1000
            
            # Phase 5: EMPATHY
            t0 = time.perf_counter()
            empathy_result = self._phase_empathy(perception_result, world_state)
            phase_times["empathy"] = (time.perf_counter() - t0) * 1000
            
            # Phase 6: PLANNING (includes ETHMOR check)
            t0 = time.perf_counter()
            action_plan = self._phase_planning(
                self_state, appraisal_result, perception_result, empathy_result
            )
            phase_times["planning"] = (time.perf_counter() - t0) * 1000
            
            # Phase 7: EXECUTION
            t0 = time.perf_counter()
            action_result = await self._phase_execution(action_plan)
            phase_times["execution"] = (time.perf_counter() - t0) * 1000
            
            # Phase 8: LEARNING
            t0 = time.perf_counter()
            await self._phase_learning(self_state, action_plan, action_result)
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
        
        # Metrics
        total_ms = (time.perf_counter() - start) * 1000
        if self.collect_metrics:
            self.last_metrics = CycleMetrics(
                tick=self.tick,
                total_time_ms=total_ms,
                phase_times=phase_times,
            )
        
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
        """Phase 5: Empathy computation (if other agents present)."""
        self.logger.debug(f"[Cycle {self.tick}] Phase: empathy")
        
        if self.empathy is None:
            return None
        
        # Check for agents
        agents = getattr(world_state, 'agents', [])
        if not agents:
            return None
        
        try:
            # Get first agent (v1: single agent)
            other = agents[0]
            
            # Build OtherEntity
            if EMPATHY_AVAILABLE:
                other_entity = OtherEntity(
                    entity_id=other.get('id', 'unknown'),
                    state_vector=(0.5, 0.5, 0.5),  # Inferred
                    valence=other.get('valence', 0.0),
                    relationship=other.get('relation', 0.0),
                )
                return self.empathy.compute(other_entity)
        except Exception as e:
            self.logger.warning(f"[Empathy] Failed: {e}")
        
        return None
    
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
        self.current_emotion = {"valence": 0.0, "arousal": 0.5, "dominance": 0.0}
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

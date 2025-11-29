"""
Integration layer between UnifiedUEMCore and uem_logger.
Automatically logs cognitive cycle data to PostgreSQL.
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
import time

# Import logger
import sys
sys.path.insert(0, '.')
from uem_logger import UEMLogger, LoggerConfig

logger = logging.getLogger("UEM.LoggerIntegration")


@dataclass
class CycleLogData:
    """Data collected during a cognitive cycle for logging."""
    tick: int
    cycle_id: int
    
    # Perception
    novelty_score: Optional[float] = None
    attention_focus: Optional[str] = None
    
    # Emotion
    valence: Optional[float] = None
    arousal: Optional[float] = None
    emotion_label: Optional[str] = None
    
    # Workspace
    coalition_strength: Optional[float] = None
    broadcast_content: Optional[Dict] = None
    
    # Planner
    action_name: Optional[str] = None
    utility: Optional[float] = None
    candidate_plans: Optional[list] = None
    somatic_bias: Optional[float] = None
    
    # ETHMOR
    ethmor_decision: Optional[str] = None
    risk_level: Optional[float] = None
    triggered_rules: Optional[list] = None
    
    # Execution
    success: Optional[bool] = None
    cycle_time_ms: Optional[float] = None


class CoreLoggerIntegration:
    """
    Integrates uem_logger with UnifiedUEMCore.
    
    Usage:
        integration = CoreLoggerIntegration()
        await integration.start()
        
        # In your core cycle:
        integration.on_cycle_start(tick)
        integration.on_perception(novelty=0.7, ...)
        integration.on_emotion(valence=0.3, ...)
        integration.on_planning(action="flee", ...)
        integration.on_ethmor(decision="allow", ...)
        await integration.on_cycle_end(success=True)
    """
    
    def __init__(self, config: Optional[LoggerConfig] = None, enabled: bool = True):
        self.enabled = enabled
        self.logger = UEMLogger(config) if enabled else None
        self.run_id: Optional[str] = None
        self.current_cycle: Optional[CycleLogData] = None
        self._cycle_start_time: float = 0
    
    async def start(self, run_config: Optional[Dict] = None) -> Optional[str]:
        """Start logging session."""
        if not self.enabled:
            return None
        
        connected = await self.logger.connect()
        if not connected:
            logger.warning("Failed to connect to database, logging disabled")
            self.enabled = False
            return None
        
        self.run_id = await self.logger.start_run(config=run_config)
        logger.info(f"Logging started: {self.run_id}")
        return self.run_id
    
    async def stop(self, summary: Optional[Dict] = None) -> None:
        """Stop logging session."""
        if not self.enabled or not self.run_id:
            return
        
        await self.logger.end_run(self.run_id, summary=summary)
        await self.logger.disconnect()
        logger.info(f"Logging stopped: {self.run_id}")
    
    def on_cycle_start(self, tick: int, cycle_id: Optional[int] = None) -> None:
        """Called at the start of each cognitive cycle."""
        if not self.enabled:
            return
        
        self._cycle_start_time = time.perf_counter()
        self.current_cycle = CycleLogData(
            tick=tick,
            cycle_id=cycle_id or tick
        )
    
    def on_perception(self, **kwargs) -> None:
        """Log perception phase data."""
        if not self.enabled or not self.current_cycle:
            return
        
        self.current_cycle.novelty_score = kwargs.get("novelty_score")
        self.current_cycle.attention_focus = kwargs.get("attention_focus")
    
    def on_emotion(self, **kwargs) -> None:
        """Log emotion phase data."""
        if not self.enabled or not self.current_cycle:
            return
        
        self.current_cycle.valence = kwargs.get("valence")
        self.current_cycle.arousal = kwargs.get("arousal")
        self.current_cycle.emotion_label = kwargs.get("label")
    
    def on_workspace(self, **kwargs) -> None:
        """Log workspace phase data."""
        if not self.enabled or not self.current_cycle:
            return
        
        self.current_cycle.coalition_strength = kwargs.get("coalition_strength")
        self.current_cycle.broadcast_content = kwargs.get("broadcast_content")
    
    def on_planning(self, **kwargs) -> None:
        """Log planning phase data."""
        if not self.enabled or not self.current_cycle:
            return
        
        self.current_cycle.action_name = kwargs.get("action")
        self.current_cycle.utility = kwargs.get("utility")
        self.current_cycle.candidate_plans = kwargs.get("candidates")
        self.current_cycle.somatic_bias = kwargs.get("somatic_bias")
    
    def on_ethmor(self, **kwargs) -> None:
        """Log ETHMOR phase data."""
        if not self.enabled or not self.current_cycle:
            return
        
        self.current_cycle.ethmor_decision = kwargs.get("decision")
        self.current_cycle.risk_level = kwargs.get("risk_level")
        self.current_cycle.triggered_rules = kwargs.get("triggered_rules")
    
    async def on_cycle_end(self, success: Optional[bool] = None) -> None:
        """Called at the end of each cognitive cycle. Flushes all data."""
        if not self.enabled or not self.current_cycle or not self.run_id:
            return
        
        cycle = self.current_cycle
        cycle.success = success
        cycle.cycle_time_ms = (time.perf_counter() - self._cycle_start_time) * 1000
        
        # Start cycle in DB
        await self.logger.start_cycle(self.run_id, cycle.cycle_id, cycle.tick)
        
        # Log perception event
        if cycle.novelty_score is not None:
            await self.logger.log_event(
                self.run_id, cycle.cycle_id, "perception", "perception_complete",
                {
                    "novelty_score": cycle.novelty_score,
                    "attention_focus": cycle.attention_focus,
                }
            )
        
        # Log emotion event
        if cycle.valence is not None:
            await self.logger.log_event(
                self.run_id, cycle.cycle_id, "emotion", "emotion_updated",
                {
                    "valence": cycle.valence,
                    "arousal": cycle.arousal,
                    "label": cycle.emotion_label,
                },
                emotion_valence=cycle.valence
            )
        
        # Log workspace event
        if cycle.coalition_strength is not None:
            await self.logger.log_event(
                self.run_id, cycle.cycle_id, "workspace", "broadcast_complete",
                {
                    "coalition_strength": cycle.coalition_strength,
                    "broadcast_content": cycle.broadcast_content,
                }
            )
        
        # Log planning event
        if cycle.action_name is not None:
            await self.logger.log_event(
                self.run_id, cycle.cycle_id, "planner", "action_selected",
                {
                    "action": cycle.action_name,
                    "utility": cycle.utility,
                    "candidates": cycle.candidate_plans,
                    "somatic_bias": cycle.somatic_bias,
                },
                action_name=cycle.action_name
            )
        
        # Log ETHMOR event
        if cycle.ethmor_decision is not None:
            await self.logger.log_event(
                self.run_id, cycle.cycle_id, "ethmor", "ethmor_check",
                {
                    "decision": cycle.ethmor_decision,
                    "risk_level": cycle.risk_level,
                    "triggered_rules": cycle.triggered_rules,
                },
                ethmor_decision=cycle.ethmor_decision
            )
        
        # Log execution/cycle summary event
        await self.logger.log_event(
            self.run_id, cycle.cycle_id, "execution", "cycle_complete",
            {
                "success": cycle.success,
                "cycle_time_ms": cycle.cycle_time_ms,
            },
            success_flag_explicit=cycle.success,
            cycle_time_ms=cycle.cycle_time_ms
        )
        
        # End cycle
        await self.logger.end_cycle(
            self.run_id, cycle.cycle_id,
            summary={
                "action": cycle.action_name,
                "success": cycle.success,
                "time_ms": cycle.cycle_time_ms,
            }
        )
        
        self.current_cycle = None

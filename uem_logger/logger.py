"""Main UEM Logger facade - unified interface for all logging operations."""
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .config import LoggerConfig
from .db import DatabaseManager, get_db_manager
from .runs import RunManager
from .cycles import CycleManager
from .events import EventLogger, EventData
from .fallback import FallbackLogger
from .utils import extract_denorm_fields, now_utc


class UEMLogger:
    """
    Unified logger facade for UEM_CoreAI.
    
    Usage:
        logger = UEMLogger()
        await logger.connect()
        
        run_id = await logger.start_run(config={...})
        await logger.start_cycle(run_id, 1)
        await logger.log_event(run_id, 1, "perception", "novelty_detected", {...})
        await logger.end_cycle(run_id, 1)
        await logger.end_run(run_id)
    """
    
    def __init__(self, config: Optional[LoggerConfig] = None):
        self.config = config or LoggerConfig()
        self.db = DatabaseManager(self.config)
        self.runs = RunManager(self.db)
        self.cycles = CycleManager(self.db)
        self.events = EventLogger(self.db)
        self.fallback = FallbackLogger(self.config.fallback_dir)
        self._use_fallback = False
    
    @property
    def is_connected(self) -> bool:
        return self.db.is_connected
    
    async def connect(self) -> bool:
        """Connect to database."""
        connected = await self.db.connect()
        self._use_fallback = not connected and self.config.fallback_enabled
        return connected
    
    async def disconnect(self) -> None:
        """Disconnect from database."""
        await self.db.disconnect()
    
    # ==================== RUN OPERATIONS ====================
    
    async def start_run(
        self,
        run_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        experiment_id: Optional[str] = None,
        ab_bucket: Optional[str] = None,
        **kwargs
    ) -> str:
        """Start a new run."""
        return await self.runs.start_run(
            run_id=run_id,
            config=config,
            experiment_id=experiment_id,
            ab_bucket=ab_bucket,
            **kwargs
        )
    
    async def end_run(
        self,
        run_id: str,
        status: str = "completed",
        summary: Optional[Dict[str, Any]] = None
    ) -> None:
        """End a run."""
        await self.runs.end_run(run_id, status, summary)
    
    # ==================== CYCLE OPERATIONS ====================
    
    async def start_cycle(
        self,
        run_id: str,
        cycle_id: int,
        tick: Optional[int] = None
    ) -> None:
        """Start a cycle."""
        await self.cycles.start_cycle(run_id, cycle_id, tick)
    
    async def end_cycle(
        self,
        run_id: str,
        cycle_id: int,
        status: str = "completed",
        summary: Optional[Dict[str, Any]] = None
    ) -> None:
        """End a cycle."""
        await self.cycles.end_cycle(run_id, cycle_id, status, summary)
    
    # ==================== EVENT OPERATIONS ====================
    
    async def log_event(
        self,
        run_id: str,
        cycle_id: int,
        module_name: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[int]:
        """Log a single event with automatic denormalization."""
        # Extract denormalized fields
        denorm = {}
        if payload:
            denorm = extract_denorm_fields(payload, module_name)
        
        # Merge with explicit kwargs
        denorm.update(kwargs)
        
        event = EventData(
            run_id=run_id,
            cycle_id=cycle_id,
            event_type=event_type,
            module_name=module_name,
            payload=payload,
            **denorm
        )
        
        if self._use_fallback:
            self.fallback.log_event(event.__dict__)
            return None
        
        return await self.events.log_event(event)
    
    async def log_module_event(
        self,
        run_id: str,
        cycle_id: int,
        module_name: str,
        payload: Dict[str, Any]
    ) -> Optional[int]:
        """Convenience method for logging module output."""
        event_type = f"{module_name}_complete"
        return await self.log_event(run_id, cycle_id, module_name, event_type, payload)
    
    # ==================== QUERY OPERATIONS ====================
    
    async def get_run_summary(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get run with stats."""
        run = await self.runs.get_run(run_id)
        if not run:
            return None
        
        run["cycle_count"] = await self.cycles.get_cycle_count(run_id)
        run["event_count"] = await self.events.get_event_count(run_id)
        return run
    
    async def get_cycle_events(
        self,
        run_id: str,
        cycle_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all events for a cycle."""
        return await self.events.get_events(run_id, cycle_id=cycle_id, limit=limit)
    
    # ==================== HEALTH ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """Full health check."""
        db_health = await self.db.health_check()
        fallback_stats = self.fallback.get_stats()
        
        return {
            "database": db_health,
            "fallback": fallback_stats,
            "using_fallback": self._use_fallback,
        }


# Singleton
_logger: Optional[UEMLogger] = None


def get_logger(config: Optional[LoggerConfig] = None) -> UEMLogger:
    """Get or create singleton logger."""
    global _logger
    if _logger is None:
        _logger = UEMLogger(config)
    return _logger

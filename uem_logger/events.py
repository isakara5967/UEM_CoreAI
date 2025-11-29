"""Event logging for UEM Logger."""
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict

from .db import DatabaseManager, get_db_manager


@dataclass
class EventData:
    """Event data structure matching core.events table."""
    run_id: str
    cycle_id: int
    event_type: str
    module_id: Optional[int] = None
    submodule_id: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None
    # Denormalize columns
    emotion_valence: Optional[float] = None
    action_name: Optional[str] = None
    ethmor_decision: Optional[str] = None
    success_flag_explicit: Optional[bool] = None
    cycle_time_ms: Optional[float] = None
    module_name: Optional[str] = None
    input_quality_score: Optional[float] = None
    input_language: Optional[str] = None
    output_language: Optional[str] = None


class EventLogger:
    """Logs events to PostgreSQL."""
    
    # Module name to ID mapping (cached)
    _module_cache: Dict[str, int] = {}
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db_manager()
        self._batch: List[EventData] = []
    
    async def _get_module_id(self, module_name: str) -> Optional[int]:
        """Get module ID from name (cached)."""
        if module_name in self._module_cache:
            return self._module_cache[module_name]
        
        module_id = await self.db.fetchval(
            "SELECT module_id FROM core.modules WHERE name = $1",
            module_name
        )
        if module_id:
            self._module_cache[module_name] = module_id
        return module_id
    
    async def log_event(self, event: EventData) -> int:
        """Log a single event. Returns event ID."""
        # Resolve module_id if module_name provided
        module_id = event.module_id
        if event.module_name and not module_id:
            module_id = await self._get_module_id(event.module_name)
        
        event_id = await self.db.fetchval(
            """
            INSERT INTO core.events (
                run_id, cycle_id, module_id, submodule_id, event_type, payload,
                emotion_valence, action_name, ethmor_decision, success_flag_explicit,
                cycle_time_ms, module_name, input_quality_score, input_language, output_language
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            RETURNING id
            """,
            event.run_id,
            event.cycle_id,
            module_id,
            event.submodule_id,
            event.event_type,
            json.dumps(event.payload) if event.payload else None,
            event.emotion_valence,
            event.action_name,
            event.ethmor_decision,
            event.success_flag_explicit,
            event.cycle_time_ms,
            event.module_name,
            event.input_quality_score,
            event.input_language,
            event.output_language,
        )
        return event_id
    
    async def log_events_batch(self, events: List[EventData]) -> int:
        """Log multiple events in batch. Returns count."""
        if not events:
            return 0
        
        # Prepare data
        records = []
        for e in events:
            module_id = e.module_id
            if e.module_name and not module_id:
                module_id = await self._get_module_id(e.module_name)
            
            records.append((
                e.run_id, e.cycle_id, module_id, e.submodule_id, e.event_type,
                json.dumps(e.payload) if e.payload else None,
                e.emotion_valence, e.action_name, e.ethmor_decision,
                e.success_flag_explicit, e.cycle_time_ms, e.module_name,
                e.input_quality_score, e.input_language, e.output_language,
            ))
        
        await self.db.execute_many(
            """
            INSERT INTO core.events (
                run_id, cycle_id, module_id, submodule_id, event_type, payload,
                emotion_valence, action_name, ethmor_decision, success_flag_explicit,
                cycle_time_ms, module_name, input_quality_score, input_language, output_language
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            """,
            records
        )
        return len(records)
    
    async def get_events(
        self,
        run_id: str,
        cycle_id: Optional[int] = None,
        event_type: Optional[str] = None,
        module_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query events with filters."""
        conditions = ["run_id = $1"]
        params = [run_id]
        param_idx = 2
        
        if cycle_id is not None:
            conditions.append(f"cycle_id = ${param_idx}")
            params.append(cycle_id)
            param_idx += 1
        
        if event_type:
            conditions.append(f"event_type = ${param_idx}")
            params.append(event_type)
            param_idx += 1
        
        if module_name:
            conditions.append(f"module_name = ${param_idx}")
            params.append(module_name)
            param_idx += 1
        
        params.append(limit)
        
        query = f"""
            SELECT * FROM core.events 
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp DESC
            LIMIT ${param_idx}
        """
        
        rows = await self.db.fetch(query, *params)
        return [dict(r) for r in rows]
    
    async def get_event_count(self, run_id: str) -> int:
        """Get total event count for a run."""
        return await self.db.fetchval(
            "SELECT COUNT(*) FROM core.events WHERE run_id = $1",
            run_id
        )

"""Cycle management for UEM Logger."""
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from .db import DatabaseManager, get_db_manager


class CycleManager:
    """Manages cognitive cycle lifecycle."""
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db_manager()
    
    async def start_cycle(
        self,
        run_id: str,
        cycle_id: int,
        tick: Optional[int] = None,
    ) -> None:
        """Start a new cycle."""
        await self.db.execute(
            """
            INSERT INTO core.cycles (run_id, cycle_id, tick)
            VALUES ($1, $2, $3)
            ON CONFLICT (run_id, cycle_id) DO NOTHING
            """,
            run_id,
            cycle_id,
            tick or cycle_id,
        )
    
    async def end_cycle(
        self,
        run_id: str,
        cycle_id: int,
        status: str = "completed",
        summary: Optional[Dict[str, Any]] = None,
    ) -> None:
        """End a cycle."""
        await self.db.execute(
            """
            UPDATE core.cycles 
            SET ended_at = NOW(), status = $3, summary = $4
            WHERE run_id = $1 AND cycle_id = $2
            """,
            run_id,
            cycle_id,
            status,
            json.dumps(summary) if summary else None,
        )
    
    async def get_cycle(self, run_id: str, cycle_id: int) -> Optional[Dict[str, Any]]:
        """Get cycle details."""
        row = await self.db.fetchrow(
            "SELECT * FROM core.cycles WHERE run_id = $1 AND cycle_id = $2",
            run_id,
            cycle_id
        )
        return dict(row) if row else None
    
    async def get_run_cycles(self, run_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all cycles for a run."""
        rows = await self.db.fetch(
            """
            SELECT * FROM core.cycles 
            WHERE run_id = $1 
            ORDER BY cycle_id DESC 
            LIMIT $2
            """,
            run_id,
            limit
        )
        return [dict(r) for r in rows]
    
    async def get_cycle_count(self, run_id: str) -> int:
        """Get total cycle count for a run."""
        return await self.db.fetchval(
            "SELECT COUNT(*) FROM core.cycles WHERE run_id = $1",
            run_id
        )

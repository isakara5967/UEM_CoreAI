"""Run management for UEM Logger."""
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from .db import DatabaseManager, get_db_manager


class RunManager:
    """Manages UEM run lifecycle."""
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db_manager()
    
    @staticmethod
    def generate_run_id() -> str:
        """Generate unique run ID."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        short_uuid = uuid.uuid4().hex[:8]
        return f"run_{ts}_{short_uuid}"
    
    async def start_run(
        self,
        run_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        experiment_id: Optional[str] = None,
        config_id: Optional[str] = None,
        ab_bucket: Optional[str] = None,
        environment_profile: Optional[Dict[str, Any]] = None,
        primary_language: Optional[str] = None,
    ) -> str:
        """Start a new run and return run_id."""
        run_id = run_id or self.generate_run_id()
        
        await self.db.execute(
            """
            INSERT INTO core.runs 
                (run_id, config, experiment_id, config_id, ab_bucket, environment_profile, primary_language)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            run_id,
            json.dumps(config) if config else None,
            experiment_id,
            config_id,
            ab_bucket,
            json.dumps(environment_profile) if environment_profile else None,
            primary_language,
        )
        return run_id
    
    async def end_run(
        self,
        run_id: str,
        status: str = "completed",
        summary: Optional[Dict[str, Any]] = None,
    ) -> None:
        """End a run."""
        await self.db.execute(
            """
            UPDATE core.runs 
            SET ended_at = NOW(), status = $2, summary = $3
            WHERE run_id = $1
            """,
            run_id,
            status,
            json.dumps(summary) if summary else None,
        )
    
    async def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get run details."""
        row = await self.db.fetchrow(
            "SELECT * FROM core.runs WHERE run_id = $1",
            run_id
        )
        return dict(row) if row else None
    
    async def get_active_runs(self) -> list:
        """Get all running runs."""
        rows = await self.db.fetch(
            "SELECT * FROM core.runs WHERE status = 'running' ORDER BY started_at DESC"
        )
        return [dict(r) for r in rows]

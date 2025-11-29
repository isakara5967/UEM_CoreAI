"""Experiment CRUD operations for database."""
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from .db import DatabaseManager, get_db_manager


class ExperimentRepository:
    """
    Database operations for experiments table.
    
    Usage:
        repo = ExperimentRepository(db)
        await repo.create(experiment_id="exp_001", name="Test", ...)
    """
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db_manager()
    
    async def create(
        self,
        experiment_id: str,
        name: str,
        description: Optional[str] = None,
        hypothesis: Optional[str] = None,
        owner: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        status: str = "planned"
    ) -> str:
        """Create a new experiment."""
        await self.db.execute(
            """
            INSERT INTO core.experiments 
                (experiment_id, name, description, hypothesis, owner, config, tags, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (experiment_id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                updated_at = NOW()
            """,
            experiment_id,
            name,
            description,
            hypothesis,
            owner,
            json.dumps(config) if config else None,
            tags,
            status
        )
        return experiment_id
    
    async def get(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment by ID."""
        row = await self.db.fetchrow(
            "SELECT * FROM core.experiments WHERE experiment_id = $1",
            experiment_id
        )
        return dict(row) if row else None
    
    async def list(
        self,
        status: Optional[str] = None,
        owner: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List experiments with optional filters."""
        conditions = []
        params = []
        param_idx = 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        if owner:
            conditions.append(f"owner = ${param_idx}")
            params.append(owner)
            param_idx += 1
        
        params.append(limit)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f"""
            SELECT * FROM core.experiments 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx}
        """
        
        rows = await self.db.fetch(query, *params)
        return [dict(r) for r in rows]
    
    async def update_status(
        self,
        experiment_id: str,
        status: str,
        start: bool = False,
        end: bool = False
    ) -> None:
        """Update experiment status."""
        updates = ["status = $2", "updated_at = NOW()"]
        params = [experiment_id, status]
        
        if start:
            updates.append("start_ts = NOW()")
        if end:
            updates.append("end_ts = NOW()")
        
        await self.db.execute(
            f"UPDATE core.experiments SET {', '.join(updates)} WHERE experiment_id = $1",
            *params
        )
    
    async def start(self, experiment_id: str) -> None:
        """Start an experiment."""
        await self.update_status(experiment_id, "running", start=True)
    
    async def complete(self, experiment_id: str) -> None:
        """Mark experiment as completed."""
        await self.update_status(experiment_id, "completed", end=True)
    
    async def pause(self, experiment_id: str) -> None:
        """Pause an experiment."""
        await self.update_status(experiment_id, "paused")
    
    async def delete(self, experiment_id: str) -> bool:
        """Delete an experiment."""
        result = await self.db.execute(
            "DELETE FROM core.experiments WHERE experiment_id = $1",
            experiment_id
        )
        return "DELETE 1" in result
    
    async def add_tags(self, experiment_id: str, tags: List[str]) -> None:
        """Add tags to experiment."""
        await self.db.execute(
            """
            UPDATE core.experiments 
            SET tags = array_cat(COALESCE(tags, '{}'), $2), updated_at = NOW()
            WHERE experiment_id = $1
            """,
            experiment_id,
            tags
        )
    
    async def get_active_experiments(self) -> List[Dict[str, Any]]:
        """Get all active (running) experiments."""
        return await self.list(status="running")

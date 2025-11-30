"""Config snapshot management for reproducibility."""
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from .db import DatabaseManager, get_db_manager


def generate_config_id(config: Dict[str, Any], prefix: str = "cfg") -> str:
    """Generate unique config ID from content."""
    json_str = json.dumps(config, sort_keys=True, default=str)
    hash_val = hashlib.sha256(json_str.encode()).hexdigest()[:12]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{prefix}_{ts}_{hash_val}"


def generate_checksum(config: Dict[str, Any]) -> str:
    """Generate checksum for config verification."""
    json_str = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()


class ConfigSnapshotRepository:
    """
    Database operations for config_snapshots table.
    
    Enables reproducibility by storing complete config state.
    
    Usage:
        repo = ConfigSnapshotRepository(db)
        config_id = await repo.create(config_blob={...}, core_version="1.0")
    """
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db_manager()
    
    async def create(
        self,
        config_blob: Dict[str, Any],
        core_version: str,
        model_version: Optional[str] = None,
        policy_set_id: Optional[str] = None,
        ethmor_rules_version: Optional[str] = None,
        description: Optional[str] = None,
        config_id: Optional[str] = None
    ) -> str:
        """Create a config snapshot."""
        config_id = config_id or generate_config_id(config_blob)
        checksum = generate_checksum(config_blob)
        
        await self.db.execute(
            """
            INSERT INTO core.config_snapshots 
                (config_id, core_version, model_version, policy_set_id, 
                 ethmor_rules_version, config_blob, checksum, description)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (config_id) DO NOTHING
            """,
            config_id,
            core_version,
            model_version,
            policy_set_id,
            ethmor_rules_version,
            json.dumps(config_blob),
            checksum,
            description
        )
        return config_id
    
    async def get(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get config snapshot by ID."""
        row = await self.db.fetchrow(
            "SELECT * FROM core.config_snapshots WHERE config_id = $1",
            config_id
        )
        return dict(row) if row else None
    
    async def get_by_checksum(self, checksum: str) -> Optional[Dict[str, Any]]:
        """Get config by checksum (find duplicates)."""
        row = await self.db.fetchrow(
            "SELECT * FROM core.config_snapshots WHERE checksum = $1",
            checksum
        )
        return dict(row) if row else None
    
    async def list(
        self,
        core_version: Optional[str] = None,
        policy_set_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List config snapshots."""
        conditions = []
        params = []
        param_idx = 1
        
        if core_version:
            conditions.append(f"core_version = ${param_idx}")
            params.append(core_version)
            param_idx += 1
        
        if policy_set_id:
            conditions.append(f"policy_set_id = ${param_idx}")
            params.append(policy_set_id)
            param_idx += 1
        
        params.append(limit)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f"""
            SELECT config_id, created_ts, core_version, model_version, 
                   policy_set_id, checksum, description
            FROM core.config_snapshots 
            {where_clause}
            ORDER BY created_ts DESC
            LIMIT ${param_idx}
        """
        
        rows = await self.db.fetch(query, *params)
        return [dict(r) for r in rows]
    
    async def verify(self, config_id: str) -> bool:
        """Verify config integrity using checksum."""
        row = await self.db.fetchrow(
            "SELECT config_blob, checksum FROM core.config_snapshots WHERE config_id = $1",
            config_id
        )
        
        if not row:
            return False
        
        config_blob = row["config_blob"]
        stored_checksum = row["checksum"]
        
        # Handle JSONB return
        if isinstance(config_blob, str):
            config_blob = json.loads(config_blob)
        
        computed_checksum = generate_checksum(config_blob)
        return computed_checksum == stored_checksum
    
    async def find_or_create(
        self,
        config_blob: Dict[str, Any],
        core_version: str,
        **kwargs
    ) -> str:
        """Find existing config by checksum or create new."""
        checksum = generate_checksum(config_blob)
        
        existing = await self.get_by_checksum(checksum)
        if existing:
            return existing["config_id"]
        
        return await self.create(
            config_blob=config_blob,
            core_version=core_version,
            **kwargs
        )
    
    async def get_latest(self, core_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get most recent config snapshot."""
        configs = await self.list(core_version=core_version, limit=1)
        return configs[0] if configs else None

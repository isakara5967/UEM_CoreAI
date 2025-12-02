"""
PostgreSQL Storage Implementation with pgvector support.
Updated: 16D vectors, state_before/after for events
"""

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

try:
    import asyncpg
except ImportError:
    asyncpg = None

from .base import BaseStorage, StoredEvent, StoredSnapshot, STATE_VECTOR_SIZE, _ensure_16d


class PostgresStorage(BaseStorage):
    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 5,
        default_agent_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs,
    ):
        super().__init__()
        if asyncpg is None:
            raise ImportError("asyncpg required")
        self._database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://uem:uem_secure_password@localhost:5432/uem_memory"
        )
        self._pool_size = pool_size
        self._pool = None
        self._default_agent_id = agent_id or default_agent_id or "00000000-0000-0000-0000-000000000001"
        self._loop = None
    
    def _get_loop(self):
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
            return self._loop
    
    def _run_sync(self, coro):
        loop = self._get_loop()
        return loop.run_until_complete(coro)
    
    async def _get_pool(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self._database_url, min_size=1, max_size=self._pool_size
            )
        return self._pool
    
    async def _ensure_tables(self):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS events (
                    id BIGSERIAL PRIMARY KEY,
                    agent_id UUID NOT NULL,
                    session_id UUID,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    tick BIGINT NOT NULL DEFAULT 0,
                    category VARCHAR(20) DEFAULT 'WORLD',
                    source VARCHAR(50) NOT NULL,
                    target VARCHAR(50) NOT NULL,
                    state_before vector({STATE_VECTOR_SIZE}),
                    effect vector({STATE_VECTOR_SIZE}) NOT NULL,
                    state_after vector({STATE_VECTOR_SIZE}),
                    salience REAL DEFAULT 0.5,
                    metadata JSONB DEFAULT '{{}}'
                );
            """)
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id BIGSERIAL PRIMARY KEY,
                    agent_id UUID NOT NULL,
                    session_id UUID,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    tick BIGINT NOT NULL DEFAULT 0,
                    state_vector vector({STATE_VECTOR_SIZE}) NOT NULL,
                    consolidation_level INTEGER DEFAULT 0,
                    last_accessed TIMESTAMPTZ DEFAULT NOW(),
                    access_count INTEGER DEFAULT 0,
                    strength REAL DEFAULT 1.0,
                    salience REAL DEFAULT 0.5,
                    goals JSONB DEFAULT '[]',
                    metadata JSONB DEFAULT '{{}}'
                );
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_events_agent_tick ON events (agent_id, tick DESC);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_agent_tick ON snapshots (agent_id, tick DESC);")
    
    def initialize(self):
        self._run_sync(self._ensure_tables())
    
    def store_event(self, event: StoredEvent) -> int:
        return self._run_sync(self._store_event_async(event))
    
    async def _store_event_async(self, event: StoredEvent) -> int:
        pool = await self._get_pool()
        if not event.agent_id:
            event.agent_id = self._default_agent_id
        if event.timestamp is None:
            event.timestamp = datetime.now()
        
        sb = f"[{','.join(str(x) for x in event.state_before)}]"
        ef = f"[{','.join(str(x) for x in event.effect)}]"
        sa = f"[{','.join(str(x) for x in event.state_after)}]"
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO events (
                    agent_id, session_id, timestamp, tick, category,
                    source, target, state_before, effect, state_after,
                    salience, metadata
                ) VALUES (
                    $1::uuid, $2::uuid, $3, $4, $5,
                    $6, $7, $8::vector, $9::vector, $10::vector,
                    $11, $12::jsonb
                ) RETURNING id
            """,
                event.agent_id, event.session_id, event.timestamp,
                event.tick, event.category, event.source, event.target,
                sb, ef, sa, event.salience, json.dumps(event.metadata or {})
            )
            self._stats['events_stored'] += 1
            return row['id']
    
    def store_snapshot(self, snapshot: StoredSnapshot) -> int:
        return self._run_sync(self._store_snapshot_async(snapshot))
    
    async def _store_snapshot_async(self, snapshot: StoredSnapshot) -> int:
        pool = await self._get_pool()
        if not snapshot.agent_id:
            snapshot.agent_id = self._default_agent_id
        if snapshot.timestamp is None:
            snapshot.timestamp = datetime.now()
        if snapshot.last_accessed is None:
            snapshot.last_accessed = snapshot.timestamp
        
        vec = f"[{','.join(str(x) for x in snapshot.state_vector)}]"
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO snapshots (
                    agent_id, session_id, timestamp, tick, state_vector,
                    consolidation_level, last_accessed, access_count,
                    strength, salience, goals, metadata
                ) VALUES (
                    $1::uuid, $2::uuid, $3, $4, $5::vector,
                    $6, $7, $8, $9, $10, $11::jsonb, $12::jsonb
                ) RETURNING id
            """,
                snapshot.agent_id, snapshot.session_id, snapshot.timestamp,
                snapshot.tick, vec, snapshot.consolidation_level,
                snapshot.last_accessed, snapshot.access_count,
                snapshot.strength, snapshot.salience,
                json.dumps(snapshot.goals or []), json.dumps(snapshot.metadata or {})
            )
            self._stats['snapshots_stored'] += 1
            return row['id']
    
    def get_recent_events(self, n: int = 10, agent_id: Optional[str] = None) -> List[StoredEvent]:
        return self._run_sync(self._get_recent_events_async(n, agent_id))
    
    async def _get_recent_events_async(self, n: int, agent_id: Optional[str]) -> List[StoredEvent]:
        self._stats['queries'] += 1
        pool = await self._get_pool()
        aid = agent_id or self._default_agent_id
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM events WHERE agent_id = $1::uuid ORDER BY tick DESC LIMIT $2",
                aid, n
            )
            return [self._row_to_event(r) for r in rows]
    
    def get_recent_snapshots(self, n: int = 10, agent_id: Optional[str] = None) -> List[StoredSnapshot]:
        return self._run_sync(self._get_recent_snapshots_async(n, agent_id))
    
    async def _get_recent_snapshots_async(self, n: int, agent_id: Optional[str]) -> List[StoredSnapshot]:
        self._stats['queries'] += 1
        pool = await self._get_pool()
        aid = agent_id or self._default_agent_id
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM snapshots WHERE agent_id = $1::uuid ORDER BY tick DESC LIMIT $2",
                aid, n
            )
            return [self._row_to_snapshot(r) for r in rows]
    
    def find_similar_snapshots(
        self, state_vector: Tuple[float, ...], limit: int = 5,
        tolerance: float = 0.5, agent_id: Optional[str] = None,
        allow_cross_agent: bool = False
    ) -> List[Dict[str, Any]]:
        return self._run_sync(
            self._find_similar_async(state_vector, limit, tolerance, agent_id, allow_cross_agent)
        )
    
    async def _find_similar_async(
        self, state_vector, limit, tolerance, agent_id, allow_cross_agent
    ) -> List[Dict[str, Any]]:
        self._stats['queries'] += 1
        pool = await self._get_pool()
        state_vector = _ensure_16d(state_vector)
        vec = f"[{','.join(str(x) for x in state_vector)}]"
        
        async with pool.acquire() as conn:
            if allow_cross_agent:
                rows = await conn.fetch("""
                    SELECT *, state_vector <-> $1::vector AS distance FROM snapshots
                    WHERE state_vector <-> $1::vector < $2 ORDER BY distance LIMIT $3
                """, vec, tolerance, limit)
            else:
                aid = agent_id or self._default_agent_id
                rows = await conn.fetch("""
                    SELECT *, state_vector <-> $1::vector AS distance FROM snapshots
                    WHERE agent_id = $2::uuid AND state_vector <-> $1::vector < $3
                    ORDER BY distance LIMIT $4
                """, vec, aid, tolerance, limit)
            
            return [{'snapshot': self._row_to_snapshot(r), 'distance': r['distance'],
                     'similarity': 1.0/(1.0+r['distance'])} for r in rows]
    
    def close(self):
        if self._pool:
            self._run_sync(self._pool.close())
            self._pool = None
    
    def _parse_vec(self, v):
        if v is None:
            return (0.0,) * STATE_VECTOR_SIZE
        if isinstance(v, str):
            return tuple(float(x) for x in v.strip('[]').split(','))
        return tuple(v)
    
    def _row_to_event(self, row) -> StoredEvent:
        return StoredEvent(
            id=row['id'], agent_id=str(row['agent_id']),
            session_id=str(row['session_id']) if row['session_id'] else None,
            timestamp=row['timestamp'], tick=row['tick'],
            category=row['category'], source=row['source'], target=row['target'],
            state_before=self._parse_vec(row.get('state_before')),
            effect=self._parse_vec(row['effect']),
            state_after=self._parse_vec(row.get('state_after')),
            salience=row['salience'], metadata=row['metadata'] or {}
        )
    
    def _row_to_snapshot(self, row) -> StoredSnapshot:
        return StoredSnapshot(
            id=row['id'], agent_id=str(row['agent_id']),
            session_id=str(row['session_id']) if row['session_id'] else None,
            timestamp=row['timestamp'], tick=row['tick'],
            state_vector=self._parse_vec(row['state_vector']),
            consolidation_level=row['consolidation_level'],
            last_accessed=row['last_accessed'], access_count=row['access_count'],
            strength=row['strength'], salience=row['salience'],
            goals=row['goals'] or [], metadata=row['metadata'] or {}
        )
    
    def health_check(self) -> bool:
        try:
            return self._run_sync(self._health_check_async())
        except:
            return False
    
    async def _health_check_async(self) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval("SELECT 1") == 1
    
    def get_stats(self) -> Dict[str, Any]:
        stats = super().get_stats()
        stats['database_url'] = self._database_url.split('@')[-1]
        stats['pool_size'] = self._pool_size
        stats['connected'] = self._pool is not None
        return stats

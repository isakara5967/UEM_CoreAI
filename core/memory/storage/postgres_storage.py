"""
PostgresStorage - PostgreSQL + pgvector storage implementation.
Production için. Kalıcı, vector search, multi-agent desteği.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import os

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

from .base import BaseStorage, StoredEvent, StoredSnapshot


class PostgresStorage(BaseStorage):
    """
    PostgreSQL + pgvector storage implementation.
    
    Use cases:
        - Production deployment
        - Multi-agent systems
        - Vector similarity search
        - Persistent storage with ACID guarantees
    
    Requirements:
        - PostgreSQL 16+
        - pgvector extension
        - asyncpg library
    """
    
    def __init__(
        self, 
        agent_id: Optional[str] = None,
        database_url: Optional[str] = None,
        pool_size: int = 5
    ):
        if not HAS_ASYNCPG:
            raise ImportError("asyncpg required: pip install asyncpg")
        
        super().__init__(agent_id)
        
        self._database_url = database_url or os.getenv(
            'DATABASE_URL', 
            'postgresql://uem:uem_secret_123@localhost:5432/uem_memory'
        )
        self._pool_size = pool_size
        self._pool: Optional[asyncpg.Pool] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    # ============== Connection Management ==============
    
    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._loop is None or self._loop.is_closed():
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
            return self._loop
    
    def _run_sync(self, coro):
        """Run coroutine synchronously."""
        loop = self._get_loop()
        return loop.run_until_complete(coro)
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self._database_url,
                min_size=1,
                max_size=self._pool_size
            )
        return self._pool
    
    async def _ensure_tables(self) -> None:
        """Create tables if they don't exist."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            # Enable pgvector
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id BIGSERIAL PRIMARY KEY,
                    agent_id UUID NOT NULL,
                    session_id UUID,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    tick BIGINT NOT NULL DEFAULT 0,
                    category VARCHAR(20) DEFAULT 'WORLD',
                    source VARCHAR(50) NOT NULL,
                    target VARCHAR(50) NOT NULL,
                    effect vector(8) NOT NULL,
                    salience REAL DEFAULT 0.5,
                    emotion_valence REAL,
                    emotion_arousal REAL,
                    metadata JSONB DEFAULT '{}'
                );
            """)
            
            # Snapshots table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id BIGSERIAL PRIMARY KEY,
                    agent_id UUID NOT NULL,
                    session_id UUID,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    tick BIGINT NOT NULL DEFAULT 0,
                    state_vector vector(8) NOT NULL,
                    consolidation_level INTEGER DEFAULT 0,
                    last_accessed TIMESTAMPTZ DEFAULT NOW(),
                    access_count INTEGER DEFAULT 0,
                    strength REAL DEFAULT 1.0,
                    salience REAL DEFAULT 0.5,
                    goals JSONB DEFAULT '[]',
                    metadata JSONB DEFAULT '{}'
                );
            """)
            
            # Indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_agent_tick 
                ON events (agent_id, tick DESC);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_agent_tick 
                ON snapshots (agent_id, tick DESC);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_vector 
                ON snapshots USING ivfflat (state_vector vector_l2_ops) WITH (lists = 100);
            """)
    
    def initialize(self) -> None:
        """Initialize database (create tables)."""
        self._run_sync(self._ensure_tables())
    
    # ============== Core Methods ==============
    
    def store_event(self, event: StoredEvent) -> int:
        """Store event in PostgreSQL."""
        return self._run_sync(self._store_event_async(event))
    
    async def _store_event_async(self, event: StoredEvent) -> int:
        pool = await self._get_pool()
        
        if not event.agent_id:
            event.agent_id = self._default_agent_id
        if event.timestamp is None:
            event.timestamp = datetime.now()
        
        effect_str = f"[{','.join(str(x) for x in event.effect)}]"
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO events (
                    agent_id, session_id, timestamp, tick, category,
                    source, target, effect, salience, 
                    emotion_valence, emotion_arousal, metadata
                ) VALUES (
                    $1::uuid, $2::uuid, $3, $4, $5,
                    $6, $7, $8::vector, $9,
                    $10, $11, $12::jsonb
                ) RETURNING id
            """,
                event.agent_id,
                event.session_id,
                event.timestamp,
                event.tick,
                event.category,
                event.source,
                event.target,
                effect_str,
                event.salience,
                event.emotion_valence,
                event.emotion_arousal,
                json.dumps(event.metadata or {})
            )
            
            self._stats['events_stored'] += 1
            return row['id']
    
    def store_snapshot(self, snapshot: StoredSnapshot) -> int:
        """Store snapshot in PostgreSQL."""
        return self._run_sync(self._store_snapshot_async(snapshot))
    
    async def _store_snapshot_async(self, snapshot: StoredSnapshot) -> int:
        pool = await self._get_pool()
        
        if not snapshot.agent_id:
            snapshot.agent_id = self._default_agent_id
        if snapshot.timestamp is None:
            snapshot.timestamp = datetime.now()
        if snapshot.last_accessed is None:
            snapshot.last_accessed = snapshot.timestamp
        
        vector_str = f"[{','.join(str(x) for x in snapshot.state_vector)}]"
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO snapshots (
                    agent_id, session_id, timestamp, tick, state_vector,
                    consolidation_level, last_accessed, access_count,
                    strength, salience, goals, metadata
                ) VALUES (
                    $1::uuid, $2::uuid, $3, $4, $5::vector,
                    $6, $7, $8,
                    $9, $10, $11::jsonb, $12::jsonb
                ) RETURNING id
            """,
                snapshot.agent_id,
                snapshot.session_id,
                snapshot.timestamp,
                snapshot.tick,
                vector_str,
                snapshot.consolidation_level,
                snapshot.last_accessed,
                snapshot.access_count,
                snapshot.strength,
                snapshot.salience,
                json.dumps(snapshot.goals or []),
                json.dumps(snapshot.metadata or {})
            )
            
            self._stats['snapshots_stored'] += 1
            return row['id']
    
    def get_recent_events(
        self, 
        n: int = 10, 
        agent_id: Optional[str] = None
    ) -> List[StoredEvent]:
        """Get recent events from PostgreSQL."""
        return self._run_sync(self._get_recent_events_async(n, agent_id))
    
    async def _get_recent_events_async(
        self, n: int, agent_id: Optional[str]
    ) -> List[StoredEvent]:
        self._stats['queries'] += 1
        pool = await self._get_pool()
        resolved_agent = self._resolve_agent_id(agent_id)
        
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM events 
                WHERE agent_id = $1::uuid
                ORDER BY tick DESC, timestamp DESC
                LIMIT $2
            """, resolved_agent, n)
            
            return [self._row_to_event(row) for row in rows]
    
    def get_recent_snapshots(
        self, 
        n: int = 10, 
        agent_id: Optional[str] = None
    ) -> List[StoredSnapshot]:
        """Get recent snapshots from PostgreSQL."""
        return self._run_sync(self._get_recent_snapshots_async(n, agent_id))
    
    async def _get_recent_snapshots_async(
        self, n: int, agent_id: Optional[str]
    ) -> List[StoredSnapshot]:
        self._stats['queries'] += 1
        pool = await self._get_pool()
        resolved_agent = self._resolve_agent_id(agent_id)
        
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM snapshots 
                WHERE agent_id = $1::uuid
                ORDER BY tick DESC, timestamp DESC
                LIMIT $2
            """, resolved_agent, n)
            
            return [self._row_to_snapshot(row) for row in rows]
    
    def get_similar_experiences(
        self,
        state_vector: Tuple[float, ...],
        limit: int = 5,
        tolerance: float = 0.3,
        agent_id: Optional[str] = None,
        allow_cross_agent: bool = False
    ) -> List[StoredSnapshot]:
        """Find similar experiences using pgvector."""
        return self._run_sync(self._get_similar_async(
            state_vector, limit, tolerance, agent_id, allow_cross_agent
        ))
    
    async def _get_similar_async(
        self,
        state_vector: Tuple[float, ...],
        limit: int,
        tolerance: float,
        agent_id: Optional[str],
        allow_cross_agent: bool
    ) -> List[StoredSnapshot]:
        self._stats['queries'] += 1
        pool = await self._get_pool()
        resolved_agent = self._resolve_agent_id(agent_id)
        
        vector_str = f"[{','.join(str(x) for x in state_vector)}]"
        
        async with pool.acquire() as conn:
            if allow_cross_agent:
                rows = await conn.fetch("""
                    SELECT *, state_vector <-> $1::vector AS distance
                    FROM snapshots
                    WHERE state_vector <-> $1::vector < $2
                    ORDER BY distance
                    LIMIT $3
                """, vector_str, tolerance, limit)
            else:
                rows = await conn.fetch("""
                    SELECT *, state_vector <-> $1::vector AS distance
                    FROM snapshots
                    WHERE agent_id = $2::uuid
                    AND state_vector <-> $1::vector < $3
                    ORDER BY distance
                    LIMIT $4
                """, vector_str, resolved_agent, tolerance, limit)
            
            # Update access stats
            if rows:
                ids = [row['id'] for row in rows]
                await conn.execute("""
                    UPDATE snapshots 
                    SET access_count = access_count + 1,
                        last_accessed = NOW()
                    WHERE id = ANY($1)
                """, ids)
            
            return [self._row_to_snapshot(row) for row in rows]
    
    def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            self._run_sync(self._pool.close())
            self._pool = None
    
    # ============== Row Conversion ==============
    
    def _row_to_event(self, row) -> StoredEvent:
        effect = row['effect']
        if isinstance(effect, str):
            effect = tuple(float(x) for x in effect.strip('[]').split(','))
        else:
            effect = tuple(effect)
        
        return StoredEvent(
            id=row['id'],
            agent_id=str(row['agent_id']),
            session_id=str(row['session_id']) if row['session_id'] else None,
            timestamp=row['timestamp'],
            tick=row['tick'],
            category=row['category'],
            source=row['source'],
            target=row['target'],
            effect=effect,
            salience=row['salience'],
            emotion_valence=row['emotion_valence'],
            emotion_arousal=row['emotion_arousal'],
            metadata=row['metadata'] or {}
        )
    
    def _row_to_snapshot(self, row) -> StoredSnapshot:
        state_vector = row['state_vector']
        if isinstance(state_vector, str):
            state_vector = tuple(float(x) for x in state_vector.strip('[]').split(','))
        else:
            state_vector = tuple(state_vector)
        
        return StoredSnapshot(
            id=row['id'],
            agent_id=str(row['agent_id']),
            session_id=str(row['session_id']) if row['session_id'] else None,
            timestamp=row['timestamp'],
            tick=row['tick'],
            state_vector=state_vector,
            consolidation_level=row['consolidation_level'],
            last_accessed=row['last_accessed'],
            access_count=row['access_count'],
            strength=row['strength'],
            salience=row['salience'],
            goals=row['goals'] or [],
            metadata=row['metadata'] or {}
        )
    
    # ============== Additional Methods ==============
    
    def health_check(self) -> bool:
        """Check PostgreSQL connection."""
        try:
            return self._run_sync(self._health_check_async())
        except Exception:
            return False
    
    async def _health_check_async(self) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Extended stats including DB info."""
        stats = super().get_stats()
        stats['database_url'] = self._database_url.split('@')[-1]  # Hide credentials
        stats['pool_size'] = self._pool_size
        stats['connected'] = self._pool is not None
        return stats

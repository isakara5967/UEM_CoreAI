"""Database connection pool management."""
import asyncio
import logging
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

from .config import LoggerConfig

logger = logging.getLogger("uem_logger.db")


class DatabaseManager:
    """Manages async PostgreSQL connection pool."""
    
    def __init__(self, config: Optional[LoggerConfig] = None):
        self.config = config or LoggerConfig()
        self._pool: Optional[asyncpg.Pool] = None
        self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if pool is active."""
        return self._connected and self._pool is not None
    
    async def connect(self) -> bool:
        """Initialize connection pool."""
        if not ASYNCPG_AVAILABLE:
            logger.error("asyncpg not installed")
            return False
        
        if self._pool is not None:
            return True
        
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self.config.asyncpg_dsn,
                min_size=self.config.min_pool_size,
                max_size=self.config.max_pool_size,
                command_timeout=60,
            )
            self._connected = True
            logger.info(f"Connected to PostgreSQL: {self.config.host}:{self.config.port}/{self.config.database}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._connected = False
            logger.info("Disconnected from PostgreSQL")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from pool."""
        if not self._pool:
            raise RuntimeError("Database not connected")
        async with self._pool.acquire() as conn:
            yield conn
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch single row."""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_many(self, query: str, args_list: List[tuple]) -> None:
        """Execute query with multiple argument sets."""
        async with self.acquire() as conn:
            await conn.executemany(query, args_list)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            version = await self.fetchval("SELECT version()")
            pool_size = self._pool.get_size() if self._pool else 0
            return {
                "status": "healthy",
                "connected": self._connected,
                "pool_size": pool_size,
                "version": version[:50] if version else None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }


# Singleton instance
_default_manager: Optional[DatabaseManager] = None


def get_db_manager(config: Optional[LoggerConfig] = None) -> DatabaseManager:
    """Get or create default DatabaseManager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = DatabaseManager(config)
    return _default_manager

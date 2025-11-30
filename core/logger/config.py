"""Logger configuration management."""
import os
from dataclasses import dataclass, field
from typing import Optional

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass
class LoggerConfig:
    """Configuration for UEM Logger."""
    # Database connection (from environment variables)
    host: str = field(default_factory=lambda: os.getenv("UEM_DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("UEM_DB_PORT", "5432")))
    database: str = field(default_factory=lambda: os.getenv("UEM_DB_NAME", "uem_memory"))
    user: str = field(default_factory=lambda: os.getenv("UEM_DB_USER", "uem"))
    password: str = field(default_factory=lambda: os.getenv("UEM_DB_PASSWORD", ""))
    
    # Connection pool
    min_pool_size: int = 2
    max_pool_size: int = 10
    
    # Fallback
    fallback_enabled: bool = True
    fallback_dir: str = field(default_factory=lambda: os.getenv("UEM_FALLBACK_DIR", "data/fallback"))
    
    # Batch settings
    batch_size: int = 100
    flush_interval_ms: int = 1000
    
    @property
    def dsn(self) -> str:
        """PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def asyncpg_dsn(self) -> str:
        """Asyncpg connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

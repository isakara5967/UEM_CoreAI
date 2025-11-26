"""
Storage implementations for UEM Memory System.
"""

from .base import (
    BaseStorage,
    StoredEvent,
    StoredSnapshot,
    get_storage
)
from .memory_storage import MemoryStorage
from .file_storage import FileStorage

# PostgresStorage optional (requires asyncpg)
try:
    from .postgres_storage import PostgresStorage
    __all__ = [
        'BaseStorage', 'StoredEvent', 'StoredSnapshot', 'get_storage',
        'MemoryStorage', 'FileStorage', 'PostgresStorage'
    ]
except ImportError:
    __all__ = [
        'BaseStorage', 'StoredEvent', 'StoredSnapshot', 'get_storage',
        'MemoryStorage', 'FileStorage'
    ]

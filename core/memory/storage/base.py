"""
BaseStorage - Abstract Storage Interface
Tüm storage implementasyonları bu interface'i kullanır.

Updated: 16D vectors, state_before/after for events
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid


STATE_VECTOR_SIZE = 16

SV_RESOURCE = 0
SV_THREAT = 1
SV_WELLBEING = 2
SV_HEALTH = 3
SV_ENERGY = 4
SV_VALENCE = 5
SV_AROUSAL = 6
SV_DOMINANCE = 7


def _ensure_16d(vec: Tuple[float, ...]) -> Tuple[float, ...]:
    if vec is None:
        return (0.0,) * STATE_VECTOR_SIZE
    if len(vec) >= STATE_VECTOR_SIZE:
        return tuple(vec[:STATE_VECTOR_SIZE])
    return tuple(vec) + (0.0,) * (STATE_VECTOR_SIZE - len(vec))


@dataclass
class StoredEvent:
    """Event for public.events - 16D vectors."""
    id: Optional[int] = None
    agent_id: str = ""
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    tick: int = 0
    category: str = "WORLD"
    source: str = ""
    target: str = ""
    state_before: Tuple[float, ...] = (0.0,) * STATE_VECTOR_SIZE
    effect: Tuple[float, ...] = (0.0,) * STATE_VECTOR_SIZE
    state_after: Tuple[float, ...] = (0.0,) * STATE_VECTOR_SIZE
    salience: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        self.state_before = _ensure_16d(self.state_before)
        self.effect = _ensure_16d(self.effect)
        self.state_after = _ensure_16d(self.state_after)


@dataclass 
class StoredSnapshot:
    """Snapshot for public.snapshots - 16D state_vector."""
    id: Optional[int] = None
    agent_id: str = ""
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    tick: int = 0
    state_vector: Tuple[float, ...] = (0.0,) * STATE_VECTOR_SIZE
    consolidation_level: int = 0
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    strength: float = 1.0
    salience: float = 0.5
    goals: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
        self.state_vector = _ensure_16d(self.state_vector)


class BaseStorage(ABC):
    def __init__(self):
        self._stats = {
            'events_stored': 0,
            'snapshots_stored': 0,
            'queries': 0,
        }
    
    @abstractmethod
    def store_event(self, event: StoredEvent) -> int:
        pass
    
    @abstractmethod
    def store_snapshot(self, snapshot: StoredSnapshot) -> int:
        pass
    
    @abstractmethod
    def get_recent_events(self, n: int = 10, agent_id: Optional[str] = None) -> List[StoredEvent]:
        pass
    
    @abstractmethod
    def get_recent_snapshots(self, n: int = 10, agent_id: Optional[str] = None) -> List[StoredSnapshot]:
        pass
    
    @abstractmethod
    def find_similar_snapshots(
        self,
        state_vector: Tuple[float, ...],
        limit: int = 5,
        tolerance: float = 0.5,
        agent_id: Optional[str] = None,
        allow_cross_agent: bool = False,
    ) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def close(self) -> None:
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        return self._stats.copy()
    
    def clear(self) -> None:
        self._stats = {'events_stored': 0, 'snapshots_stored': 0, 'queries': 0}
    
    @staticmethod
    def compute_distance(v1: Tuple[float, ...], v2: Tuple[float, ...]) -> float:
        v1 = _ensure_16d(v1)
        v2 = _ensure_16d(v2)
        return sum((a - b) ** 2 for a, b in zip(v1, v2)) ** 0.5


def get_storage(storage_type: str = "memory", **kwargs) -> BaseStorage:
    if storage_type == "memory":
        from .memory_storage import MemoryStorage
        return MemoryStorage(**kwargs)
    elif storage_type == "file":
        from .file_storage import FileStorage
        return FileStorage(**kwargs)
    elif storage_type == "postgres":
        from .postgres_storage import PostgresStorage
        return PostgresStorage(**kwargs)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")

"""
BaseStorage - Abstract Storage Interface
Tüm storage implementasyonları bu interface'i kullanır.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid


# ============== Data Classes ==============

@dataclass
class StoredEvent:
    """Veritabanına kaydedilen event yapısı."""
    id: Optional[int] = None
    agent_id: str = ""  # Storage tarafından atanacak
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    tick: int = 0
    category: str = "WORLD"
    source: str = ""
    target: str = ""
    effect: Tuple[float, ...] = (0.0,) * 8
    salience: float = 0.5
    emotion_valence: Optional[float] = None
    emotion_arousal: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass 
class StoredSnapshot:
    """Veritabanına kaydedilen snapshot yapısı."""
    id: Optional[int] = None
    agent_id: str = ""  # Storage tarafından atanacak
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    tick: int = 0
    state_vector: Tuple[float, ...] = (0.0,) * 8
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


# ============== Abstract Base Class ==============

class BaseStorage(ABC):
    """
    Abstract base class for all storage implementations.
    """
    
    def __init__(self, agent_id: Optional[str] = None):
        self._default_agent_id = agent_id or str(uuid.uuid4())
        self._stats = {
            'events_stored': 0,
            'snapshots_stored': 0,
            'queries': 0
        }
    
    @property
    def agent_id(self) -> str:
        return self._default_agent_id
    
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
    def get_similar_experiences(
        self,
        state_vector: Tuple[float, ...],
        limit: int = 5,
        tolerance: float = 0.3,
        agent_id: Optional[str] = None,
        allow_cross_agent: bool = False
    ) -> List[StoredSnapshot]:
        pass
    
    @abstractmethod
    def close(self) -> None:
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        self._stats = {'events_stored': 0, 'snapshots_stored': 0, 'queries': 0}
    
    def health_check(self) -> bool:
        return True
    
    def _resolve_agent_id(self, agent_id: Optional[str]) -> str:
        return agent_id or self._default_agent_id
    
    @staticmethod
    def compute_distance(v1: Tuple[float, ...], v2: Tuple[float, ...]) -> float:
        if len(v1) != len(v2):
            raise ValueError(f"Vector length mismatch: {len(v1)} vs {len(v2)}")
        return sum((a - b) ** 2 for a, b in zip(v1, v2)) ** 0.5
    
    @staticmethod
    def compute_similarity(v1: Tuple[float, ...], v2: Tuple[float, ...]) -> float:
        distance = BaseStorage.compute_distance(v1, v2)
        max_distance = len(v1) ** 0.5 * 2
        return max(0.0, 1.0 - (distance / max_distance))


def get_storage(storage_type: str = "memory", agent_id: Optional[str] = None, **kwargs) -> BaseStorage:
    if storage_type == "memory":
        from .memory_storage import MemoryStorage
        return MemoryStorage(agent_id=agent_id, **kwargs)
    elif storage_type == "file":
        from .file_storage import FileStorage
        return FileStorage(agent_id=agent_id, **kwargs)
    elif storage_type == "postgres":
        from .postgres_storage import PostgresStorage
        return PostgresStorage(agent_id=agent_id, **kwargs)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")

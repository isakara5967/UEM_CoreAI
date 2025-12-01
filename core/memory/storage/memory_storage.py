"""
MemoryStorage - In-memory storage implementation.
Updated: 16D vectors, backward compatible methods
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import deque
from datetime import datetime
import threading

from .base import BaseStorage, StoredEvent, StoredSnapshot, _ensure_16d, STATE_VECTOR_SIZE


class MemoryStorage(BaseStorage):
    """In-memory storage using deque buffers."""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        max_events: int = 10000,
        max_snapshots: int = 1000,
        **kwargs
    ):
        super().__init__()
        self._default_agent_id = agent_id or "default_agent"
        self._agent_id = self._default_agent_id
        self._events: deque = deque(maxlen=max_events)
        self._snapshots: deque = deque(maxlen=max_snapshots)
        self._event_id_counter = 0
        self._snapshot_id_counter = 0
        self._lock = threading.Lock()
        self._config = {'max_events': max_events, 'max_snapshots': max_snapshots}

    @property
    def agent_id(self) -> str:
        return self._agent_id

    def _resolve_agent_id(self, agent_id: Optional[str]) -> str:
        return agent_id or self._default_agent_id

    def store_event(self, event: StoredEvent) -> int:
        with self._lock:
            self._event_id_counter += 1
            event.id = self._event_id_counter
            if not event.agent_id:
                event.agent_id = self._default_agent_id
            if event.timestamp is None:
                event.timestamp = datetime.now()
            self._events.append(event)
            self._stats['events_stored'] += 1
            return event.id

    def store_snapshot(self, snapshot: StoredSnapshot) -> int:
        with self._lock:
            self._snapshot_id_counter += 1
            snapshot.id = self._snapshot_id_counter
            if not snapshot.agent_id:
                snapshot.agent_id = self._default_agent_id
            if snapshot.timestamp is None:
                snapshot.timestamp = datetime.now()
            if snapshot.last_accessed is None:
                snapshot.last_accessed = snapshot.timestamp
            self._snapshots.append(snapshot)
            self._stats['snapshots_stored'] += 1
            return snapshot.id

    def get_recent_events(self, n: int = 10, agent_id: Optional[str] = None) -> List[StoredEvent]:
        self._stats['queries'] += 1
        resolved = self._resolve_agent_id(agent_id)
        with self._lock:
            filtered = [e for e in self._events if e.agent_id == resolved]
            return list(reversed(filtered[-n:]))

    def get_recent_snapshots(self, n: int = 10, agent_id: Optional[str] = None) -> List[StoredSnapshot]:
        self._stats['queries'] += 1
        resolved = self._resolve_agent_id(agent_id)
        with self._lock:
            filtered = [s for s in self._snapshots if s.agent_id == resolved]
            return list(reversed(filtered[-n:]))

    def find_similar_snapshots(
        self,
        state_vector: Tuple[float, ...],
        limit: int = 5,
        tolerance: float = 0.5,
        agent_id: Optional[str] = None,
        allow_cross_agent: bool = False,
    ) -> List[Dict[str, Any]]:
        """Find similar snapshots using Euclidean distance."""
        self._stats['queries'] += 1
        resolved = self._resolve_agent_id(agent_id)
        state_vector = _ensure_16d(state_vector)

        with self._lock:
            results = []
            for snapshot in self._snapshots:
                if not allow_cross_agent and snapshot.agent_id != resolved:
                    continue
                distance = self.compute_distance(state_vector, snapshot.state_vector)
                if distance <= tolerance:
                    snapshot.access_count += 1
                    snapshot.last_accessed = datetime.now()
                    results.append({
                        'snapshot': snapshot,
                        'distance': distance,
                        'similarity': 1.0 / (1.0 + distance),
                    })
            results.sort(key=lambda x: x['distance'])
            return results[:limit]

    # Backward compatibility alias
    def get_similar_experiences(
        self,
        state_vector: Tuple[float, ...],
        limit: int = 5,
        tolerance: float = 0.5,
        agent_id: Optional[str] = None,
        allow_cross_agent: bool = False,
    ) -> List[StoredSnapshot]:
        """Backward compat: returns list of snapshots instead of dicts."""
        results = self.find_similar_snapshots(
            state_vector, limit, tolerance, agent_id, allow_cross_agent
        )
        return [r['snapshot'] for r in results]

    def close(self) -> None:
        with self._lock:
            self._events.clear()
            self._snapshots.clear()

    def clear(self) -> None:
        super().clear()
        with self._lock:
            self._events.clear()
            self._snapshots.clear()
            self._event_id_counter = 0
            self._snapshot_id_counter = 0

    def get_stats(self) -> Dict[str, Any]:
        stats = super().get_stats()
        with self._lock:
            stats.update({
                'current_events': len(self._events),
                'current_snapshots': len(self._snapshots),
                'max_events': self._config['max_events'],
                'max_snapshots': self._config['max_snapshots']
            })
        return stats

    def get_all_events(self, agent_id: Optional[str] = None) -> List[StoredEvent]:
        """Get all events (for testing/debug)."""
        resolved = self._resolve_agent_id(agent_id) if agent_id else None
        with self._lock:
            if resolved:
                return [e for e in self._events if e.agent_id == resolved]
            return list(self._events)

    def get_all_snapshots(self, agent_id: Optional[str] = None) -> List[StoredSnapshot]:
        """Get all snapshots (for testing/debug)."""
        resolved = self._resolve_agent_id(agent_id) if agent_id else None
        with self._lock:
            if resolved:
                return [s for s in self._snapshots if s.agent_id == resolved]
            return list(self._snapshots)

    def health_check(self) -> bool:
        """Always healthy for in-memory storage."""
        return True

    @staticmethod
    def compute_similarity(v1: Tuple[float, ...], v2: Tuple[float, ...]) -> float:
        """Compute similarity (1.0 = identical)."""
        distance = BaseStorage.compute_distance(v1, v2)
        return 1.0 / (1.0 + distance)

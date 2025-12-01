"""
File-based Storage Implementation using JSON files.
Updated: 16D vectors, backward compatible methods
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .base import BaseStorage, StoredEvent, StoredSnapshot, STATE_VECTOR_SIZE, _ensure_16d


class FileStorage(BaseStorage):
    def __init__(
        self, 
        data_dir: str = "./uem_data", 
        default_agent_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__()
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._default_agent_id = agent_id or default_agent_id or "default_agent"
        self._agent_id = self._default_agent_id
        self._events_file = self._data_dir / "events.json"
        self._snapshots_file = self._data_dir / "snapshots.json"
        if not self._events_file.exists():
            self._events_file.write_text("[]")
        if not self._snapshots_file.exists():
            self._snapshots_file.write_text("[]")

    @property
    def agent_id(self) -> str:
        return self._agent_id

    def _resolve_agent_id(self, agent_id: Optional[str]) -> str:
        return agent_id or self._default_agent_id

    def _load_events(self) -> List[Dict]:
        try:
            return json.loads(self._events_file.read_text())
        except:
            return []

    def _save_events(self, events: List[Dict]):
        self._events_file.write_text(json.dumps(events, indent=2, default=str))

    def _load_snapshots(self) -> List[Dict]:
        try:
            return json.loads(self._snapshots_file.read_text())
        except:
            return []

    def _save_snapshots(self, snapshots: List[Dict]):
        self._snapshots_file.write_text(json.dumps(snapshots, indent=2, default=str))

    def store_event(self, event: StoredEvent) -> int:
        events = self._load_events()
        if not event.agent_id:
            event.agent_id = self._default_agent_id
        event_id = len(events) + 1
        event.id = event_id
        events.append({
            'id': event_id, 'agent_id': event.agent_id, 'session_id': event.session_id,
            'timestamp': str(event.timestamp), 'tick': event.tick, 'category': event.category,
            'source': event.source, 'target': event.target,
            'state_before': list(event.state_before), 'effect': list(event.effect),
            'state_after': list(event.state_after), 'salience': event.salience,
            'metadata': event.metadata,
        })
        self._save_events(events)
        self._stats['events_stored'] += 1
        return event_id

    def store_snapshot(self, snapshot: StoredSnapshot) -> int:
        snapshots = self._load_snapshots()
        if not snapshot.agent_id:
            snapshot.agent_id = self._default_agent_id
        snap_id = len(snapshots) + 1
        snapshot.id = snap_id
        snapshots.append({
            'id': snap_id, 'agent_id': snapshot.agent_id, 'session_id': snapshot.session_id,
            'timestamp': str(snapshot.timestamp), 'tick': snapshot.tick,
            'state_vector': list(snapshot.state_vector),
            'consolidation_level': snapshot.consolidation_level,
            'last_accessed': str(snapshot.last_accessed), 'access_count': snapshot.access_count,
            'strength': snapshot.strength, 'salience': snapshot.salience,
            'goals': snapshot.goals, 'metadata': snapshot.metadata,
        })
        self._save_snapshots(snapshots)
        self._stats['snapshots_stored'] += 1
        return snap_id

    def get_recent_events(self, n: int = 10, agent_id: Optional[str] = None) -> List[StoredEvent]:
        self._stats['queries'] += 1
        events = self._load_events()
        aid = agent_id or self._default_agent_id
        filtered = [e for e in events if e.get('agent_id') == aid]
        filtered.sort(key=lambda x: (x.get('tick', 0), x.get('id', 0)), reverse=True)
        return [self._dict_to_event(e) for e in filtered[:n]]

    def get_recent_snapshots(self, n: int = 10, agent_id: Optional[str] = None) -> List[StoredSnapshot]:
        self._stats['queries'] += 1
        snapshots = self._load_snapshots()
        aid = agent_id or self._default_agent_id
        filtered = [s for s in snapshots if s.get('agent_id') == aid]
        filtered.sort(key=lambda x: (x.get('tick', 0), x.get('id', 0)), reverse=True)
        return [self._dict_to_snapshot(s) for s in filtered[:n]]

    def find_similar_snapshots(
        self, state_vector: Tuple[float, ...], limit: int = 5,
        tolerance: float = 0.5, agent_id: Optional[str] = None,
        allow_cross_agent: bool = False
    ) -> List[Dict[str, Any]]:
        self._stats['queries'] += 1
        snapshots = self._load_snapshots()
        state_vector = _ensure_16d(state_vector)
        if not allow_cross_agent:
            aid = agent_id or self._default_agent_id
            snapshots = [s for s in snapshots if s.get('agent_id') == aid]
        results = []
        for snap_dict in snapshots:
            snap_vec = _ensure_16d(tuple(snap_dict.get('state_vector', [])))
            dist = self.compute_distance(state_vector, snap_vec)
            if dist < tolerance:
                results.append({'snapshot': self._dict_to_snapshot(snap_dict),
                               'distance': dist, 'similarity': 1.0/(1.0+dist)})
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

    def close(self):
        pass

    def clear(self):
        super().clear()
        self._events_file.write_text("[]")
        self._snapshots_file.write_text("[]")

    def health_check(self) -> bool:
        """Check if files are accessible."""
        return self._events_file.exists() and self._snapshots_file.exists()

    @staticmethod
    def compute_similarity(v1: Tuple[float, ...], v2: Tuple[float, ...]) -> float:
        """Compute similarity (1.0 = identical)."""
        distance = BaseStorage.compute_distance(v1, v2)
        return 1.0 / (1.0 + distance)

    def _dict_to_event(self, data: Dict) -> StoredEvent:
        return StoredEvent(
            id=data.get('id'), agent_id=data.get('agent_id', ''),
            session_id=data.get('session_id'), timestamp=data.get('timestamp'),
            tick=data.get('tick', 0), category=data.get('category', 'WORLD'),
            source=data.get('source', ''), target=data.get('target', ''),
            state_before=tuple(data.get('state_before', [0.0]*16)),
            effect=tuple(data.get('effect', [0.0]*16)),
            state_after=tuple(data.get('state_after', [0.0]*16)),
            salience=data.get('salience', 0.5), metadata=data.get('metadata', {}),
        )

    def _dict_to_snapshot(self, data: Dict) -> StoredSnapshot:
        return StoredSnapshot(
            id=data.get('id'), agent_id=data.get('agent_id', ''),
            session_id=data.get('session_id'), timestamp=data.get('timestamp'),
            tick=data.get('tick', 0),
            state_vector=tuple(data.get('state_vector', [0.0]*16)),
            consolidation_level=data.get('consolidation_level', 0),
            last_accessed=data.get('last_accessed'),
            access_count=data.get('access_count', 0),
            strength=data.get('strength', 1.0), salience=data.get('salience', 0.5),
            goals=data.get('goals', []), metadata=data.get('metadata', {}),
        )

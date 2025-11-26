"""
FileStorage - JSONL file-based storage implementation.
Fallback, debug ve offline mod için. DB olmadan kalıcı depolama.
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import threading
import fcntl

from .base import BaseStorage, StoredEvent, StoredSnapshot


class FileStorage(BaseStorage):
    """
    File-based storage using JSONL format.
    
    Use cases:
        - DB fallback (DB down olursa)
        - Debug/logging
        - Offline mode
        - Data export/import
    
    File structure:
        data_dir/
            events_{agent_id}.jsonl
            snapshots_{agent_id}.jsonl
    """
    
    def __init__(
        self, 
        agent_id: Optional[str] = None,
        data_dir: str = "./data/storage"
    ):
        super().__init__(agent_id)
        
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.Lock()
        self._event_id_counter = self._load_counter('events')
        self._snapshot_id_counter = self._load_counter('snapshots')
    
    # ============== File Paths ==============
    
    def _events_file(self, agent_id: str) -> Path:
        return self._data_dir / f"events_{agent_id}.jsonl"
    
    def _snapshots_file(self, agent_id: str) -> Path:
        return self._data_dir / f"snapshots_{agent_id}.jsonl"
    
    def _counter_file(self, prefix: str) -> Path:
        return self._data_dir / f".{prefix}_counter"
    
    # ============== Counter Management ==============
    
    def _load_counter(self, prefix: str) -> int:
        counter_file = self._counter_file(prefix)
        if counter_file.exists():
            return int(counter_file.read_text().strip())
        return 0
    
    def _save_counter(self, prefix: str, value: int) -> None:
        self._counter_file(prefix).write_text(str(value))
    
    # ============== Serialization ==============
    
    def _event_to_dict(self, event: StoredEvent) -> Dict:
        return {
            'id': event.id,
            'agent_id': event.agent_id,
            'session_id': event.session_id,
            'timestamp': event.timestamp.isoformat() if event.timestamp else None,
            'tick': event.tick,
            'category': event.category,
            'source': event.source,
            'target': event.target,
            'effect': list(event.effect),
            'salience': event.salience,
            'emotion_valence': event.emotion_valence,
            'emotion_arousal': event.emotion_arousal,
            'metadata': event.metadata
        }
    
    def _dict_to_event(self, data: Dict) -> StoredEvent:
        return StoredEvent(
            id=data.get('id'),
            agent_id=data.get('agent_id', ''),
            session_id=data.get('session_id'),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            tick=data.get('tick', 0),
            category=data.get('category', 'WORLD'),
            source=data.get('source', ''),
            target=data.get('target', ''),
            effect=tuple(data.get('effect', [0.0] * 8)),
            salience=data.get('salience', 0.5),
            emotion_valence=data.get('emotion_valence'),
            emotion_arousal=data.get('emotion_arousal'),
            metadata=data.get('metadata', {})
        )
    
    def _snapshot_to_dict(self, snapshot: StoredSnapshot) -> Dict:
        return {
            'id': snapshot.id,
            'agent_id': snapshot.agent_id,
            'session_id': snapshot.session_id,
            'timestamp': snapshot.timestamp.isoformat() if snapshot.timestamp else None,
            'tick': snapshot.tick,
            'state_vector': list(snapshot.state_vector),
            'consolidation_level': snapshot.consolidation_level,
            'last_accessed': snapshot.last_accessed.isoformat() if snapshot.last_accessed else None,
            'access_count': snapshot.access_count,
            'strength': snapshot.strength,
            'salience': snapshot.salience,
            'goals': snapshot.goals,
            'metadata': snapshot.metadata
        }
    
    def _dict_to_snapshot(self, data: Dict) -> StoredSnapshot:
        return StoredSnapshot(
            id=data.get('id'),
            agent_id=data.get('agent_id', ''),
            session_id=data.get('session_id'),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            tick=data.get('tick', 0),
            state_vector=tuple(data.get('state_vector', [0.0] * 8)),
            consolidation_level=data.get('consolidation_level', 0),
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None,
            access_count=data.get('access_count', 0),
            strength=data.get('strength', 1.0),
            salience=data.get('salience', 0.5),
            goals=data.get('goals', []),
            metadata=data.get('metadata', {})
        )
    
    # ============== Core Methods ==============
    
    def store_event(self, event: StoredEvent) -> int:
        """Append event to JSONL file."""
        with self._lock:
            self._event_id_counter += 1
            event.id = self._event_id_counter
            
            if not event.agent_id:
                event.agent_id = self._default_agent_id
            if event.timestamp is None:
                event.timestamp = datetime.now()
            
            filepath = self._events_file(event.agent_id)
            with open(filepath, 'a') as f:
                f.write(json.dumps(self._event_to_dict(event)) + '\n')
            
            self._save_counter('events', self._event_id_counter)
            self._stats['events_stored'] += 1
            
            return event.id
    
    def store_snapshot(self, snapshot: StoredSnapshot) -> int:
        """Append snapshot to JSONL file."""
        with self._lock:
            self._snapshot_id_counter += 1
            snapshot.id = self._snapshot_id_counter
            
            if not snapshot.agent_id:
                snapshot.agent_id = self._default_agent_id
            if snapshot.timestamp is None:
                snapshot.timestamp = datetime.now()
            if snapshot.last_accessed is None:
                snapshot.last_accessed = snapshot.timestamp
            
            filepath = self._snapshots_file(snapshot.agent_id)
            with open(filepath, 'a') as f:
                f.write(json.dumps(self._snapshot_to_dict(snapshot)) + '\n')
            
            self._save_counter('snapshots', self._snapshot_id_counter)
            self._stats['snapshots_stored'] += 1
            
            return snapshot.id
    
    def get_recent_events(
        self, 
        n: int = 10, 
        agent_id: Optional[str] = None
    ) -> List[StoredEvent]:
        """Read last n events from file."""
        self._stats['queries'] += 1
        resolved_agent = self._resolve_agent_id(agent_id)
        filepath = self._events_file(resolved_agent)
        
        if not filepath.exists():
            return []
        
        events = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(self._dict_to_event(json.loads(line)))
        
        return list(reversed(events[-n:]))
    
    def get_recent_snapshots(
        self, 
        n: int = 10, 
        agent_id: Optional[str] = None
    ) -> List[StoredSnapshot]:
        """Read last n snapshots from file."""
        self._stats['queries'] += 1
        resolved_agent = self._resolve_agent_id(agent_id)
        filepath = self._snapshots_file(resolved_agent)
        
        if not filepath.exists():
            return []
        
        snapshots = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    snapshots.append(self._dict_to_snapshot(json.loads(line)))
        
        return list(reversed(snapshots[-n:]))
    
    def get_similar_experiences(
        self,
        state_vector: Tuple[float, ...],
        limit: int = 5,
        tolerance: float = 0.3,
        agent_id: Optional[str] = None,
        allow_cross_agent: bool = False
    ) -> List[StoredSnapshot]:
        """Find similar experiences by scanning files."""
        self._stats['queries'] += 1
        resolved_agent = self._resolve_agent_id(agent_id)
        
        candidates = []
        
        # Determine which files to scan
        if allow_cross_agent:
            snapshot_files = list(self._data_dir.glob("snapshots_*.jsonl"))
        else:
            snapshot_files = [self._snapshots_file(resolved_agent)]
        
        for filepath in snapshot_files:
            if not filepath.exists():
                continue
                
            with open(filepath, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    snapshot = self._dict_to_snapshot(json.loads(line))
                    distance = self.compute_distance(state_vector, snapshot.state_vector)
                    
                    if distance <= tolerance:
                        candidates.append((distance, snapshot))
        
        candidates.sort(key=lambda x: x[0])
        return [snap for _, snap in candidates[:limit]]
    
    def close(self) -> None:
        """Nothing to close for file storage."""
        pass
    
    # ============== Additional Methods ==============
    
    def get_stats(self) -> Dict[str, Any]:
        """Extended stats including file info."""
        stats = super().get_stats()
        
        # Count files and sizes
        total_size = 0
        file_count = 0
        for f in self._data_dir.glob("*.jsonl"):
            total_size += f.stat().st_size
            file_count += 1
        
        stats.update({
            'data_dir': str(self._data_dir),
            'file_count': file_count,
            'total_size_bytes': total_size
        })
        return stats
    
    def clear(self, agent_id: Optional[str] = None) -> None:
        """Clear data files for agent."""
        resolved_agent = self._resolve_agent_id(agent_id) if agent_id else None
        
        if resolved_agent:
            # Clear specific agent
            for f in [self._events_file(resolved_agent), self._snapshots_file(resolved_agent)]:
                if f.exists():
                    f.unlink()
        else:
            # Clear all
            for f in self._data_dir.glob("*.jsonl"):
                f.unlink()
            for f in self._data_dir.glob(".*_counter"):
                f.unlink()
            self._event_id_counter = 0
            self._snapshot_id_counter = 0
        
        self.reset_stats()

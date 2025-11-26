"""
MemoryStorage - In-memory storage implementation.
Test ve hızlı prototipleme için. Uygulama kapanınca veri kaybolur.
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import deque
from datetime import datetime
import threading

from .base import BaseStorage, StoredEvent, StoredSnapshot


class MemoryStorage(BaseStorage):
    """
    In-memory storage using deque buffers.
    
    Use cases:
        - Unit tests (no DB required)
        - Quick prototyping
        - Development without DB setup
    
    Limitations:
        - Data lost on restart
        - No persistence
        - Single process only
    """
    
    def __init__(
        self, 
        agent_id: Optional[str] = None,
        max_events: int = 10000,
        max_snapshots: int = 1000
    ):
        super().__init__(agent_id)
        
        self._events: deque = deque(maxlen=max_events)
        self._snapshots: deque = deque(maxlen=max_snapshots)
        self._event_id_counter = 0
        self._snapshot_id_counter = 0
        self._lock = threading.Lock()
        
        self._config = {
            'max_events': max_events,
            'max_snapshots': max_snapshots
        }
    
    # ============== Core Methods ==============
    
    def store_event(self, event: StoredEvent) -> int:
        """Store event in memory."""
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
        """Store snapshot in memory."""
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
    
    def get_recent_events(
        self, 
        n: int = 10, 
        agent_id: Optional[str] = None
    ) -> List[StoredEvent]:
        """Get recent events, optionally filtered by agent."""
        self._stats['queries'] += 1
        resolved_agent = self._resolve_agent_id(agent_id)
        
        with self._lock:
            # Filter by agent and get last n
            filtered = [
                e for e in self._events 
                if e.agent_id == resolved_agent
            ]
            return list(reversed(filtered[-n:]))
    
    def get_recent_snapshots(
        self, 
        n: int = 10, 
        agent_id: Optional[str] = None
    ) -> List[StoredSnapshot]:
        """Get recent snapshots, optionally filtered by agent."""
        self._stats['queries'] += 1
        resolved_agent = self._resolve_agent_id(agent_id)
        
        with self._lock:
            filtered = [
                s for s in self._snapshots 
                if s.agent_id == resolved_agent
            ]
            return list(reversed(filtered[-n:]))
    
    def get_similar_experiences(
        self,
        state_vector: Tuple[float, ...],
        limit: int = 5,
        tolerance: float = 0.3,
        agent_id: Optional[str] = None,
        allow_cross_agent: bool = False
    ) -> List[StoredSnapshot]:
        """Find similar experiences using Euclidean distance."""
        self._stats['queries'] += 1
        resolved_agent = self._resolve_agent_id(agent_id)
        
        with self._lock:
            candidates = []
            
            for snapshot in self._snapshots:
                # Agent filter
                if not allow_cross_agent and snapshot.agent_id != resolved_agent:
                    continue
                
                # Compute distance
                distance = self.compute_distance(state_vector, snapshot.state_vector)
                
                if distance <= tolerance:
                    # Update access stats
                    snapshot.access_count += 1
                    snapshot.last_accessed = datetime.now()
                    candidates.append((distance, snapshot))
            
            # Sort by distance and return top matches
            candidates.sort(key=lambda x: x[0])
            return [snap for _, snap in candidates[:limit]]
    
    def close(self) -> None:
        """Clear memory buffers."""
        with self._lock:
            self._events.clear()
            self._snapshots.clear()
    
    # ============== Additional Methods ==============
    
    def get_stats(self) -> Dict[str, Any]:
        """Extended stats including buffer sizes."""
        stats = super().get_stats()
        with self._lock:
            stats.update({
                'current_events': len(self._events),
                'current_snapshots': len(self._snapshots),
                'max_events': self._config['max_events'],
                'max_snapshots': self._config['max_snapshots']
            })
        return stats
    
    def clear(self) -> None:
        """Clear all data but keep storage open."""
        with self._lock:
            self._events.clear()
            self._snapshots.clear()
            self._event_id_counter = 0
            self._snapshot_id_counter = 0
        self.reset_stats()
    
    def get_all_events(self, agent_id: Optional[str] = None) -> List[StoredEvent]:
        """Get all events (for testing/debug)."""
        resolved_agent = self._resolve_agent_id(agent_id) if agent_id else None
        
        with self._lock:
            if resolved_agent:
                return [e for e in self._events if e.agent_id == resolved_agent]
            return list(self._events)
    
    def get_all_snapshots(self, agent_id: Optional[str] = None) -> List[StoredSnapshot]:
        """Get all snapshots (for testing/debug)."""
        resolved_agent = self._resolve_agent_id(agent_id) if agent_id else None
        
        with self._lock:
            if resolved_agent:
                return [s for s in self._snapshots if s.agent_id == resolved_agent]
            return list(self._snapshots)

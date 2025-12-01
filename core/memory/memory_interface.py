# core/memory/memory_interface.py
"""
Memory Interface for SELF Integration (v2)

Provides a simple interface for SELF to write events and snapshots to Memory.
Now supports multiple storage backends: Memory, File, PostgreSQL.

Author: UEM Project
Date: 26 November 2025
"""

from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from core.ontology.types import Event, SelfEntity, StateVector

# Import storage
from core.memory.storage import (
    BaseStorage, MemoryStorage, StoredEvent, StoredSnapshot, get_storage
)


class MemoryInterface:
    """
    Interface for SELF to interact with Memory systems.
    
    Supports multiple backends:
        - MemoryStorage (default, in-memory)
        - FileStorage (JSONL persistence)
        - PostgresStorage (production, pgvector)
    """

    def __init__(
        self,
        storage: Optional[BaseStorage] = None,
        storage_type: str = "memory",
        agent_id: Optional[str] = None,
        # Legacy parameters (backward compatibility)
        ltm: Optional[Any] = None,
        consolidator: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Memory Interface.

        Args:
            storage: Storage backend instance (preferred)
            storage_type: "memory", "file", or "postgres" (if storage not provided)
            agent_id: Agent identifier
            ltm: Legacy LTM instance (backward compat)
            consolidator: Legacy consolidator (backward compat)
            logger: Logger instance
            config: Configuration dict
        """
        self.logger = logger or logging.getLogger("memory.interface")
        self.config = config or {}
        
        # New storage backend
        if storage is not None:
            self._storage = storage
        else:
            storage_config = {}
            if storage_type == "file":
                storage_config['data_dir'] = self.config.get('data_dir', './data/memory')
            elif storage_type == "postgres":
                storage_config['database_url'] = self.config.get('database_url')
            
            self._storage = get_storage(storage_type, agent_id=agent_id, **storage_config)
        
        # Legacy support
        self.ltm = ltm
        self.consolidator = consolidator
        
        # Legacy buffers (for backward compat with old code)
        self._event_buffer: List[Dict[str, Any]] = []
        self._snapshot_buffer: List[Dict[str, Any]] = []
        self._max_buffer_size = self.config.get('max_buffer_size', 1000)

        # Statistics
        self._stats = {
            'events_stored': 0,
            'snapshots_stored': 0,
            'events_retrieved': 0,
            'similar_queries': 0,
        }

    # ========================================================================
    # STORE OPERATIONS
    # ========================================================================

    def store_event(self, event: Any) -> bool:
        """
        Store an event to memory.

        Args:
            event: Event object or dict with event data

        Returns:
            True if stored successfully
        """
        try:
            event_dict = self._event_to_dict(event)
            
            # Convert to StoredEvent
            stored_event = StoredEvent(
                source=event_dict.get('source', 'unknown'),
                target=event_dict.get('target', 'unknown'),
                effect=self._ensure_vector16(event_dict.get('effect', (0,0,0))),
                tick=event_dict.get('tick', 0),
                salience=event_dict.get('salience', 0.5),
                category=event_dict.get('category', 'WORLD'),
                state_before=self._ensure_vector16(event_dict.get('state_before', (0,)*16)),
                state_after=self._ensure_vector16(event_dict.get('state_after', (0,)*16)),
                metadata=event_dict.get('metadata', {}),
            )
            
            self._storage.store_event(stored_event)
            self._stats['events_stored'] += 1
            return True

        except Exception as e:
            self.logger.warning(f"[MemoryInterface] Failed to store event: {e}")
            return False

    def store_state_snapshot(self, snapshot: Any) -> bool:
        """
        Store a SELF state snapshot to memory.

        Args:
            snapshot: SelfEntity or dict with state data

        Returns:
            True if stored successfully
        """
        try:
            snapshot_dict = self._snapshot_to_dict(snapshot)
            
            # Convert to StoredSnapshot
            stored_snapshot = StoredSnapshot(
                state_vector=self._ensure_vector16(snapshot_dict.get('state_vector', (0.5, 0, 0.5))),
                tick=snapshot_dict.get('tick', 0),
                salience=snapshot_dict.get('salience', 0.5),
                goals=snapshot_dict.get('goals', []),
                metadata=snapshot_dict.get('metadata', {}),
            )
            
            self._storage.store_snapshot(stored_snapshot)
            self._stats['snapshots_stored'] += 1
            return True

        except Exception as e:
            self.logger.warning(f"[MemoryInterface] Failed to store snapshot: {e}")
            return False

    # ========================================================================
    # RETRIEVE OPERATIONS
    # ========================================================================

    def get_recent_events(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the n most recent events from memory.

        Args:
            n: Number of events to retrieve

        Returns:
            List of event dicts, newest first
        """
        try:
            stored_events = self._storage.get_recent_events(n)
            events = [self._stored_event_to_dict(e) for e in stored_events]
            self._stats['events_retrieved'] += len(events)
            return events
        except Exception as e:
            self.logger.warning(f"[MemoryInterface] Failed to retrieve events: {e}")
            return []

    def get_recent_snapshots(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the n most recent snapshots from memory.

        Args:
            n: Number of snapshots to retrieve

        Returns:
            List of snapshot dicts, newest first
        """
        try:
            stored_snapshots = self._storage.get_recent_snapshots(n)
            return [self._stored_snapshot_to_dict(s) for s in stored_snapshots]
        except Exception as e:
            self.logger.warning(f"[MemoryInterface] Failed to retrieve snapshots: {e}")
            return []

    def get_similar_experiences(
        self,
        state_vector: tuple,
        tolerance: float = 0.3,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find experiences similar to the given state vector.
        Useful for empathy - finding past experiences matching another's state.

        Args:
            state_vector: State tuple (at least 3 elements)
            tolerance: Max distance threshold (0-1)
            limit: Max results to return

        Returns:
            List of similar experience dicts with similarity scores
        """
        try:
            vector8 = self._ensure_vector16(state_vector)
            
            similar_snapshots = self._storage.get_similar_experiences(
                state_vector=vector8,
                tolerance=tolerance,
                limit=limit,
            )
            
            self._stats['similar_queries'] += 1
            
            results = []
            for snap in similar_snapshots:
                similarity = self._compute_similarity(vector8, snap.state_vector)
                results.append({
                    'snapshot': self._stored_snapshot_to_dict(snap),
                    'similarity': similarity,
                    'state_vector': snap.state_vector[:3],  # Return original 3D
                })
            
            return results

        except Exception as e:
            self.logger.warning(f"[MemoryInterface] Failed to find similar: {e}")
            return []

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _ensure_vector16(self, vec: tuple) -> tuple:
        """Ensure vector has 16 dimensions (pad with zeros if needed)."""
        if vec is None:
            vec = ()
        if len(vec) >= 16:
            return tuple(vec[:16])
        return tuple(vec) + (0.0,) * (16 - len(vec))
    
    # Backward compatibility alias
    def _ensure_vector8(self, vec: tuple) -> tuple:
        """Deprecated: Use _ensure_vector16. Kept for compatibility."""
        return self._ensure_vector16(vec)

    def _event_to_dict(self, event: Any) -> Dict[str, Any]:
        """Convert Event object to dict."""
        if isinstance(event, dict):
            return event
        return {
            'source': getattr(event, 'source', 'unknown'),
            'target': getattr(event, 'target', 'unknown'),
            'effect': getattr(event, 'effect', (0.0,) * 16),
            'timestamp': getattr(event, 'timestamp', time.time()),
            'tick': getattr(event, 'tick', 0),
            'salience': getattr(event, 'salience', 0.5),
        }

    def _snapshot_to_dict(self, snapshot: Any) -> Dict[str, Any]:
        """Convert SelfEntity snapshot to dict."""
        if isinstance(snapshot, dict):
            return snapshot
        return {
            'state_vector': getattr(snapshot, 'state_vector', (0.5, 0.0, 0.5)),
            'history': list(getattr(snapshot, 'history', [])),
            'goals': [
                {'name': g.name, 'priority': g.priority}
                for g in getattr(snapshot, 'goals', [])
            ],
            'tick': getattr(snapshot, 'tick', 0),
            'timestamp': time.time(),
        }

    def _stored_event_to_dict(self, event: StoredEvent) -> Dict[str, Any]:
        """Convert StoredEvent to dict."""
        return {
            'id': event.id,
            'source': event.source,
            'target': event.target,
            'effect': event.effect[:3],  # Return 3D for compatibility
            'tick': event.tick,
            'salience': event.salience,
            'category': event.category,
            'timestamp': event.timestamp,
            'metadata': event.metadata,
        }

    def _stored_snapshot_to_dict(self, snapshot: StoredSnapshot) -> Dict[str, Any]:
        """Convert StoredSnapshot to dict."""
        return {
            'id': snapshot.id,
            'state_vector': snapshot.state_vector[:3],  # Return 3D
            'tick': snapshot.tick,
            'salience': snapshot.salience,
            'goals': snapshot.goals,
            'timestamp': snapshot.timestamp,
            'access_count': snapshot.access_count,
            'strength': snapshot.strength,
            'metadata': snapshot.metadata,
        }

    def _compute_similarity(self, state1: tuple, state2: tuple) -> float:
        """Compute similarity between two state vectors (0-1)."""
        return self._storage.compute_similarity(state1, state2)

    # ========================================================================
    # UTILITY
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get interface and storage statistics."""
        storage_stats = self._storage.get_stats()
        return {
            **self._stats,
            'storage': storage_stats,
            'storage_type': type(self._storage).__name__,
        }

    def health_check(self) -> bool:
        """Check if storage is healthy."""
        return self._storage.health_check()

    def close(self) -> None:
        """Close storage connections."""
        self._storage.close()

    @property
    def storage(self) -> BaseStorage:
        """Access underlying storage."""
        return self._storage

    # Legacy compatibility
    def set_ltm(self, ltm: Any) -> None:
        """Legacy method - no longer needed with new storage."""
        self.ltm = ltm
        self.logger.info("[MemoryInterface] set_ltm called - using new storage backend instead")

    def set_consolidator(self, consolidator: Any) -> None:
        """Legacy method - no longer needed with new storage."""
        self.consolidator = consolidator

    def flush_buffers(self) -> Dict[str, int]:
        """Legacy method - new storage auto-persists."""
        return {'events': 0, 'snapshots': 0}


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_memory_interface(
    storage_type: str = "memory",
    agent_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    # Legacy params
    ltm: Optional[Any] = None,
    consolidator: Optional[Any] = None,
) -> MemoryInterface:
    """
    Factory function to create a MemoryInterface.

    Usage:
        # In-memory (tests, development)
        interface = create_memory_interface()
        
        # File-based (offline, fallback)
        interface = create_memory_interface(storage_type="file")
        
        # PostgreSQL (production)
        interface = create_memory_interface(storage_type="postgres")
    """
    return MemoryInterface(
        storage_type=storage_type,
        agent_id=agent_id,
        config=config,
        ltm=ltm,
        consolidator=consolidator,
    )

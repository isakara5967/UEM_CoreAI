# core/memory/memory_interface.py
"""
Memory Interface for SELF Integration (v1)

Provides a simple interface for SELF to write events and snapshots to Memory.
This bridges the gap between SELF's Working Memory and LTM.

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


# ============================================================================
# MEMORY INTERFACE PROTOCOL
# ============================================================================

class MemoryInterface:
    """
    Interface for SELF to interact with Memory systems.
    
    This class provides a unified API that SELF can use regardless of
    the underlying memory implementation (LTM, STM, or future systems).
    
    Methods:
        store_event(event) -> bool
        store_state_snapshot(snapshot) -> bool
        get_recent_events(n) -> List[Event]
        get_similar_experiences(state_vector) -> List[Dict]
    """
    
    def __init__(
        self,
        ltm: Optional[Any] = None,
        consolidator: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Memory Interface.
        
        Args:
            ltm: LongTermMemory instance (optional)
            consolidator: MemoryConsolidator instance (optional)
            logger: Logger instance
            config: Configuration dict
        """
        self.ltm = ltm
        self.consolidator = consolidator
        self.logger = logger or logging.getLogger("memory.interface")
        self.config = config or {}
        
        # Internal event buffer (for when LTM is not available)
        self._event_buffer: List[Dict[str, Any]] = []
        self._snapshot_buffer: List[Dict[str, Any]] = []
        self._max_buffer_size = self.config.get('max_buffer_size', 1000)
        
        # Statistics
        self._stats = {
            'events_stored': 0,
            'snapshots_stored': 0,
            'events_retrieved': 0,
            'buffer_flushes': 0,
        }
    
    # ========================================================================
    # STORE OPERATIONS
    # ========================================================================
    
    def store_event(self, event: Any) -> bool:
        """
        Store an event to memory.
        
        Args:
            event: Event object (from ontology) or dict with event data
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Convert event to dict if needed
            event_dict = self._event_to_dict(event)
            
            # Try to store in LTM via consolidator
            if self.consolidator is not None:
                self._store_via_consolidator(event_dict)
            elif self.ltm is not None:
                self._store_direct_to_ltm(event_dict)
            else:
                # Buffer for later
                self._buffer_event(event_dict)
            
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
            True if stored successfully, False otherwise
        """
        try:
            # Convert snapshot to dict if needed
            snapshot_dict = self._snapshot_to_dict(snapshot)
            
            # Store as semantic memory (general state info)
            if self.ltm is not None:
                self._store_snapshot_to_ltm(snapshot_dict)
            else:
                self._buffer_snapshot(snapshot_dict)
            
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
        events = []
        
        try:
            if self.ltm is not None:
                # Try to get MemoryType, fallback if not available
                try:
                    from core.memory.consolidation.memory_consolidation import MemoryType
                    memory_type = MemoryType.EPISODIC
                except ImportError:
                    memory_type = 'episodic'
                
                try:
                    memories = self.ltm.retrieve(
                        memory_type=memory_type,
                        limit=n,
                        update_access=True,
                    )
                    events = [self._memory_to_event_dict(m) for m in memories]
                except Exception:
                    pass
            
            # Also include buffered events
            if self._event_buffer:
                buffered = self._event_buffer[-n:]
                events.extend(buffered)
            
            self._stats['events_retrieved'] += len(events)
            
        except Exception as e:
            self.logger.warning(f"[MemoryInterface] Failed to retrieve events: {e}")
        
        return events[:n]
    
    def get_similar_experiences(
        self,
        state_vector: tuple,
        tolerance: float = 0.3,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find experiences similar to the given state vector.
        
        This is useful for empathy - finding past experiences
        that match another agent's current state.
        
        Args:
            state_vector: (RESOURCE, THREAT, WELLBEING) tuple
            tolerance: How close states must be (0-1)
            limit: Max results to return
            
        Returns:
            List of similar experience dicts
        """
        similar = []
        
        try:
            # Search in snapshots for similar states
            if self.ltm is not None:
                try:
                    # Try to get MemoryType, fallback if not available
                    try:
                        from core.memory.consolidation.memory_consolidation import MemoryType
                        memory_type = MemoryType.EPISODIC
                    except ImportError:
                        memory_type = 'episodic'
                    
                    # Get episodic memories and filter by state similarity
                    memories = self.ltm.retrieve(
                        memory_type=memory_type,
                        limit=limit * 3,  # Get more, filter later
                        update_access=False,
                    )
                    
                    for mem in memories:
                        if hasattr(mem, 'content') and isinstance(mem.content, dict):
                            stored_state = mem.content.get('state_vector')
                            if stored_state:
                                similarity = self._compute_similarity(state_vector, stored_state)
                                if similarity >= (1 - tolerance):
                                    similar.append({
                                        'memory': mem,
                                        'similarity': similarity,
                                        'state_vector': stored_state,
                                    })
                    
                    # Sort by similarity
                    similar.sort(key=lambda x: x['similarity'], reverse=True)
                    similar = similar[:limit]
                    
                except Exception:
                    pass
            
            # Also check snapshot buffer
            for snapshot in self._snapshot_buffer:
                stored_state = snapshot.get('state_vector')
                if stored_state:
                    similarity = self._compute_similarity(state_vector, stored_state)
                    if similarity >= (1 - tolerance):
                        similar.append({
                            'snapshot': snapshot,
                            'similarity': similarity,
                            'state_vector': stored_state,
                        })
            
        except Exception as e:
            self.logger.warning(f"[MemoryInterface] Failed to find similar experiences: {e}")
        
        return similar[:limit]
    
    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================
    
    def _event_to_dict(self, event: Any) -> Dict[str, Any]:
        """Convert Event object to dict."""
        if isinstance(event, dict):
            return event
        
        return {
            'source': getattr(event, 'source', 'unknown'),
            'target': getattr(event, 'target', 'unknown'),
            'effect': getattr(event, 'effect', (0, 0, 0)),
            'timestamp': getattr(event, 'timestamp', time.time()),
            'type': 'event',
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
            'timestamp': time.time(),
            'type': 'snapshot',
        }
    
    def _memory_to_event_dict(self, memory: Any) -> Dict[str, Any]:
        """Convert ConsolidatedMemory to event dict."""
        content = getattr(memory, 'content', {})
        if isinstance(content, dict):
            return content
        return {'content': content, 'timestamp': getattr(memory, 'created_at', 0)}
    
    def _compute_similarity(self, state1: tuple, state2: tuple) -> float:
        """Compute similarity between two state vectors (0-1)."""
        try:
            # Euclidean distance normalized to 0-1 similarity
            dist_sq = sum((a - b) ** 2 for a, b in zip(state1, state2))
            max_dist = 3.0  # sqrt(3) for 3D unit cube
            similarity = 1 - (dist_sq ** 0.5) / (max_dist ** 0.5)
            return max(0, min(1, similarity))
        except:
            return 0.0
    
    def _store_via_consolidator(self, event_dict: Dict[str, Any]) -> None:
        """Store event via consolidator (STM → LTM path)."""
        try:
            # Try to get MemoryType, fallback to string if not available
            try:
                from core.memory.consolidation.memory_consolidation import MemoryType
                memory_type = MemoryType.EPISODIC
            except ImportError:
                memory_type = 'episodic'
            
            self.consolidator.add_to_pending(
                content=event_dict,
                salience=event_dict.get('salience', 0.5),
                memory_type=memory_type,
            )
        except Exception as e:
            self.logger.debug(f"[MemoryInterface] Consolidator store failed: {e}")
            # Fallback to direct LTM
            if self.ltm:
                self._store_direct_to_ltm(event_dict)
    
    def _store_direct_to_ltm(self, event_dict: Dict[str, Any]) -> None:
        """Store event directly to LTM."""
        try:
            # Try to get MemoryType, fallback to string if not available
            try:
                from core.memory.consolidation.memory_consolidation import MemoryType
                memory_type = MemoryType.EPISODIC
            except ImportError:
                memory_type = 'episodic'  # Fallback for mock LTM
            
            self.ltm.store(
                content=event_dict,
                memory_type=memory_type,
                salience=event_dict.get('salience', 0.5),
                source='self_interface',
            )
        except Exception as e:
            self.logger.debug(f"[MemoryInterface] Direct LTM store failed: {e}")
    
    def _store_snapshot_to_ltm(self, snapshot_dict: Dict[str, Any]) -> None:
        """Store snapshot to LTM as semantic memory."""
        try:
            # Try to get MemoryType, fallback to string if not available
            try:
                from core.memory.consolidation.memory_consolidation import MemoryType
                memory_type = MemoryType.SEMANTIC
            except ImportError:
                memory_type = 'semantic'  # Fallback for mock LTM
            
            self.ltm.store(
                content=snapshot_dict,
                memory_type=memory_type,
                salience=0.3,  # Snapshots are routine
                source='self_snapshot',
            )
        except Exception as e:
            self.logger.debug(f"[MemoryInterface] Snapshot store failed: {e}")
    
    def _buffer_event(self, event_dict: Dict[str, Any]) -> None:
        """Buffer event when LTM not available."""
        self._event_buffer.append(event_dict)
        if len(self._event_buffer) > self._max_buffer_size:
            self._event_buffer = self._event_buffer[-self._max_buffer_size:]
    
    def _buffer_snapshot(self, snapshot_dict: Dict[str, Any]) -> None:
        """Buffer snapshot when LTM not available."""
        self._snapshot_buffer.append(snapshot_dict)
        if len(self._snapshot_buffer) > self._max_buffer_size:
            self._snapshot_buffer = self._snapshot_buffer[-self._max_buffer_size:]
    
    # ========================================================================
    # UTILITY
    # ========================================================================
    
    def flush_buffers(self) -> Dict[str, int]:
        """
        Flush buffered items to LTM (if available).
        
        Returns:
            Dict with counts of flushed items
        """
        flushed = {'events': 0, 'snapshots': 0}
        
        if self.ltm is None:
            return flushed
        
        # Flush events
        for event in self._event_buffer:
            try:
                self._store_direct_to_ltm(event)
                flushed['events'] += 1
            except:
                pass
        self._event_buffer = []
        
        # Flush snapshots
        for snapshot in self._snapshot_buffer:
            try:
                self._store_snapshot_to_ltm(snapshot)
                flushed['snapshots'] += 1
            except:
                pass
        self._snapshot_buffer = []
        
        self._stats['buffer_flushes'] += 1
        
        return flushed
    
    def get_stats(self) -> Dict[str, Any]:
        """Get interface statistics."""
        return {
            **self._stats,
            'event_buffer_size': len(self._event_buffer),
            'snapshot_buffer_size': len(self._snapshot_buffer),
            'has_ltm': self.ltm is not None,
            'has_consolidator': self.consolidator is not None,
        }
    
    def set_ltm(self, ltm: Any) -> None:
        """Set LTM instance (for late binding)."""
        self.ltm = ltm
        # Flush buffers if we now have LTM
        if ltm is not None:
            self.flush_buffers()
    
    def set_consolidator(self, consolidator: Any) -> None:
        """Set consolidator instance (for late binding)."""
        self.consolidator = consolidator


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_memory_interface(
    ltm: Optional[Any] = None,
    consolidator: Optional[Any] = None,
    config: Optional[Dict[str, Any]] = None,
) -> MemoryInterface:
    """
    Factory function to create a MemoryInterface.
    
    Usage:
        # With LTM
        interface = create_memory_interface(ltm=my_ltm)
        
        # Standalone (buffered mode)
        interface = create_memory_interface()
        
        # With consolidator
        interface = create_memory_interface(
            ltm=my_ltm,
            consolidator=my_consolidator,
        )
    """
    return MemoryInterface(
        ltm=ltm,
        consolidator=consolidator,
        config=config,
    )

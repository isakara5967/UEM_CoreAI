"""
Long-Term Memory Manager

Business logic layer for LTM operations.
Uses PostgresStorage for persistence, implements decay/consolidate/forget logic.

Author: UEM Project
Date: 2 December 2025
"""

import math
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from core.memory.storage.base import BaseStorage, StoredSnapshot, get_storage


@dataclass
class ConsolidationResult:
    """Result of a consolidation cycle"""
    consolidated: int
    rejected: int
    total_candidates: int


@dataclass
class DecayResult:
    """Result of a decay cycle"""
    processed: int
    forgotten: int  # Strength dropped below threshold


@dataclass 
class LTMStats:
    """LTM statistics"""
    total_memories: int
    avg_strength: float
    avg_access_count: float
    oldest_memory_age_hours: float
    consolidation_cycles: int
    decay_cycles: int
    total_forgotten: int


class LTMManager:
    """
    Long-Term Memory Manager
    
    Handles:
    - Consolidation: STM → LTM transfer based on salience/importance
    - Decay: Ebbinghaus forgetting curve
    - Rehearsal: Access strengthens memory
    - Forgetting: Remove weak memories
    - Retrieval: Similarity-based search
    """
    
    def __init__(
        self,
        storage: Optional[BaseStorage] = None,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger("memory.LTMManager")
        self.config = config or {}
        
        # Storage backend
        if storage:
            self._storage = storage
        else:
            self._storage = get_storage(
                "postgres", 
                agent_id=agent_id or "00000000-0000-0000-0000-000000000001"
            )
        
        # Configuration
        self._decay_rate = self.config.get('decay_rate', 0.1)  # Per hour
        self._consolidation_threshold = self.config.get('consolidation_threshold', 0.6)
        self._forget_threshold = self.config.get('forget_threshold', 0.05)
        self._min_consolidation_level = 1  # LTM = consolidation_level >= 1
        
        # Statistics
        self._stats = {
            'consolidation_cycles': 0,
            'decay_cycles': 0,
            'total_consolidated': 0,
            'total_forgotten': 0,
        }
    
    # ========================================================================
    # CONSOLIDATION: STM → LTM
    # ========================================================================
    
    def consolidate(
        self,
        candidates: List[StoredSnapshot],
        emotion_boost: float = 0.2,
    ) -> ConsolidationResult:
        """
        Consolidate STM snapshots to LTM.
        
        Criteria:
        - salience > threshold → consolidate
        - high emotion → boost score
        - already consolidated (level >= 1) → skip
        
        Args:
            candidates: Snapshots to consider for consolidation
            emotion_boost: Extra score for emotional memories
            
        Returns:
            ConsolidationResult with counts
        """
        consolidated = 0
        rejected = 0
        
        for snapshot in candidates:
            # Skip already consolidated
            if snapshot.consolidation_level >= self._min_consolidation_level:
                continue
            
            # Calculate consolidation score
            score = self._calculate_consolidation_score(snapshot, emotion_boost)
            
            if score >= self._consolidation_threshold:
                # Promote to LTM
                success = self._storage.update_snapshot(
                    snapshot_id=snapshot.id,
                    consolidation_level=1,
                    strength=min(1.0, snapshot.strength + 0.1),  # Boost on consolidation
                )
                if success:
                    consolidated += 1
                    self.logger.debug(f"[LTM] Consolidated snapshot {snapshot.id} (score={score:.2f})")
            else:
                rejected += 1
        
        self._stats['consolidation_cycles'] += 1
        self._stats['total_consolidated'] += consolidated
        
        return ConsolidationResult(
            consolidated=consolidated,
            rejected=rejected,
            total_candidates=len(candidates),
        )
    
    def _calculate_consolidation_score(
        self, 
        snapshot: StoredSnapshot, 
        emotion_boost: float,
    ) -> float:
        """Calculate consolidation score for a snapshot"""
        score = snapshot.salience
        
        # Access frequency boost
        if snapshot.access_count >= 3:
            score += min(0.2, snapshot.access_count * 0.03)
        
        # Emotion boost (from metadata if available)
        emotion_intensity = snapshot.metadata.get('emotion_intensity', 0.0)
        if emotion_intensity > 0.5:
            score += emotion_boost * emotion_intensity
        
        return min(1.0, score)
    
    # ========================================================================
    # DECAY: Ebbinghaus Forgetting Curve
    # ========================================================================
    
    def decay(
        self,
        agent_id: Optional[str] = None,
        min_age_seconds: float = 3600,  # At least 1 hour old
    ) -> DecayResult:
        """
        Apply decay to memories based on Ebbinghaus forgetting curve.
        
        Formula: strength *= exp(-decay_rate * hours_since_access)
        
        Args:
            agent_id: Filter by agent
            min_age_seconds: Only decay memories older than this
            
        Returns:
            DecayResult with counts
        """
        # Get candidates for decay
        candidates = self._storage.get_snapshots_for_decay(
            agent_id=agent_id,
            min_age_seconds=min_age_seconds,
        )
        
        processed = 0
        forgotten = 0
        now = datetime.now()
        
        for snapshot in candidates:
            # Calculate time since last access
            if snapshot.last_accessed:
                if isinstance(snapshot.last_accessed, str):
                    last_accessed = datetime.fromisoformat(snapshot.last_accessed.replace('Z', '+00:00'))
                else:
                    last_accessed = snapshot.last_accessed
                    
                # Handle timezone-aware vs naive datetime
                if last_accessed.tzinfo is not None:
                    from datetime import timezone
                    now_aware = datetime.now(timezone.utc)
                    hours_passed = (now_aware - last_accessed).total_seconds() / 3600
                else:
                    hours_passed = (now - last_accessed).total_seconds() / 3600
            else:
                hours_passed = min_age_seconds / 3600
            
            # Apply Ebbinghaus decay
            decay_factor = math.exp(-self._decay_rate * hours_passed)
            new_strength = snapshot.strength * decay_factor
            
            if new_strength < self._forget_threshold:
                # Memory too weak, will be forgotten
                forgotten += 1
                new_strength = 0.0
            
            # Update in storage
            self._storage.update_snapshot(
                snapshot_id=snapshot.id,
                strength=new_strength,
            )
            processed += 1
        
        self._stats['decay_cycles'] += 1
        self._stats['total_forgotten'] += forgotten
        
        self.logger.debug(f"[LTM] Decay cycle: processed={processed}, forgotten={forgotten}")
        
        return DecayResult(processed=processed, forgotten=forgotten)
    
    # ========================================================================
    # REHEARSAL: Access Strengthens Memory
    # ========================================================================
    
    def rehearse(self, snapshot_id: int, boost: float = 0.1) -> bool:
        """
        Strengthen a memory through access (rehearsal).
        
        Args:
            snapshot_id: Memory to strengthen
            boost: Amount to increase strength
            
        Returns:
            Success status
        """
        # Get current snapshot
        snapshots = self._storage.get_recent_snapshots(n=1000)
        target = None
        for s in snapshots:
            if s.id == snapshot_id:
                target = s
                break
        
        if not target:
            return False
        
        # Strengthen
        new_strength = min(1.0, target.strength + boost)
        new_access_count = target.access_count + 1
        
        return self._storage.update_snapshot(
            snapshot_id=snapshot_id,
            strength=new_strength,
            access_count=new_access_count,
            last_accessed=datetime.now(),
        )
    
    # ========================================================================
    # FORGETTING: Remove Weak Memories
    # ========================================================================
    
    def forget(
        self,
        agent_id: Optional[str] = None,
        strength_threshold: Optional[float] = None,
    ) -> int:
        """
        Remove memories with strength below threshold.
        
        Args:
            agent_id: Filter by agent
            strength_threshold: Remove if strength < this (default: forget_threshold)
            
        Returns:
            Number of memories forgotten
        """
        threshold = strength_threshold or self._forget_threshold
        
        deleted = self._storage.delete_snapshots(
            agent_id=agent_id,
            strength_lt=threshold,
        )
        
        self._stats['total_forgotten'] += deleted
        self.logger.info(f"[LTM] Forgot {deleted} weak memories (threshold={threshold})")
        
        return deleted
    
    # ========================================================================
    # RETRIEVAL: Similarity-Based Search
    # ========================================================================
    
    def retrieve_similar(
        self,
        state_vector: Tuple[float, ...],
        limit: int = 5,
        tolerance: float = 0.5,
        agent_id: Optional[str] = None,
        min_consolidation_level: int = 0,
        update_access: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar memories from LTM.
        
        Args:
            state_vector: Query vector
            limit: Max results
            tolerance: Distance threshold
            agent_id: Filter by agent
            min_consolidation_level: Only return consolidated memories
            update_access: Whether to update access time/count
            
        Returns:
            List of similar memories with distance/similarity scores
        """
        results = self._storage.find_similar_snapshots(
            state_vector=state_vector,
            limit=limit * 2,  # Get extra, filter by consolidation
            tolerance=tolerance,
            agent_id=agent_id,
        )
        
        # Filter by consolidation level
        filtered = [
            r for r in results 
            if r['snapshot'].consolidation_level >= min_consolidation_level
        ][:limit]
        
        # Update access for retrieved memories (rehearsal effect)
        if update_access and filtered:
            for r in filtered:
                self.rehearse(r['snapshot'].id, boost=0.05)
        
        return filtered
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get LTM statistics"""
        storage_stats = self._storage.get_stats()
        
        return {
            **self._stats,
            'storage': storage_stats,
            'config': {
                'decay_rate': self._decay_rate,
                'consolidation_threshold': self._consolidation_threshold,
                'forget_threshold': self._forget_threshold,
            },
        }


# Factory function
def create_ltm_manager(
    storage_type: str = "postgres",
    agent_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> LTMManager:
    """Create an LTMManager instance"""
    storage = get_storage(storage_type, agent_id=agent_id)
    return LTMManager(storage=storage, agent_id=agent_id, config=config)

# core/memory/types.py
"""
Memory module type definitions.

Provides MemoryResult class as specified in master document.
Alias/wrapper to MemoryContext for architectural consistency.

Author: UEM Project
Date: 30 November 2025
Version: 1.0 (Hybrid/Alias Strategy per Alice decision)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.unified_types import MemoryContext


@dataclass
class MemoryResult:
    """
    Memory retrieval results - Document-compliant interface.
    
    Master spec: UEM_PreData_Log_Master_Implementation_Document_Fix.md Section 6.2.6
    
    PreData Fields:
        - retrieval_count: Number of memories retrieved
        - relevance_score: Average relevance of retrieved memories (0.0-1.0)
        - working_memory_load: Current WM utilization (0.0-1.0)
        - ltm_write_count: Number of items written to LTM this cycle
    """
    # Core fields
    similar_experiences: List[Dict[str, Any]] = field(default_factory=list)
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # PreData fields (v1.9)
    retrieval_count: Optional[int] = None
    relevance_score: Optional[float] = None
    working_memory_load: Optional[float] = None
    ltm_write_count: Optional[int] = None
    
    def to_memory_context(self) -> MemoryContext:
        """Convert to MemoryContext for internal use."""
        return MemoryContext(
            similar_experiences=self.similar_experiences,
            recent_events=self.recent_events,
            retrieval_count=self.retrieval_count,
            memory_relevance=self.relevance_score,
            working_memory_load=self.working_memory_load,
            ltm_write_count=self.ltm_write_count,
        )
    
    @classmethod
    def from_memory_context(cls, ctx: MemoryContext) -> "MemoryResult":
        """Create from existing MemoryContext."""
        return cls(
            similar_experiences=ctx.similar_experiences,
            recent_events=ctx.recent_events,
            retrieval_count=ctx.retrieval_count,
            relevance_score=ctx.memory_relevance,
            working_memory_load=ctx.working_memory_load,
            ltm_write_count=ctx.ltm_write_count,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            'similar_experiences_count': len(self.similar_experiences),
            'recent_events_count': len(self.recent_events),
            'retrieval_count': self.retrieval_count,
            'relevance_score': self.relevance_score,
            'working_memory_load': self.working_memory_load,
            'ltm_write_count': self.ltm_write_count,
        }


__all__ = ['MemoryResult', 'MemoryContext']

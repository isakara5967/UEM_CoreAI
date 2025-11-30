# core/consciousness/types.py
"""
Consciousness module type definitions.

Provides WorkspaceState class as specified in master document.
Alias/wrapper to BroadcastMessage for architectural consistency.

Author: UEM Project
Date: 30 November 2025
Version: 1.0 (Hybrid/Alias Strategy per Alice decision)
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
import time

from core.consciousness.global_workspace import (
    BroadcastMessage,
    Coalition,
    ContentType,
    BroadcastPriority,
)


@dataclass
class WorkspaceState:
    """
    Workspace/Consciousness state - Document-compliant interface.
    
    Master spec: UEM_PreData_Log_Master_Implementation_Document_Fix.md Section 6.2.5
    
    PreData Fields:
        - coalition_strength: Winning coalition's activation strength (0.0-1.0)
        - broadcast_content: Content being broadcast to global workspace
        - competition_intensity: How competitive was the coalition selection (0.0-1.0)
        - conscious_threshold: Threshold used for conscious access (0.0-1.0)
    """
    # PreData fields (v1.9)
    coalition_strength: Optional[float] = None
    broadcast_content: Optional[Dict[str, Any]] = None
    competition_intensity: Optional[float] = None
    conscious_threshold: Optional[float] = None
    
    # Additional context
    content_type: Optional[str] = None
    cycle_number: Optional[int] = None
    timestamp: Optional[float] = None
    
    @classmethod
    def from_broadcast_message(cls, msg: BroadcastMessage) -> "WorkspaceState":
        """Create from existing BroadcastMessage."""
        return cls(
            coalition_strength=msg.coalition_strength,
            broadcast_content=msg.content,
            competition_intensity=msg.competition_intensity,
            conscious_threshold=msg.conscious_threshold,
            content_type=msg.content_type.value if msg.content_type else None,
            cycle_number=msg.cycle_number,
            timestamp=msg.timestamp,
        )
    
    def to_broadcast_message(
        self,
        coalition: Coalition,
        content_type: ContentType = ContentType.GOAL,
        priority: BroadcastPriority = BroadcastPriority.NORMAL,
    ) -> BroadcastMessage:
        """Convert to BroadcastMessage for internal use."""
        return BroadcastMessage(
            coalition=coalition,
            content_type=content_type,
            content=self.broadcast_content or {},
            timestamp=self.timestamp or time.time(),
            cycle_number=self.cycle_number or 0,
            priority=priority,
            coalition_strength=self.coalition_strength,
            competition_intensity=self.competition_intensity,
            conscious_threshold=self.conscious_threshold,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            'coalition_strength': self.coalition_strength,
            'broadcast_content': self.broadcast_content,
            'competition_intensity': self.competition_intensity,
            'conscious_threshold': self.conscious_threshold,
            'content_type': self.content_type,
            'cycle_number': self.cycle_number,
        }


__all__ = ['WorkspaceState', 'BroadcastMessage', 'Coalition', 'ContentType', 'BroadcastPriority']

# core/memory/short_term/short_term_memory.py
"""
Short-Term Memory with Decay

Holds recent perceptions with activation-based decay.
Items lose activation over time unless refreshed.

Author: UEM Project
"""

from __future__ import annotations

import math
import time
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Optional, Any

from core.perception.types import PerceptionResult


@dataclass
class STMItem:
    """Item in STM with activation tracking"""
    content: Any
    timestamp: float = field(default_factory=time.time)
    activation: float = 1.0
    salience: float = 0.5
    access_count: int = 0
    
    def refresh(self, boost: float = 0.2) -> None:
        """Refresh activation on access"""
        self.activation = min(1.0, self.activation + boost)
        self.access_count += 1


class ShortTermMemory:
    """
    Short-term memory with decay.
    
    - Holds last N perceptions (default: 20)
    - Activation decays over time
    - High salience items decay slower
    - Items below threshold can be pruned
    """

    def __init__(
        self,
        capacity: int = 20,
        decay_rate: float = 0.1,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.capacity = max(1, int(capacity))
        self.decay_rate = decay_rate
        self._buffer: Deque[STMItem] = deque(maxlen=self.capacity)
        self._last_decay_time: float = time.time()
        self.logger = logger or logging.getLogger("core.memory.ShortTermMemory")

    # ------------------------------------------------------------------ #
    # Core API
    # ------------------------------------------------------------------ #

    def store(self, content: Any, salience: float = 0.5) -> None:
        """Store item in STM with initial activation=1.0"""
        item = STMItem(
            content=content,
            timestamp=time.time(),
            activation=1.0,
            salience=salience,
        )
        self._buffer.append(item)
        self.logger.debug("[STM] Stored (salience=%.2f, size=%d)", salience, len(self._buffer))

    def store_perception(self, perception: PerceptionResult) -> None:
        """Store perception (backward compatible)"""
        salience = getattr(perception.environment_state, 'danger_level', 0.5)
        self.store(perception, salience=salience)

    def decay_all(self, delta_time: Optional[float] = None) -> int:
        """
        Apply exponential decay to all items.
        High salience items decay slower.
        Returns: Number of items below threshold
        """
        now = time.time()
        if delta_time is None:
            delta_time = now - self._last_decay_time
        self._last_decay_time = now
        
        dropped = 0
        for item in self._buffer:
            effective_decay = self.decay_rate * (1.0 - item.salience * 0.5)
            item.activation *= math.exp(-effective_decay * delta_time)
            if item.activation < 0.1:
                dropped += 1
        
        return dropped

    def get_active_items(self, threshold: float = 0.3) -> List[STMItem]:
        """Get items with activation above threshold"""
        return [item for item in self._buffer if item.activation >= threshold]

    def get_by_activation(self, limit: int = 5) -> List[STMItem]:
        """Get top N items sorted by activation"""
        sorted_items = sorted(self._buffer, key=lambda x: x.activation, reverse=True)
        return sorted_items[:limit]

    def refresh_item(self, index: int, boost: float = 0.2) -> bool:
        """Refresh item at index (rehearsal effect)"""
        if 0 <= index < len(self._buffer):
            self._buffer[index].refresh(boost)
            return True
        return False

    def prune_weak(self, threshold: float = 0.1) -> int:
        """Remove items below activation threshold"""
        initial_size = len(self._buffer)
        self._buffer = deque(
            [item for item in self._buffer if item.activation >= threshold],
            maxlen=self.capacity
        )
        return initial_size - len(self._buffer)

    # ------------------------------------------------------------------ #
    # Legacy API
    # ------------------------------------------------------------------ #

    def get_last(self) -> Optional[Any]:
        """Get most recent item"""
        if not self._buffer:
            return None
        return self._buffer[-1].content

    def get_all(self) -> List[Any]:
        """Get all contents"""
        return [item.content for item in self._buffer]

    def get_all_items(self) -> List[STMItem]:
        """Get all STM items with metadata"""
        return list(self._buffer)

    def clear(self) -> None:
        """Clear all items"""
        self._buffer.clear()

    # ------------------------------------------------------------------ #
    # Stats
    # ------------------------------------------------------------------ #

    def get_stats(self) -> dict:
        """Get STM statistics"""
        if not self._buffer:
            return {'size': 0, 'capacity': self.capacity, 'avg_activation': 0.0}
        
        activations = [item.activation for item in self._buffer]
        return {
            'size': len(self._buffer),
            'capacity': self.capacity,
            'avg_activation': sum(activations) / len(activations),
            'min_activation': min(activations),
            'max_activation': max(activations),
        }

    def __len__(self) -> int:
        return len(self._buffer)

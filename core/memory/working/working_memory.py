# core/memory/working/working_memory.py
"""
Working Memory with Attention Focus

Active workspace for decision-making.
Limited slots with attention mechanism.
Prepared for multi-focus extension (P2).

Author: UEM Project
"""

from __future__ import annotations

import math
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from core.perception.types import (
    EnvironmentState,
    PerceptionResult,
    PerceivedObject,
)


@dataclass
class WMSlot:
    """A slot in working memory"""
    key: str
    content: Any
    timestamp: float = field(default_factory=time.time)
    activation: float = 1.0
    salience: float = 0.5
    
    def refresh(self) -> None:
        """Refresh activation when focused"""
        self.activation = 1.0
        self.timestamp = time.time()


@dataclass
class WorkingMemoryState:
    """Summary state for planning/decision systems (legacy)"""
    tick: int = 0
    danger_level: float = 0.0
    nearest_target: Optional[PerceivedObject] = None
    visible_objects: int = 0
    visible_agents: int = 0
    symbols: List[str] = field(default_factory=list)
    notes: str = ""


class WorkingMemory:
    """
    Working Memory with Attention Focus.
    
    - Configurable capacity (default: 8)
    - Single attention focus (multi-focus ready for P2)
    - Lowest activation evicted when full
    """

    def __init__(
        self,
        capacity: int = 8,
        max_focus_items: int = 1,  # P2: increase for multi-focus
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.capacity = capacity
        self.max_focus_items = max_focus_items
        self.logger = logger or logging.getLogger("core.memory.WorkingMemory")
        
        # Slot-based storage
        self._slots: Dict[str, WMSlot] = {}
        
        # Attention state (single focus for now)
        self._attention_focus: Optional[str] = None
        
        # P2 ready: weighted attention distribution
        self._attention_weights: Dict[str, float] = {}
        
        # History
        self._focus_history: List[str] = []
        
        # Legacy state
        self._state = WorkingMemoryState()

    # ------------------------------------------------------------------ #
    # Slot API
    # ------------------------------------------------------------------ #

    def load(self, key: str, content: Any, salience: float = 0.5) -> bool:
        """Load content into a slot. Evicts lowest if at capacity."""
        if key in self._slots:
            self._slots[key].content = content
            self._slots[key].salience = salience
            self._slots[key].refresh()
            return True
        
        if len(self._slots) >= self.capacity:
            self._evict_lowest_activation()
        
        self._slots[key] = WMSlot(key=key, content=content, salience=salience)
        self.logger.debug("[WM] Loaded '%s' (size=%d)", key, len(self._slots))
        return True

    def get(self, key: str) -> Optional[Any]:
        """Get content from slot"""
        if key in self._slots:
            return self._slots[key].content
        return None

    def remove(self, key: str) -> bool:
        """Remove a slot"""
        if key in self._slots:
            del self._slots[key]
            if self._attention_focus == key:
                self._attention_focus = None
            self._attention_weights.pop(key, None)
            return True
        return False

    # ------------------------------------------------------------------ #
    # Attention API
    # ------------------------------------------------------------------ #

    def focus_attention(self, key: str) -> bool:
        """Focus attention on a slot. Refreshes its activation."""
        if key not in self._slots:
            return False
        
        self._slots[key].refresh()
        self._attention_focus = key
        self._focus_history.append(key)
        
        # Update weights (single focus = 100%)
        self._attention_weights = {key: 1.0}
        
        self.logger.debug("[WM] Focused on '%s'", key)
        return True

    def auto_focus(self) -> Optional[str]:
        """Focus on highest priority item (activation × salience)"""
        if not self._slots:
            return None
        
        best_key = max(
            self._slots.keys(),
            key=lambda k: self._slots[k].activation * self._slots[k].salience
        )
        
        self.focus_attention(best_key)
        return best_key

    def get_focus(self) -> Optional[str]:
        """Get current attention focus"""
        return self._attention_focus

    def get_focused_content(self) -> Optional[Any]:
        """Get content of focused slot"""
        if self._attention_focus and self._attention_focus in self._slots:
            return self._slots[self._attention_focus].content
        return None

    def get_attention_weights(self) -> Dict[str, float]:
        """Get attention distribution (P2 ready)"""
        return self._attention_weights.copy()

    # ------------------------------------------------------------------ #
    # P2 Ready: Multi-Focus (not active yet)
    # ------------------------------------------------------------------ #

    def set_attention_distribution(self, weights: Dict[str, float]) -> bool:
        """
        Set weighted attention distribution.
        P2 feature - foundation ready.
        
        Example: {'threat': 0.5, 'goal': 0.3, 'resource': 0.2}
        """
        if self.max_focus_items == 1:
            # Single focus mode - use highest weight
            if weights:
                best = max(weights.keys(), key=lambda k: weights[k])
                return self.focus_attention(best)
            return False
        
        # Multi-focus mode (P2)
        total = sum(weights.values())
        if total > 0:
            self._attention_weights = {k: v/total for k, v in weights.items()}
            self._attention_focus = max(weights.keys(), key=lambda k: weights[k])
            return True
        return False

    # ------------------------------------------------------------------ #
    # Decay & Eviction
    # ------------------------------------------------------------------ #

    def decay_all(self, delta_time: float, decay_rate: float = 0.05) -> None:
        """Apply decay to non-focused slots"""
        for key, slot in self._slots.items():
            if key != self._attention_focus:
                slot.activation *= math.exp(-decay_rate * delta_time)

    def _evict_lowest_activation(self) -> Optional[str]:
        """Evict slot with lowest activation (protect focused)"""
        if not self._slots:
            return None
        
        candidates = {k: v for k, v in self._slots.items() if k != self._attention_focus}
        if not candidates:
            candidates = self._slots
        
        lowest_key = min(candidates.keys(), key=lambda k: candidates[k].activation)
        del self._slots[lowest_key]
        self._attention_weights.pop(lowest_key, None)
        
        self.logger.debug("[WM] Evicted '%s'", lowest_key)
        return lowest_key

    # ------------------------------------------------------------------ #
    # Legacy API
    # ------------------------------------------------------------------ #

    def update_from_perception(self, perception: PerceptionResult) -> None:
        """Update from perception (backward compatible)"""
        env: EnvironmentState = perception.environment_state

        self._state = WorkingMemoryState(
            tick=perception.snapshot.tick,
            danger_level=env.danger_level,
            nearest_target=env.nearest_target,
            visible_objects=len(perception.objects),
            visible_agents=len(perception.agents),
            symbols=list(perception.symbols),
            notes=env.notes,
        )
        
        if env.danger_level > 0.5:
            self.load('danger', {'level': env.danger_level}, salience=env.danger_level)
        
        if env.nearest_target:
            self.load('target', env.nearest_target, salience=0.7)

    def get_state(self) -> WorkingMemoryState:
        """Get legacy state"""
        return self._state

    def clear(self) -> None:
        """Clear all"""
        self._slots.clear()
        self._attention_focus = None
        self._attention_weights.clear()
        self._state = WorkingMemoryState()

    # ------------------------------------------------------------------ #
    # Stats
    # ------------------------------------------------------------------ #

    def get_slots(self) -> Dict[str, WMSlot]:
        """Get all slots"""
        return self._slots.copy()

    def get_stats(self) -> dict:
        """Get WM statistics"""
        return {
            'size': len(self._slots),
            'capacity': self.capacity,
            'max_focus_items': self.max_focus_items,
            'attention_focus': self._attention_focus,
            'attention_weights': self._attention_weights,
            'slot_keys': list(self._slots.keys()),
        }

    def __len__(self) -> int:
        return len(self._slots)

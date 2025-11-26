# core/self/self_v2_memory_patch.py
"""
SELF v2 Memory Integration Patch

This patch adds memory writing capability to SelfCore.
Apply this by copying the methods to self_core.py or importing.

Changes:
1. _write_to_memory() now actually writes to Memory
2. Periodic snapshot saving
3. Event writing on state changes

Author: UEM Project
Date: 26 November 2025
"""

# =============================================================================
# PATCH INSTRUCTIONS
# =============================================================================
# 
# Replace the existing _write_to_memory() method in self_core.py with:
#
# def _write_to_memory(self) -> None:
#     """v2: Write state snapshot to Memory system (if available)."""
#     if self.memory_system is None:
#         return
#     
#     # Only write every N ticks to avoid spam
#     write_interval = self.config.get('memory_write_interval', 10)
#     if self._tick_count % write_interval != 0:
#         return
#     
#     try:
#         # Build and store snapshot
#         snapshot = self.build_self_entity()
#         if hasattr(self.memory_system, 'store_state_snapshot'):
#             self.memory_system.store_state_snapshot(snapshot)
#     except Exception as e:
#         if self.logger:
#             self.logger.debug(f"[SELF] Memory write failed: {e}")
#
# =============================================================================


def patched_write_to_memory(self) -> None:
    """
    v2: Write state snapshot to Memory system (if available).
    
    This method is called at the end of each update cycle.
    It writes periodic snapshots to long-term memory for:
    - Autobiographical continuity
    - Experience-based learning
    - Empathy (finding similar past states)
    """
    if self.memory_system is None:
        return
    
    # Only write every N ticks to avoid spam
    write_interval = self.config.get('memory_write_interval', 10)
    if self._tick_count % write_interval != 0:
        return
    
    try:
        # Build current snapshot
        snapshot = self.build_self_entity()
        
        # Store via MemoryInterface
        if hasattr(self.memory_system, 'store_state_snapshot'):
            self.memory_system.store_state_snapshot(snapshot)
        
        # Log if significant state change
        if self._state_delta is not None:
            delta_magnitude = sum(abs(d) for d in self._state_delta)
            if delta_magnitude > 0.3:  # Significant change
                if self.logger:
                    self.logger.debug(
                        f"[SELF] Stored significant state change (delta={delta_magnitude:.2f})"
                    )
    
    except Exception as e:
        if self.logger:
            self.logger.debug(f"[SELF] Memory write failed: {e}")


def patched_record_event(self, event) -> None:
    """
    Record an event to history.
    
    v2: Also writes to Memory if available.
    """
    self._event_history.append(event)
    
    # v2: Also write to Memory if available
    if self.memory_system is not None and hasattr(self.memory_system, 'store_event'):
        try:
            self.memory_system.store_event(event)
        except Exception:
            pass


# =============================================================================
# SELF CONFIG ADDITIONS
# =============================================================================
# Add these to SelfCore.DEFAULT_CONFIG:
#
# 'memory_write_interval': 10,  # Write snapshot every N ticks
# 'memory_significant_delta': 0.3,  # Delta threshold for logging
#
# =============================================================================

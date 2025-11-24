from __future__ import annotations

"""Continuity unit for the SELF system.

Tracks self-continuity and narrative state over time by integrating
episodic and emotional memory into a compact "story of self".
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..self_core import SelfCore


class ContinuityUnit:
    """Maintains the narrative and temporal continuity of SELF."""

    def __init__(self, core: "SelfCore") -> None:
        self.core = core
        self.narrative_summary: str = ""
        self.timeline_markers: List[Dict[str, Any]] = []
        self._max_markers: int = 50

    def start(self) -> None:
        """Initialization that may depend on memory systems.

        İlk başlatmada, eğer MemoryCore SELF için özet API sunuyorsa
        oradan başlangıç anlatısını kurmayı dener.
        """
        memory = getattr(self.core, "memory_system", None)
        if memory is not None and hasattr(memory, "get_self_view"):
            try:
                view = memory.get_self_view()
                episodes = view.get("episodes") or []
                self.timeline_markers = list(episodes[-self._max_markers :])
                self.narrative_summary = self._build_narrative_summary(view)
            except Exception:
                self.narrative_summary = ""
                self.timeline_markers = []

    def update(
        self,
        dt: float,
        world_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update narrative continuity if new salient events appear."""
        memory = getattr(self.core, "memory_system", None)
        if memory is None or not hasattr(memory, "get_self_view"):
            return

        try:
            view = memory.get_self_view()
        except Exception:
            return

        episodes = view.get("episodes") or []
        if not isinstance(episodes, list):
            return

        self.timeline_markers = list(episodes[-self._max_markers :])
        self.narrative_summary = self._build_narrative_summary(view)

    def _build_narrative_summary(self, self_view: Dict[str, Any]) -> str:
        """Derive a compact textual narrative summary from memory view."""
        episodes = self_view.get("episodes") or []
        emotional = self_view.get("emotional_profile") or {}

        event_count = len(episodes)

        mood = "unknown"
        try:
            vals = emotional.get("recent_valence") or []
            if isinstance(vals, list) and vals:
                nums = [v for v in vals if isinstance(v, (int, float))]
                if nums:
                    avg = sum(nums) / len(nums)
                    if avg > 0.2:
                        mood = "mostly_positive"
                    elif avg < -0.2:
                        mood = "mostly_negative"
                    else:
                        mood = "mixed"
        except Exception:
            pass

        dominant_emotion = emotional.get("dominant_emotion")
        if dominant_emotion:
            return (
                f"{event_count} self-relevant events; "
                f"mood={mood}; dominant_emotion={dominant_emotion}"
            )
        else:
            return f"{event_count} self-relevant events; mood={mood}"

    def export_state(self) -> Dict[str, Any]:
        """Return a serializable snapshot of narrative self state."""
        return {
            "narrative_summary": self.narrative_summary,
            "timeline_markers": list(self.timeline_markers),
        }

    def notify_event(self, event: Dict[str, Any]) -> None:
        """Update timeline markers for self-relevant events."""
        if not isinstance(event, dict):
            return

        marker = {
            "type": event.get("type", "event"),
            "timestamp": event.get("timestamp"),
            "label": event.get("label") or event.get("content"),
        }
        self.timeline_markers.append(marker)
        if len(self.timeline_markers) > self._max_markers:
            self.timeline_markers = self.timeline_markers[-self._max_markers :]

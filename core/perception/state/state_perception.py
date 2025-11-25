from __future__ import annotations

import logging
from typing import List, Optional

from core.perception.types import (
    EnvironmentState,
    PerceivedObject,
    PerceivedAgent,
    WorldSnapshot,
)


class StatePerception:
    """
    Nesneler ve ajanlardan, UEM için kullanılabilir özet bir EnvironmentState çıkarır.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def _compute_danger_level(self, objects: List[PerceivedObject]) -> float:
        if not objects:
            return 0.0

        dangerous = [o for o in objects if o.is_dangerous]
        if not dangerous:
            return 0.0

        min_dist = min(o.distance for o in dangerous)
        # Çok kaba bir ölçekleme: yakın tehlike -> yüksek skor
        level = max(0.0, min(1.0, 1.0 - min_dist / 50.0))
        return level

    def _nearest(self, objs: List[PerceivedObject], predicate) -> Optional[PerceivedObject]:
        candidates = [o for o in objs if predicate(o)]
        if not candidates:
            return None
        return min(candidates, key=lambda o: o.distance)

    def infer_state(
        self,
        snapshot: WorldSnapshot,
        objects: List[PerceivedObject],
        agents: List[PerceivedAgent],
    ) -> EnvironmentState:
        danger_level = self._compute_danger_level(objects)
        nearest_danger = self._nearest(objects, lambda o: o.is_dangerous)
        nearest_target = self._nearest(objects, lambda o: o.is_interactable)

        notes_parts: List[str] = []
        if danger_level > 0.7:
            notes_parts.append("High danger nearby.")
        elif danger_level > 0.0:
            notes_parts.append("Some danger in area.")

        if nearest_target is not None:
            notes_parts.append(f"Target visible: {nearest_target.obj_type} (dist={nearest_target.distance:.1f}).")

        notes = " ".join(notes_parts)

        env_state = EnvironmentState(
            danger_level=danger_level,
            nearest_danger=nearest_danger,
            nearest_target=nearest_target,
            notes=notes,
        )

        self.logger.debug(
            "[Perception][StatePerception] danger=%.2f, nearest_target=%s",
            danger_level,
            nearest_target.id if nearest_target else None,
        )

        return env_state

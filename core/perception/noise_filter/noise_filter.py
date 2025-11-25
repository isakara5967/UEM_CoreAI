from __future__ import annotations

import logging
from typing import Any, Dict, List

from core.perception.types import WorldSnapshot, Vec3


class NoiseFilter:
    """
    Ham world snapshot içindeki gürültüyü ayıklayan basit filtre.
    lk versiyon: None/bozuk değerleri atar, çok uzaktaki nesneleri keser.
    """

    def __init__(self, max_distance: float = 100.0, logger: logging.Logger | None = None) -> None:
        self.max_distance = max_distance
        self.logger = logger or logging.getLogger(__name__)

    def _distance(self, a: Vec3, b: Vec3) -> float:
        ax, ay, az = a
        bx, by, bz = b
        dx = ax - bx
        dy = ay - by
        dz = az - bz
        return (dx * dx + dy * dy + dz * dz) ** 0.5

    def _filter_objects(self, agent_pos: Vec3, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned: List[Dict[str, Any]] = []
        for obj in objects:
            pos = obj.get("position")
            if not isinstance(pos, (list, tuple)) or len(pos) != 3:
                continue

            try:
                position: Vec3 = (float(pos[0]), float(pos[1]), float(pos[2]))
            except (TypeError, ValueError):
                continue

            dist = self._distance(agent_pos, position)
            if dist > self.max_distance:
                continue

            obj = dict(obj)
            obj["position"] = position
            obj["distance"] = dist
            cleaned.append(obj)

        return cleaned

    def process(self, snapshot: WorldSnapshot) -> WorldSnapshot:
        """
        WorldSnapshot -> temizlenmiş WorldSnapshot

        NOT: şimdilik sadece objects üzerinde çalışıyor.
        """
        cleaned_objects = self._filter_objects(snapshot.agent_position, snapshot.objects)

        if len(cleaned_objects) != len(snapshot.objects):
            self.logger.debug(
                "[Perception][NoiseFilter] Objects filtered: %s -> %s",
                len(snapshot.objects),
                len(cleaned_objects),
            )

        return WorldSnapshot(
            tick=snapshot.tick,
            timestamp=snapshot.timestamp,
            agent_position=snapshot.agent_position,
            objects=cleaned_objects,
            agents=snapshot.agents,
            environment=snapshot.environment,
        )

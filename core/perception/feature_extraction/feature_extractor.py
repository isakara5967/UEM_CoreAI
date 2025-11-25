from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from core.perception.types import (
    PerceivedAgent,
    PerceivedObject,
    Vec3,
    WorldSnapshot,
)


class FeatureExtractor:
    """
    Gürültüden arındırılmış WorldSnapshot'tan PerceivedObject / PerceivedAgent üretir.
    lk versiyon tamamen kural tabanlıdır.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def _extract_objects(self, snapshot: WorldSnapshot) -> List[PerceivedObject]:
        result: List[PerceivedObject] = []
        for idx, obj in enumerate(snapshot.objects):
            obj_id = obj.get("id") or f"obj_{idx}"
            obj_type = obj.get("type") or "unknown"
            pos: Vec3 = obj.get("position", snapshot.agent_position)  # type: ignore[assignment]
            dist = float(obj.get("distance", 0.0))

            tags: List[str] = obj.get("tags", []) or []
            is_dangerous = "danger" in tags or obj.get("is_dangerous", False)
            is_interactable = "interactable" in tags or obj.get("is_interactable", False)

            po = PerceivedObject(
                id=str(obj_id),
                obj_type=str(obj_type),
                position=pos,
                distance=dist,
                is_dangerous=bool(is_dangerous),
                is_interactable=bool(is_interactable),
                raw=obj,
            )
            result.append(po)

        self.logger.debug("[Perception][FeatureExtractor] Extracted %s objects", len(result))
        return result

    def _extract_agents(self, snapshot: WorldSnapshot) -> List[PerceivedAgent]:
        result: List[PerceivedAgent] = []
        for idx, ag in enumerate(snapshot.agents):
            ag_id = ag.get("id") or f"agent_{idx}"
            ag_type = ag.get("type") or "AGENT"
            pos_raw = ag.get("position") or snapshot.agent_position

            try:
                pos: Vec3 = (float(pos_raw[0]), float(pos_raw[1]), float(pos_raw[2]))  # type: ignore[index]
            except Exception:
                pos = snapshot.agent_position

            relation = ag.get("relation")

            pa = PerceivedAgent(
                id=str(ag_id),
                agent_type=str(ag_type),
                position=pos,
                relation=str(relation) if relation is not None else None,
                raw=ag,
            )
            result.append(pa)

        self.logger.debug("[Perception][FeatureExtractor] Extracted %s agents", len(result))
        return result

    def process(self, snapshot: WorldSnapshot) -> Tuple[List[PerceivedObject], List[PerceivedAgent]]:
        objects = self._extract_objects(snapshot)
        agents = self._extract_agents(snapshot)
        return objects, agents

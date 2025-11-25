from __future__ import annotations

import logging
from typing import List

from core.perception.types import (
    EnvironmentState,
    PerceivedObject,
    PerceivedAgent,
)


class SymbolicPerception:
    """
    EnvironmentState + algılanan nesnelerden sembolik etiketler çıkarır.
    Bu etiketler Cognition / Planning / Ethmor tarafından kullanılabilir.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def infer_symbols(
        self,
        env_state: EnvironmentState,
        objects: List[PerceivedObject],
        agents: List[PerceivedAgent],
    ) -> List[str]:
        symbols: List[str] = []

        if env_state.danger_level >= 0.7:
            symbols.append("DANGER_HIGH")
        elif env_state.danger_level > 0.0:
            symbols.append("DANGER_LOW")

        if env_state.nearest_target is not None:
            symbols.append("TARGET_VISIBLE")

        if not objects and not agents:
            symbols.append("SCENE_EMPTY")

        if agents:
            symbols.append("AGENT_IN_SIGHT")

        self.logger.debug("[Perception][SymbolicPerception] symbols=%s", symbols)
        return symbols

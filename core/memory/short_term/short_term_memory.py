from __future__ import annotations

import logging
from collections import deque
from typing import Deque, List, Optional

from core.perception.types import PerceptionResult


class ShortTermMemory:
    """
    Son N adet PerceptionResult'ı tutan kısa süreli hafıza.
    Bu yapı, milisaniyeler / birkaç saniyelik algı geçmişini temsil eder.
    """

    def __init__(
        self,
        capacity: int = 10,
        logger: logging.Logger | None = None,
    ) -> None:
        self.capacity = max(1, int(capacity))
        self._buffer: Deque[PerceptionResult] = deque(maxlen=self.capacity)
        self.logger = logger or logging.getLogger("core.memory.ShortTermMemory")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def store_perception(self, perception: PerceptionResult) -> None:
        """
        Son perception'ı hafızaya ekler.
        """
        self._buffer.append(perception)
        self.logger.debug(
            "[Memory][STM] stored perception (tick=%s, size=%d)",
            perception.snapshot.tick,
            len(self._buffer),
        )

    def get_last(self) -> Optional[PerceptionResult]:
        """
        En son perception.
        """
        if not self._buffer:
            return None
        return self._buffer[-1]

    def get_all(self) -> List[PerceptionResult]:
        """
        Bütün kısa süreli perception geçmişini listeler (kopya).
        """
        return list(self._buffer)

    def clear(self) -> None:
        """
        Tüm kısa süreli hafızayı temizler.
        """
        self._buffer.clear()
        self.logger.debug("[Memory][STM] cleared.")

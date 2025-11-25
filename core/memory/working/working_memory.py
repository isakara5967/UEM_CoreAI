from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from core.perception.types import (
    EnvironmentState,
    PerceptionResult,
    PerceivedObject,
)


@dataclass
class WorkingMemoryState:
    """
    Karar verme ve planlama için kullanılan, o ana ait özet zihin durumu.
    """
    tick: int = 0
    danger_level: float = 0.0
    nearest_target: Optional[PerceivedObject] = None
    visible_objects: int = 0
    visible_agents: int = 0
    symbols: List[str] = field(default_factory=list)
    notes: str = ""


class WorkingMemory:
    """
    Kısa süreli hafızadan beslenen, aktif olarak kullanılan çalışma alanı.
    Planlama, duygu ve etik sistemleri buradan bilgi okuyabilir.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("core.memory.WorkingMemory")
        self._state = WorkingMemoryState()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def update_from_perception(self, perception: PerceptionResult) -> None:
        """
        Son perception'dan özet çalışma durumunu çıkarır.
        """
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

        self.logger.debug(
            "[Memory][WM] updated: tick=%s danger=%.2f objs=%d agents=%d symbols=%s",
            self._state.tick,
            self._state.danger_level,
            self._state.visible_objects,
            self._state.visible_agents,
            self._state.symbols,
        )

    def get_state(self) -> WorkingMemoryState:
        """
        Şu anki çalışma durumu (kopya değil referans; sadece read-only kullan).
        """
        return self._state

    def clear(self) -> None:
        """
        Çalışan hafızayı sıfırlar.
        """
        self._state = WorkingMemoryState()
        self.logger.debug("[Memory][WM] cleared.")

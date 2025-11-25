from __future__ import annotations

import logging
from typing import Any, Optional

from core.perception.types import PerceptionResult
from core.memory.short_term.short_term_memory import ShortTermMemory
from core.memory.working.working_memory import WorkingMemory, WorkingMemoryState


class MemoryCore:
    """
    UEM'in hafıza çekirdeği.

    Şu anki kapsam:
        - Kısa Süreli Hafıza (ShortTermMemory)
        - Çalışan Hafıza (WorkingMemory)

    Uzun vadede:
        - LongTermMemory
        - EpisodicMemory
        - SemanticMemory
        - EmotionalMemory
    gibi alt sistemler buraya eklenecek.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config = config or {}
        base_logger = logger or logging.getLogger("core.memory")
        self.logger = base_logger

        self.short_term: Optional[ShortTermMemory] = None
        self.working: Optional[WorkingMemory] = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """
        Alt hafıza sistemlerini başlatır.
        UEMCore.start() içinde çağrılması beklenir.
        """
        stm_capacity = int(self.config.get("short_term_capacity", 10))

        self.short_term = ShortTermMemory(
            capacity=stm_capacity,
            logger=self.logger.getChild("ShortTermMemory"),
        )
        self.working = WorkingMemory(
            logger=self.logger.getChild("WorkingMemory"),
        )

        self.logger.info(
            "[Memory] MemoryCore initialized (short_term_capacity=%d).",
            stm_capacity,
        )

    def update(self, dt: float) -> None:
        """
        Şu anda STM/WM için per-tick aktif bir iş yapmıyor.
        Gerektiğinde unutma, decay vb. mekanizmalar buraya eklenecek.
        """
        # Gelecekte unutma / consolidasyon vs. için kullanılacak.
        return

    # ------------------------------------------------------------------ #
    # Integration points
    # ------------------------------------------------------------------ #

    def store_perception(self, perception: PerceptionResult) -> None:
        """
        PerceptionCore tarafından çağrılır.
        Gelen perception'ı kısa süreli hafızaya yazar ve
        çalışan hafızayı günceller.
        """
        if self.short_term is None or self.working is None:
            # start() henüz çağrılmadıysa sessizce çık.
            self.logger.warning(
                "[Memory] store_perception called before start(); ignoring."
            )
            return

        self.short_term.store_perception(perception)
        self.working.update_from_perception(perception)

    # ------------------------------------------------------------------ #
    # Query helpers
    # ------------------------------------------------------------------ #

    def get_last_perception(self) -> Optional[PerceptionResult]:
        if self.short_term is None:
            return None
        return self.short_term.get_last()

    def get_recent_perceptions(self):
        if self.short_term is None:
            return []
        return self.short_term.get_all()

    def get_working_state(self) -> Optional[WorkingMemoryState]:
        if self.working is None:
            return None
        return self.working.get_state()

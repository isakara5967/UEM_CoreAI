from __future__ import annotations

import logging
from typing import Any, Optional

from core.memory.memory_core import MemoryCore
from core.memory.working.working_memory import WorkingMemoryState
from core.planning.action_selection.action_selector import (
    ActionCommand,
    ActionSelector,
)


class PlanningCore:
    """
    UEM'in planlama / karar verme çekirdeği.

    lk versiyon:
        - Çalışan hafızadan (WorkingMemoryState) durumu okur.
        - ActionSelector ile reaktif bir eylem seçer.
        - Son kararı last_action olarak saklar.
        - Eğer world_interface eylem kabul ediyorsa, komutu oraya iletmeye çalışır.

    leride:
        - Hedef yönetimi
        - Görev / alt görev ayrıştırma
        - Uzun vadeli planlama
        - RL tabanlı politika
    bu çekirdeğe eklenecek.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        memory_core: Optional[MemoryCore] = None,
        world_interface: Any | None = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config = config or {}
        self.memory = memory_core
        self.world = world_interface

        base_logger = logger or logging.getLogger("core.planning")
        self.logger = base_logger

        self.action_selector: Optional[ActionSelector] = None
        self.last_action: Optional[ActionCommand] = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """
        Planlama sistemini başlatır.
        UEMCore.start() içinde çağrılması beklenir.
        """
        self.action_selector = ActionSelector(
            logger=self.logger.getChild("ActionSelector")
        )

        self.logger.info("[Planning] PlanningCore initialized.")

    def update(self, dt: float) -> None:
        """
        Tek bir karar verme tick'i.

        Akış:
            - MemoryCore'dan WorkingMemoryState alınır.
            - ActionSelector ile eylem seçilir.
            - last_action güncellenir.
            - world_interface varsa eylem iletilmeye çalışılır.
        """
        if self.action_selector is None:
            self.logger.error("[Planning] start() not called; action_selector is None.")
            return

        if self.memory is None:
            self.logger.warning("[Planning] MemoryCore is None; skipping planning.")
            return

        wm_state = self.memory.get_working_state()
        if wm_state is None:
            # Henüz perception/memory çalışmadıysa sessiz geç.
            self.logger.debug("[Planning] No WorkingMemoryState available; skipping.")
            return

        # 1) Eylem seç
        action = self.action_selector.select_action(wm_state)
        self.last_action = action

        self.logger.debug("[Planning] Selected action: %r", action)

        # 2) Dünya arayüzüne iletmeye çalış (varsa)
        self._send_action_to_world(action, wm_state)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _send_action_to_world(
        self,
        action: ActionCommand,
        wm_state: WorkingMemoryState,
    ) -> None:
        """
        Seçilen eylemi Dünya arayüzüne iletir.

        Beklenen (ama zorunlu olmayan) world API'leri:
            - world_interface.enqueue_action(action)
              veya
            - world_interface.apply_action(action)

        Eğer bunlar yoksa sadece log yazar.
        """
        if self.world is None:
            # Şu an world entegrasyonu olmayabilir; problem değil.
            self.logger.debug("[Planning] No world interface; action not dispatched.")
            return

        # Tercih sırası: enqueue_action > apply_action
        try:
            if hasattr(self.world, "enqueue_action"):
                self.world.enqueue_action(action)
                self.logger.debug("[Planning] Action enqueued to world: %r", action)
            elif hasattr(self.world, "apply_action"):
                self.world.apply_action(action)
                self.logger.debug("[Planning] Action applied to world: %r", action)
            else:
                self.logger.debug(
                    "[Planning] World interface has no enqueue/apply; action not dispatched."
                )
        except Exception as exc:  # noqa: BLE001
            # Dünya tarafındaki hatalar planlamayı çökertmesin.
            self.logger.debug("[Planning] Failed to dispatch action to world: %s", exc)

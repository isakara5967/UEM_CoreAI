from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

from core.memory.working.working_memory import WorkingMemoryState


@dataclass
class ActionCommand:
    """
    Planning katmanının ürettiği temel eylem komutu.
    World / actuator sistemi bu komutu alıp gerçek harekete çevirebilir.
    """
    name: str
    params: Dict[str, object] = field(default_factory=dict)

    def __repr__(self) -> str:  # log'larda okunabilirlik için
        if not self.params:
            return f"ActionCommand({self.name})"
        return f"ActionCommand({self.name}, {self.params})"


class ActionSelector:
    """
    Basit reaktif karar verici.

    Girdi: WorkingMemoryState
    Çıktı: ActionCommand

    Bu ilk versiyon tamamen kural tabanlıdır.
    Daha sonra RL / planlama sistemi eklenebilir.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("core.planning.ActionSelector")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def select_action(self, wm: WorkingMemoryState) -> ActionCommand:
        """
        Çalışan hafıza durumuna bakarak bir eylem seçer.
        """
        # 1) Yüksek tehlike: kaç
        if wm.danger_level >= 0.7:
            action = ActionCommand(
                name="ESCAPE",
                params={
                    "reason": "high_danger",
                    "danger_level": wm.danger_level,
                },
            )
            self.logger.debug("[Planning][ActionSelector] ESCAPE selected (danger=%.2f)", wm.danger_level)
            return action

        # 2) Hedef görünüyorsa: hedefe yaklaş
        if wm.nearest_target is not None:
            action = ActionCommand(
                name="APPROACH_TARGET",
                params={
                    "target_id": wm.nearest_target.id,
                    "distance": wm.nearest_target.distance,
                    "obj_type": wm.nearest_target.obj_type,
                },
            )
            self.logger.debug(
                "[Planning][ActionSelector] APPROACH_TARGET selected (id=%s, dist=%.2f)",
                wm.nearest_target.id,
                wm.nearest_target.distance,
            )
            return action

        # 3) Görüş alanında ajan varsa: selam ver
        if "AGENT_IN_SIGHT" in wm.symbols:
            action = ActionCommand(
                name="GREET_AGENT",
                params={
                    "note": "agent_in_sight",
                },
            )
            self.logger.debug("[Planning][ActionSelector] GREET_AGENT selected.")
            return action

        # 4) Sahne boş veya özel durum yoksa: keşfet
        action = ActionCommand(
            name="EXPLORE",
            params={
                "reason": "default",
                "symbols": list(wm.symbols),
            },
        )
        self.logger.debug("[Planning][ActionSelector] EXPLORE selected (fallback).")
        return action

from __future__ import annotations

import time
import random
from typing import Dict, Any


class TestDummyWorld:
    """
    UEM'in algı-test döngüsü için minimal world simülatörü.
    Her çağrıda basit bir snapshot üretir.
    """

    def __init__(self) -> None:
        self.tick = 0

    def get_snapshot(self) -> Dict[str, Any]:
        self.tick += 1

        # Rastgele bir hedef nesne
        obj = {
            "id": f"obj_{self.tick}",
            "type": "box",
            "position": [
                random.uniform(1, 10),
                0.0,
                random.uniform(1, 10),
            ],
            "tags": ["interactable"],
        }

        # Bazen tehlikeli nesne üretelim
        if random.random() < 0.3:
            obj["tags"].append("danger")

        snapshot = {
            "tick": self.tick,
            "timestamp": time.time(),
            "agent_position": (0.0, 0.0, 0.0),
            "objects": [obj],
            "agents": [],
            "environment": {},
        }

        return snapshot

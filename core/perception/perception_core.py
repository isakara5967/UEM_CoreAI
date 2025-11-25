from __future__ import annotations

import logging
from typing import Any, Optional

from core.perception.types import (
    EnvironmentState,
    PerceptionResult,
    WorldSnapshot,
)
from core.perception.noise_filter.noise_filter import NoiseFilter
from core.perception.feature_extraction.feature_extractor import FeatureExtractor
from core.perception.state.state_perception import StatePerception
from core.perception.symbolic.symbolic_perception import SymbolicPerception


class PerceptionCore:
    """
    UEM'in algı pipeline'ını yöneten çekirdek modül.

    Akış:
        world_interface.get_snapshot()
            -> NoiseFilter
            -> FeatureExtractor
            -> StatePerception
            -> SymbolicPerception
            -> PerceptionResult

    NOT:
        - Memory tarafı henüz tam implemente edilmediği için opsiyoneldir.
        - update() şu an PerceptionResult üretir ve self.last_result'a yazar.
    """

    def __init__(
        self,
        config: dict[str, Any] | None,
        world_interface: Any,
        memory_core: Any | None = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config = config or {}
        self.world = world_interface
        self.memory = memory_core

        base_logger = logger or logging.getLogger("core.perception")
        self.logger = base_logger

        self.noise_filter: Optional[NoiseFilter] = None
        self.feature_extractor: Optional[FeatureExtractor] = None
        self.state_perception: Optional[StatePerception] = None
        self.symbolic_perception: Optional[SymbolicPerception] = None

        self.last_result: Optional[PerceptionResult] = None

    # --------------------------------------------------------------------- #
    # Lifecycle
    # --------------------------------------------------------------------- #

    def start(self) -> None:
        """
        Alt modülleri oluşturur ve perception sistemini başlatır.
        UEMCore.start() içinde çağrılması beklenir.
        """
        max_distance = float(self.config.get("max_distance", 100.0))

        self.noise_filter = NoiseFilter(
            max_distance=max_distance,
            logger=self.logger.getChild("NoiseFilter"),
        )
        self.feature_extractor = FeatureExtractor(
            logger=self.logger.getChild("FeatureExtractor")
        )
        self.state_perception = StatePerception(
            logger=self.logger.getChild("StatePerception")
        )
        self.symbolic_perception = SymbolicPerception(
            logger=self.logger.getChild("SymbolicPerception")
        )

        self.logger.info(
            "[Perception] PerceptionCore initialized "
            "(max_distance=%.1f).",
            max_distance,
        )

    # --------------------------------------------------------------------- #
    # Main update loop
    # --------------------------------------------------------------------- #

    def update(self, dt: float) -> None:
        """
        Tek bir algı tick'ini çalıştırır.

        Şu anki davranış:
            - world_interface'den snapshot almaya çalışır
            - perception pipeline'ından geçirir
            - PerceptionResult oluşturur
            - self.last_result içine yazar
            - Eğer memory_core.store_perception varsa, onu çağırır (opsiyonel)
        """
        if self.world is None:
            self.logger.warning("[Perception] World interface is None; skipping update.")
            return

        if self.noise_filter is None:
            self.logger.error("[Perception] start() not called; noise_filter is None.")
            return

        if (
            self.feature_extractor is None
            or self.state_perception is None
            or self.symbolic_perception is None
        ):
            self.logger.error("[Perception] start() not fully initialized.")
            return

        # 1) Dünyadan snapshot çek
        raw_snapshot = self._get_world_snapshot()
        if raw_snapshot is None:
            # Dünya henüz veri vermiyorsa sessizce çıkıyoruz.
            return

        # 2) Gürültü filtresi
        filtered_snapshot = self.noise_filter.process(raw_snapshot)

        # 3) Özellik çıkarımı
        objects, agents = self.feature_extractor.process(filtered_snapshot)

        # 4) Durum algısı
        env_state = self.state_perception.infer_state(
            filtered_snapshot, objects, agents
        )

        # 5) Sembolik etiketler
        symbols = self.symbolic_perception.infer_symbols(
            env_state, objects, agents
        )

        # 6) Nihai PerceptionResult
        result = PerceptionResult(
            snapshot=filtered_snapshot,
            objects=objects,
            agents=agents,
            environment_state=env_state,
            symbols=symbols,
        )

        self.last_result = result

        # 7) Memory entegrasyonu (şimdilik opsiyonel, kırmaması için korumalı)
        if self.memory is not None and hasattr(self.memory, "store_perception"):
            try:
                self.memory.store_perception(result)
            except Exception as exc:  # noqa: BLE001
                self.logger.debug(
                    "[Perception] memory.store_perception failed: %s", exc
                )

        self.logger.debug(
            "[Perception] tick processed: objects=%d, agents=%d, symbols=%s",
            len(result.objects),
            len(result.agents),
            result.symbols,
        )

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _get_world_snapshot(self) -> Optional[WorldSnapshot]:
        """
        World interface'den WorldSnapshot alır.

        Varsayılan beklenti:
            world_interface.get_snapshot() -> WorldSnapshot veya dict

        Eğer dict dönerse, WorldSnapshot'a kabaca adapt etmeye çalışır.
        Bu, henüz dünya tam implemente edilmemişken test için esneklik sağlar.
        """
        if not hasattr(self.world, "get_snapshot"):
            self.logger.warning(
                "[Perception] World interface has no get_snapshot(); skipping."
            )
            return None

        raw = self.world.get_snapshot()
        if raw is None:
            return None

        if isinstance(raw, WorldSnapshot):
            return raw

        # Dict veya benzeri bir yapı ise, kaba adaptasyon:
        if isinstance(raw, dict):
            try:
                tick = int(raw.get("tick", 0))
                timestamp = float(raw.get("timestamp", 0.0))
                agent_position = tuple(raw.get("agent_position", (0.0, 0.0, 0.0)))  # type: ignore[assignment]
                objects = list(raw.get("objects", []))
                agents = list(raw.get("agents", []))
                environment = dict(raw.get("environment", {}))

                snapshot = WorldSnapshot(
                    tick=tick,
                    timestamp=timestamp,
                    agent_position=agent_position,  # type: ignore[arg-type]
                    objects=objects,
                    agents=agents,
                    environment=environment,
                )
                return snapshot
            except Exception as exc:  # noqa: BLE001
                self.logger.error(
                    "[Perception] Failed to adapt raw snapshot dict -> WorldSnapshot: %s",
                    exc,
                )
                return None

        self.logger.warning(
            "[Perception] Unsupported snapshot type from world: %r", type(raw)
        )
        return None

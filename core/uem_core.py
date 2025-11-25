import logging
from typing import Any, Dict, Optional

from .memory import MemoryCore
from .cognition import CognitionCore
from .perception import PerceptionCore
from .emotion import EmotionCore
from .planning import PlanningCore
from .self import SelfCore
from .metamind import MetaMindCore
from .ethmor.ethmor_system import EthmorSynthSystem


class UEMCore:
    """
    UEM ana orkestratörü.

    - Alt sistemleri (perception, memory, cognition, planning, emotion,
      ethmor, self, metamind) başlatır.
    - Tek bir zaman adımı (tick) için update/step çalıştırır.
    - Önemli olayları (event) ilgili sistemlere dağıtır.

    Not:
        Var olan start/update/notify_event imzalarını koruyoruz.
        Ek olarak initialize() ve step() alias'ları eklenmiştir.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
        world_interface: Any | None = None,
    ) -> None:
        # Genel ayarlar
        self.config: Dict[str, Any] = config or {}
        self.logger: logging.Logger = logger or logging.getLogger("uem_core")
        self.world_interface: Any | None = world_interface

        self.started: bool = False

        # Alt sistemler
        self.memory = MemoryCore()
        self.cognition = CognitionCore()

        # PerceptionCore: world + memory + logger ile başlatılacak
        self.perception = PerceptionCore(
            config=self.config.get("perception", {}),
            world_interface=self.world_interface,
            memory_core=self.memory,
            logger=self.logger.getChild("perception"),
        )

        self.emotion = EmotionCore()
        self.planning = PlanningCore(
        config=self.config.get("planning", {}),
        memory_core=self.memory,
        world_interface=self.world_interface,
        logger=self.logger.getChild("planning"),
)

        self.metamind = MetaMindCore()
        self.ethmor_system = EthmorSynthSystem()

        # SELF sistemini diğer sistemlerle birlikte başlat
        self.self_system = SelfCore(
            memory_system=self.memory,
            emotion_system=self.emotion,
            cognition_system=self.cognition,
            planning_system=self.planning,
            metamind_system=self.metamind,
            ethmor_system=self.ethmor_system,
            logger=self.logger,
            config=self.config.get("self", None),
        )

    # ---- Yaşam döngüsü alias'ları ----

    def initialize(self) -> None:
        """
        Core loop için standart isim.
        Mevcut start() fonksiyonuna alias olarak davranır.
        """
        self.start()

    def step(
        self,
        world_state: Optional[Dict[str, Any]] = None,
        dt: Optional[float] = None,
    ) -> None:
        """
        Core loop için standart tek-adım fonksiyonu.

        Varsayılan olarak config.loop.tick_seconds kullanır.
        Yoksa 0.1 saniye kullanılır.

        world_state parametresi imza uyumluluğu için tutuluyor,
        şu an için kullanılmıyor.
        """
        if dt is None:
            dt = (
                self.config.get("loop", {}).get("tick_seconds", 0.1)
                if self.config is not None
                else 0.1
            )
        self.update(dt=dt, world_snapshot=world_state)

    # ---- Orijinal yaşam döngüsü API'si ----

    def start(self) -> None:
        """
        Alt sistemleri başlatır.
        Eski API ile uyumludur, ancak artık print yerine logger kullanır.
        """
        if self.started:
            self.logger.warning("UEMCore.start() called but core is already started.")
            return

        self.started = True
        self.logger.info("[UEM] Core initialized.")

        self.logger.info("[UEM] Memory system loading...")
        if hasattr(self.memory, "start"):
            self.memory.start()

        self.logger.info("[UEM] Cognition system loading...")
        if hasattr(self.cognition, "start"):
            self.cognition.start()

        self.logger.info("[UEM] Perception system loading...")
        if hasattr(self.perception, "start"):
            self.perception.start()

        self.logger.info("[UEM] Emotion system loading...")
        if hasattr(self.emotion, "start"):
            self.emotion.start()

        self.logger.info("[UEM] Planning system loading...")
        if hasattr(self.planning, "start"):
            self.planning.start()

        self.logger.info("[UEM] EthmorSynth system loading...")
        if hasattr(self.ethmor_system, "start"):
            self.ethmor_system.start()

        self.logger.info("[UEM] Self system loading...")
        if hasattr(self.self_system, "start"):
            self.self_system.start()

        self.logger.info("[UEM] MetaMind system loading...")
        if hasattr(self.metamind, "start"):
            self.metamind.start()

        self.logger.info("[UEM] All subsystems started.")

    def update(
        self,
        dt: float = 0.1,
        world_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        UEM çekirdeğinin bir zaman adımını simüle eder.

        Args:
            dt: zaman adımı (saniye vb.)
            world_snapshot: API imzası uyumluluğu için tutuluyor, şu an kullanılmıyor.
        """
        if not self.started:
            # henüz başlatılmamışsa sessizce çık
            return

        self.logger.debug(
            "UEMCore.update() tick started (dt=%s)", dt
        )

        # 1) Algı → 2) Hafıza → 3) Biliş → 4) Duygu → 5) Planlama → 6) Ethmor → 7) SELF → 8) MetaMind

        # Perception
        if hasattr(self.perception, "update"):
            self.perception.update(dt)

        # Memory
        if hasattr(self.memory, "update"):
            self.memory.update(dt)

        # Cognition
        if hasattr(self.cognition, "update"):
            self.cognition.update(dt)

        # Emotion
        if hasattr(self.emotion, "update"):
            self.emotion.update(dt)

        # Planning
        if hasattr(self.planning, "update"):
            self.planning.update(dt)

        # EthmorSynth
        if hasattr(self.ethmor_system, "update"):
            self.ethmor_system.update(dt)

        # SELF (benlik durumu, bütünlük vs.)
        if hasattr(self.self_system, "update"):
            self.self_system.update(dt)

        # MetaMind
        if hasattr(self.metamind, "update"):
            self.metamind.update(dt)

        self.logger.debug("UEMCore.update() tick finished.")

    def notify_event(self, event: Dict[str, Any]) -> None:
        """
        Dış dünyadan veya iç sistemlerden gelen anlamlı bir olayı
        çekirdeğe bildirir ve ilgili alt sistemlere dağıtır.

        Örnek event:
            {
                "type": "user_message",
                "content": "...",
                "emotional_tone": "negative",
                "timestamp": 123.456
            }
        """
        if not isinstance(event, dict):
            self.logger.warning("notify_event called with non-dict event: %r", event)
            return

        self.logger.debug("UEMCore.notify_event() event=%r", event)

        # 1) Emotion: duygusal tonu etkileyebilir
        if hasattr(self.emotion, "notify_event"):
            self.emotion.notify_event(event)

        # 2) Memory: önemli olaylar episodik hafızaya kaydedilebilir
        if hasattr(self.memory, "notify_event"):
            self.memory.notify_event(event)

        # SELF: benlik şeması ve bütünlük açısından anlamlı olabilir
        if hasattr(self.self_system, "notify_event"):
            self.self_system.notify_event(event)

        # Ethmor: etik/ahlaki açıdan anlamlı olabilir
        if hasattr(self.ethmor_system, "notify_event"):
            self.ethmor_system.notify_event(event)

        # MetaMind: sosyal/empatik değerlendirme yapabilir
        if hasattr(self.metamind, "notify_event"):
            self.metamind.notify_event(event)

    def shutdown(self) -> None:
        """Gracefully stop UEM Core."""
        self.logger.info("[UEM] Shutting down...")

        # İleride alt sistemlere özel shutdown ekleyeceğiz.
        # Şimdilik sadece log atıyoruz ki KeyboardInterrupt sonrası hata vermesin.

        if getattr(self, "memory", None) is not None:
            self.logger.info(" - Memory system shutdown")
        if getattr(self, "cognition", None) is not None:
            self.logger.info(" - Cognition system shutdown")
        if getattr(self, "perception", None) is not None:
            self.logger.info(" - Perception system shutdown")
        if getattr(self, "emotion", None) is not None:
            self.logger.info(" - Emotion system shutdown")
        if getattr(self, "planning", None) is not None:
            self.logger.info(" - Planning system shutdown")
        if getattr(self, "ethmor_system", None) is not None:
            self.logger.info(" - EthmorSynth system shutdown")
        if getattr(self, "self_system", None) is not None:
            self.logger.info(" - Self system shutdown")
        if getattr(self, "metamind", None) is not None:
            self.logger.info(" - MetaMind system shutdown")

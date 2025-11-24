from .short_term import ShortTermMemory
from .working import WorkingMemory
from .long_term import LongTermMemory
from .episodic import EpisodicMemory
from .semantic import SemanticMemory
from .emotional import EmotionalMemory


class MemoryCore:
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.working = WorkingMemory()
        self.long_term = LongTermMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.emotional = EmotionalMemory()

        self.initialized = True

    def start(self):
        self.short_term.start()
        self.working.start()
        self.long_term.start()
        self.episodic.start()
        self.semantic.start()
        self.emotional.start()

    # --- SELF Integration API ---

    def get_self_view(self) -> dict:
        """SELF sistemi için episodik + duygusal hafıza özetini döndürür."""
        episodes = []
        emotional_profile = {}

        if hasattr(self.episodic, "get_self_relevant_episodes"):
            episodes = self.episodic.get_self_relevant_episodes()

        if hasattr(self.emotional, "get_recent_emotional_profile_for_self"):
            emotional_profile = self.emotional.get_recent_emotional_profile_for_self()

        return {
            "episodes": episodes,
            "emotional_profile": emotional_profile,
        }

    # --- Event pipeline integration ---

    def notify_event(self, event: dict) -> None:
        """
        UEMCore'dan gelen olayı hafızaya iletir.
        Şimdilik tüm olayları SELF-relevant sayıp episodik hafızaya yazıyoruz.
        """
        if not isinstance(event, dict):
            return

        if hasattr(self.episodic, "tag_self_relevant_event"):
            self.episodic.tag_self_relevant_event(event)

        # İleride burada duygusal / semantik hafıza güncellemeleri de yapılabilir.

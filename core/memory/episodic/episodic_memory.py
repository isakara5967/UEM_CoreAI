# core/memory/episodic/episodic_memory.py

class EpisodicMemory:
    """
    UEM episodik (olay) hafıza sistemi.
    Zaman, yer, durum ve duygusal bağlam içeren olay kayıtları burada tutulacak.
    Şimdilik sadece iskelet.
    """

    def __init__(self):
        self.events = []  # ileride: timestamp, context, emotional tags
        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - EpisodicMemory subsystem loaded.")
        else:
            print("     - EpisodicMemory subsystem FAILED to load.")

    # --- SELF Integration API ---

    def tag_self_relevant_event(self, event: dict) -> None:
        """Episodik olayı SELF açısından önemli olarak işaretle."""
        if not isinstance(event, dict):
            return

        ev = dict(event)
        ev["self_relevant"] = True
        self.events.append(ev)

    def get_self_relevant_episodes(self, limit: int = 20) -> list[dict]:
        """SELF için son self-relevant episodları döndür."""
        filtered = [e for e in self.events if e.get("self_relevant")]
        return filtered[-limit:]

# core/emotion/primitive/novelty_system.py

class NoveltySystem:
    """
    Yenilik / alışkanlık algısı.
    Merak ve stres modellerine temel sinyal sağlar.
    """

    def __init__(self):
        # 0.0 .. 1.0 arası
        self.novelty = 0.0       # ne kadar yeni
        self.familiarity = 1.0   # ne kadar tanıdık

        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - NoveltySystem subsystem loaded.")
        else:
            print("     - NoveltySystem subsystem FAILED to load.")

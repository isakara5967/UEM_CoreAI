# core/emotion/primitive/core_affect_system.py

class CoreAffectSystem:
    """
    Valence / arousal / control (dominance) gibi temel duygusal eksenleri tutar.
    Şimdilik sadece iskelet ve dummy değerler.
    """

    def __init__(self):
        # -1.0 .. +1.0 arası kullanılacak (ileride)
        self.valence = 0.0    # hoş / nahoş
        self.arousal = 0.0    # sakin / yoğun
        self.control = 0.0    # kontrol bende / değil

        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - CoreAffectSystem subsystem loaded.")
        else:
            print("     - CoreAffectSystem subsystem FAILED to load.")

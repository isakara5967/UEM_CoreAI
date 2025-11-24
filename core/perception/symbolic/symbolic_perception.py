# core/perception/symbolic/symbolic_perception.py

class SymbolicPerception:
    """
    UEM sembolik algı birimi.
    İleride: metin, komut, kelime, etiket gibi sembolik girdileri işleyecek.
    Şimdilik iskelet.
    """

    def __init__(self):
        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - SymbolicPerception subsystem loaded.")
        else:
            print("     - SymbolicPerception subsystem FAILED to load.")

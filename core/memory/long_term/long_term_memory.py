# core/memory/long_term/long_term_memory.py

class LongTermMemory:
    """
    UEM uzun süreli hafıza sistemi.
    Zaman içinde kalıcı olacak bilgilerin tutulacağı yer.
    Şimdilik iskelet + basit durum bayrağı.
    """

    def __init__(self):
        self.storage = {}
        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - LongTermMemory subsystem loaded.")
        else:
            print("     - LongTermMemory subsystem FAILED to load.")

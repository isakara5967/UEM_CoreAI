# core/perception/state/state_perception.py

class StatePerception:
    """
    UEM durum algı birimi.
    Oyun motoru/sanal dünya durumlarını (health, position, env state vb.) algılayacak.
    Şimdilik iskelet.
    """

    def __init__(self):
        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - StatePerception subsystem loaded.")
        else:
            print("     - StatePerception subsystem FAILED to load.")

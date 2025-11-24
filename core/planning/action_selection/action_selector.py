# core/planning/action_selection/action_selector.py

class ActionSelector:
    """
    UEM planlama sisteminde eylem seçici birim.
    O an hangi aksiyonun yapılacağına karar verme katmanı.
    Şimdilik iskelet.
    """

    def __init__(self):
        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - ActionSelector subsystem loaded.")
        else:
            print("     - ActionSelector subsystem FAILED to load.")

# core/emotion/primitive/pain_comfort_system.py

class PainComfortSystem:
    """
    Fiziksel ve duygusal acı / rahatlık durumunu temsil eder.
    Travma, kaçınma, rahatlama gibi durumlar için temel sinyal kaynağı.
    """

    def __init__(self):
        # 0.0 .. 1.0 arası skorlar
        self.physical_pain = 0.0
        self.emotional_pain = 0.0
        self.relief = 0.0

        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - PainComfortSystem subsystem loaded.")
        else:
            print("     - PainComfortSystem subsystem FAILED to load.")

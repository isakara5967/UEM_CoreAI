# core/perception/visual/visual_perception.py

class VisualPerception:
    """
    UEM görsel algı birimi.
    İleride: sahne, obje, renk, şekil gibi görsel bilgileri işleyecek.
    Şimdilik sadece iskelet.
    """

    def __init__(self):
        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - VisualPerception subsystem loaded.")
        else:
            print("     - VisualPerception subsystem FAILED to load.")

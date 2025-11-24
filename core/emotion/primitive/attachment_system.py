# core/emotion/primitive/attachment_system.py

class AttachmentSystem:
    """
    Varlıklara / kişilere / kavramlara bağlılık ve önem derecesi.
    Aşk, özlem, kayıp gibi karmaşık duygular için temel sinyal kaynağı olacak.
    """

    def __init__(self):
        # 0.0 .. 1.0 arası global bir bağlılık yoğunluğu (ileride entity-bazlı yapılabilir)
        self.attachment_strength = 0.0
        self.separation_distress_potential = 0.0

        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - AttachmentSystem subsystem loaded.")
        else:
            print("     - AttachmentSystem subsystem FAILED to load.")

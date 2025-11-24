# core/cognition/cognition_core.py

from .evaluation import EvaluationUnit
from .inference import InferenceUnit
from .intuition import IntuitionUnit
from .conflict_resolution import ConflictResolutionUnit
from .internal_simulation import InternalSimulationUnit
from .meta_cognition import MetaCognitionUnit


class CognitionCore:
    """
    UEM bilişsel çekirdeği.
    Değerlendirme, çıkarım, sezgi, çatışma çözümü, simülasyon ve metabilişsel birimler.
    Şimdilik her alt birim iskelet formunda yükleniyor.
    """

    def __init__(self):
        self.evaluation = EvaluationUnit()
        self.inference = InferenceUnit()
        self.intuition = IntuitionUnit()
        self.conflict_resolution = ConflictResolutionUnit()
        self.internal_simulation = InternalSimulationUnit()
        self.meta_cognition = MetaCognitionUnit()

        self.initialized = True

    def start(self):
        self.evaluation.start()
        self.inference.start()
        self.intuition.start()
        self.conflict_resolution.start()
        self.internal_simulation.start()
        self.meta_cognition.start()

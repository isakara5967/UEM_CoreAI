# core/perception/perception_core.py

from .visual import VisualPerception
from .symbolic import SymbolicPerception
from .state import StatePerception
from .feature_extraction import FeatureExtractor
from .noise_filter import NoiseFilter


class PerceptionCore:
    """
    UEM algı çekirdeği.
    Görsel, sembolik, durum temelli algı + özellik çıkarım ve gürültü filtreleme birimlerini yönetir.
    Şimdilik tüm alt birimler iskelet formunda yükleniyor.
    """

    def __init__(self):
        self.visual = VisualPerception()
        self.symbolic = SymbolicPerception()
        self.state = StatePerception()
        self.feature_extractor = FeatureExtractor()
        self.noise_filter = NoiseFilter()

        self.initialized = True

    def start(self):
        self.visual.start()
        self.symbolic.start()
        self.state.start()
        self.feature_extractor.start()
        self.noise_filter.start()

# core/perception/feature_extraction/feature_extractor.py

class FeatureExtractor:
    """
    UEM özellik çıkarım birimi.
    Ham girdilerden embedding/tensör/özellik vektörü çıkaracak.
    Şimdilik iskelet.
    """

    def __init__(self):
        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - FeatureExtractor subsystem loaded.")
        else:
            print("     - FeatureExtractor subsystem FAILED to load.")

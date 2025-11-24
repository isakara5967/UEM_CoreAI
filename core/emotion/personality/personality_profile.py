# core/emotion/personality/personality_profile.py

class PersonalityProfile:
    """
    UEM'in duygusal kişilik profilini temsil eder.
    Risk alma, empati, güven eğilimi, saldırganlık eşiği gibi parametreler içerir.
    Şimdilik sadece iskelet ve dummy değerler.
    """

    def __init__(self):
        # 0.0 .. 1.0 arası normalleştirilmiş parametreler
        self.risk_taking = 0.5       # risk alma eğilimi
        self.empathy = 0.5           # empati düzeyi
        self.trust_tendency = 0.5    # kolay güvenme / şüphecilik
        self.aggression_threshold = 0.5  # agresyon eşiği

        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - PersonalityProfile subsystem loaded.")
        else:
            print("     - PersonalityProfile subsystem FAILED to load.")

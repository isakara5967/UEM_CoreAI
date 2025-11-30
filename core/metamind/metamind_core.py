from .social.emotional_empathy import EmotionalEmpathyUnit
from .social.cognitive_empathy import CognitiveEmpathyUnit
from .social.social_context import SocialContextUnit
from .social.relational_mapping import RelationalMappingUnit
from .social.ethical_filter import EthicalSocialFilterUnit
from .social.state_prediction import HumanStatePredictorUnit
from .social.social_simulation import SocialSimulationEngine


class MetaMindCore:
    """
    UEM'in Meta zihin çekirdeği.
    Şimdilik sadece alt sistemlerin iskeletini ve loglarını yönetiyor.
    Karar vermez, sadece "üst seviye sosyal/empatik zihin" modüllerini başlatır.
    """

    def __init__(self):
        self.emotional_empathy = EmotionalEmpathyUnit()
        self.cognitive_empathy = CognitiveEmpathyUnit()
        self.social_context = SocialContextUnit()
        self.relational_mapping = RelationalMappingUnit()
        self.ethical_filter = EthicalSocialFilterUnit()
        self.state_predictor = HumanStatePredictorUnit()
        self.social_simulation = SocialSimulationEngine()

        self.initialized = True

        # SELF entegrasyonu: son alınan SELF raporu
        self.last_self_report: dict | None = None

    def start(self):
        print("[UEM] MetaMind system loaded.")
        self.emotional_empathy.start()
        self.cognitive_empathy.start()
        self.social_context.start()
        self.relational_mapping.start()
        self.ethical_filter.start()
        self.state_predictor.start()
        self.social_simulation.start()

    # --- SELF Integration API ---

    def receive_self_report(self, report: dict) -> None:
        """SELF tarafından gönderilen durum raporunu alır."""
        if not isinstance(report, dict):
            return
        self.last_self_report = report
        # İleride: rapor alt ünitelerle paylaşılabilir.

from .primitive import (
    CoreAffectSystem,
    ThreatSafetySystem,
    AttachmentSystem,
    NoveltySystem,
    PainComfortSystem,
)

from .personality import (
    PersonalityProfile,
    ChronicStressModel,
    ResilienceModel,
)

from .integration import (
    AffectiveStateIntegrator,
    ValenceArousalModel,
    EmotionPatternClassifier,
    EmotionRegulationController,
    EthmorEmotionBridge,
)


class EmotionCore:
    """
    UEM duygusal çekirdeği.
    - Primitive Affect Systems
    - Personality & Long-Term Affective Structure
    - Affect Integration & Regulation System
    """

    def __init__(self):
        # Primitive katman
        self.core_affect = CoreAffectSystem()
        self.threat_safety = ThreatSafetySystem()
        self.attachment = AttachmentSystem()
        self.novelty = NoveltySystem()
        self.pain_comfort = PainComfortSystem()

        # Personality & long-term katman
        self.personality_profile = PersonalityProfile()
        self.chronic_stress = ChronicStressModel()
        self.resilience = ResilienceModel()

        # Affect Integration & Regulation katmanı
        self.affective_state_integrator = AffectiveStateIntegrator()
        self.valence_arousal_model = ValenceArousalModel()
        self.emotion_pattern_classifier = EmotionPatternClassifier()
        self.emotion_regulation_controller = EmotionRegulationController()
        self.ethmor_emotion_bridge = EthmorEmotionBridge()

        self.initialized = True

    def start(self):
        # Primitive katman başlığı
        print("   + Primitive Affect Systems")
        self.core_affect.start()
        self.threat_safety.start()
        self.attachment.start()
        self.novelty.start()
        self.pain_comfort.start()

        # Personality & long-term katman başlığı
        print("   + Personality & Long-Term Affective Structure")
        self.personality_profile.start()
        self.chronic_stress.start()
        self.resilience.start()

        # Affect Integration & Regulation katmanı başlığı
        print("   + Affect Integration & Regulation System")
        self.affective_state_integrator.start()
        self.valence_arousal_model.start()
        self.emotion_pattern_classifier.start()
        self.emotion_regulation_controller.start()
        self.ethmor_emotion_bridge.start()

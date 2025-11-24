from .affective_state_integrator import AffectiveStateIntegrator
from .valence_arousal_model import ValenceArousalModel
from .emotion_pattern_classifier import EmotionPatternClassifier
from .emotion_regulation_controller import EmotionRegulationController
from .ethmor_emotion_bridge import EthmorEmotionBridge


class EmotionIntegrationSystem:
    """
    Affect Integration & Regulation System:
    - AffectiveStateIntegrator
    - ValenceArousalModel
    - EmotionPatternClassifier
    - EmotionRegulationController
    - EthmorEmotionBridge
    """

    def __init__(self):
        print("   + Affect Integration & Regulation System")
        self.state_integrator = AffectiveStateIntegrator()
        self.valence_arousal = ValenceArousalModel()
        self.pattern_classifier = EmotionPatternClassifier()
        self.regulation_controller = EmotionRegulationController()
        self.ethmor_bridge = EthmorEmotionBridge()

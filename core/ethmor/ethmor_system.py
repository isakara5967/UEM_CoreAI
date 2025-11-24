from core.ethmor.ethical_base.ethical_base import EthicalBase
from core.ethmor.moral_base.moral_base import MoralBase
from core.ethmor.self_model.self_model_extension import SelfModelExtension
from core.ethmor.context_engine.context_engine import ContextEngine
from core.ethmor.synthesis_engine.synthesis_engine import SynthesisEngine
from core.ethmor.behavior_model.behavior_value_model import BehaviorValueModel

class EthmorSynthSystem:
    def __init__(self):
        self.ethical_base = EthicalBase()
        self.moral_base = MoralBase()
        self.self_model_extension = SelfModelExtension()
        self.context_engine = ContextEngine()
        self.synthesis_engine = SynthesisEngine()
        self.behavior_value_model = BehaviorValueModel()

    def start(self):
        print("[UEM] EthmorSynth system loading...")
        self.ethical_base.start()
        self.moral_base.start()
        self.self_model_extension.start()
        self.context_engine.start()
        self.synthesis_engine.start()
        self.behavior_value_model.start()
        pass

    # --- SELF Integration API ---
    def export_value_profile(self) -> dict:
        """Return stable ethical/moral value profile for SELF identity system."""
        return {
            "ethical_weights": self.ethical_base.export_weights()
            if hasattr(self.ethical_base, "export_weights")
            else {},
            "moral_rules": self.moral_base.export_rules()
            if hasattr(self.moral_base, "export_rules")
            else {},
        }

# core/planning/rl_interface/rl_policy_interface.py

class RLPolicyInterface:
    """
    UEM planlama sisteminde pekiştirmeli öğrenme politika arayüzü.
    RL ajanları ile planlama sistemi arasındaki köprü olacak.
    Şimdilik iskelet.
    """

    def __init__(self):
        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - RLPolicyInterface subsystem loaded.")
        else:
            print("     - RLPolicyInterface subsystem FAILED to load.")

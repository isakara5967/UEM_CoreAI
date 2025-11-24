class ShortTermMemory:
    def __init__(self):
        self.buffer = []
        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - ShortTermMemory subsystem loaded.")
        else:
            print("     - ShortTermMemory subsystem FAILED to load.")

class WorkingMemory:
    def __init__(self):
        self.state = {}
        self.initialized = True

    def start(self):
        if self.initialized:
            print("     - WorkingMemory subsystem loaded.")
        else:
            print("     - WorkingMemory subsystem FAILED to load.")

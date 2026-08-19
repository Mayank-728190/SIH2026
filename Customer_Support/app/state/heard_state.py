class HeardStateManager:
    """
    Distinguishes between LLM generated state, TTS generated audio, 
    and what was actually heard/confirmed by the user.
    """
    def __init__(self):
        self.proposed_state = None
        self.committed_state = None
        self.interrupted = False

    def propose_state(self, state_update: dict):
        self.proposed_state = state_update
        self.interrupted = False

    def mark_interrupted(self):
        self.interrupted = True
        self.proposed_state = None

    def commit_state(self):
        if not self.interrupted and self.proposed_state:
            if not self.committed_state:
                self.committed_state = {}
            self.committed_state.update(self.proposed_state)
            self.proposed_state = None
            return True
        return False
        
    def get_committed_state(self):
        return self.committed_state or {}

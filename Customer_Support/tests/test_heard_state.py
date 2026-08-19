from app.state.heard_state import HeardStateManager

def test_heard_state_commit():
    manager = HeardStateManager()
    manager.propose_state({"amount": 8500})
    manager.commit_state()
    assert manager.get_committed_state() == {"amount": 8500}

def test_heard_state_rollback_on_interruption():
    manager = HeardStateManager()
    manager.propose_state({"amount": 8500})
    manager.mark_interrupted()
    manager.commit_state()
    assert manager.get_committed_state() == {}

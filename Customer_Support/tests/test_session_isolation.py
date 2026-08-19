import pytest
from app.state.session_state import SessionManager
import uuid

@pytest.mark.asyncio
async def test_session_isolation():
    # Call A
    session_a = await SessionManager.create_session("call_a")
    session_a.customer_id = "CUSTOMER_1001"
    await SessionManager.update_session(session_a)
    
    # Call disconnects
    await SessionManager.invalidate_call_session("call_a", session_a.session_id)
    
    # Verify destroyed
    deleted = await SessionManager.get_session(session_a.session_id)
    assert deleted is None

    # Call B (new caller, even if same person)
    session_b = await SessionManager.create_session("call_b")
    # Must explicitly not have customer_id transferred
    assert session_b.customer_id is None

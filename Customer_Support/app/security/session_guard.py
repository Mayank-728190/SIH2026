from app.state.session_state import SessionManager
from app.models.session import VoiceSession
from fastapi import HTTPException

async def validate_session(session_id: str) -> VoiceSession:
    session = await SessionManager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session invalid or expired")
    return session

async def require_verified_customer(session_id: str) -> str:
    session = await validate_session(session_id)
    if not session.customer_id:
        raise HTTPException(status_code=403, detail="Customer not verified in current session")
    if session.verification_status != "SECURITY_PASSED":
        raise HTTPException(status_code=403, detail="Security check required. Please ask the user for their dog's name and verify it first using the verify_security_question tool.")
    return session.customer_id

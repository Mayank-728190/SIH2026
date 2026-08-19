import json
from datetime import datetime, timedelta
from app.models.session import VoiceSession
from typing import Optional
import uuid

SESSION_TTL_MINUTES = 30

_sessions = {}

class SessionManager:
    @staticmethod
    async def create_session(call_id: str, language: str = "english") -> VoiceSession:
        session_id = f"sess_{uuid.uuid4().hex}"
        
        expires_at = datetime.utcnow() + timedelta(minutes=SESSION_TTL_MINUTES)
        session = VoiceSession(
            session_id=session_id,
            call_id=call_id,
            language=language,
            expires_at=expires_at
        )
        
        _sessions[session_id] = session
        return session

    @staticmethod
    async def get_or_create_session(call_id: str, customer_id: str, language: str = "english") -> tuple[VoiceSession, bool]:
        """Returns (session, is_resumed)."""
        session_id = f"sess_{customer_id}"
        
        # Check if active session exists
        if session_id in _sessions:
            session = _sessions[session_id]
            if session.expires_at > datetime.utcnow():
                # Resume! Update call ID and extend expiration
                session.call_id = call_id
                session.expires_at = datetime.utcnow() + timedelta(minutes=SESSION_TTL_MINUTES)
                return session, True
        
        # Create new
        expires_at = datetime.utcnow() + timedelta(minutes=SESSION_TTL_MINUTES)
        session = VoiceSession(
            session_id=session_id,
            call_id=call_id,
            customer_id=customer_id,
            language=language,
            expires_at=expires_at
        )
        _sessions[session_id] = session
        return session, False

    @staticmethod
    async def get_session(session_id: str) -> Optional[VoiceSession]:
        session = _sessions.get(session_id)
        if session and session.expires_at > datetime.utcnow():
            return session
        if session:
            # Cleanup expired session
            del _sessions[session_id]
        return None

    @staticmethod
    async def update_session(session: VoiceSession) -> None:
        _sessions[session.session_id] = session

    @staticmethod
    async def delete_session(session_id: str) -> None:
        if session_id in _sessions:
            del _sessions[session_id]

    @staticmethod
    async def invalidate_call_session(call_id: str, session_id: str) -> None:
        """Called when a call disconnects. In session-resumption mode, we intentionally DO NOT delete the session here."""
        pass

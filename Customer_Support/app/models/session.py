from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class VoiceSession(BaseModel):
    session_id: str
    call_id: str
    customer_id: Optional[str] = None
    language: str = "english"
    verification_status: str = "NOT_VERIFIED" # NOT_VERIFIED, OTP_VERIFIED, PIN_VERIFIED, SECURITY_PASSED
    temporary_context: Dict[str, Any] = Field(default_factory=dict)
    chat_history_dict: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

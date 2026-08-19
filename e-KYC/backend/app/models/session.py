from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class KYCState(str, Enum):
    CREATED = "CREATED"
    CONSENT = "CONSENT"
    DOCUMENT_CHECK = "DOCUMENT_CHECK"
    FACE_CAPTURE = "FACE_CAPTURE"
    PAN_CAPTURE = "PAN_CAPTURE"
    AADHAAR_CAPTURE = "AADHAAR_CAPTURE"
    DOCUMENT_PROCESSING = "DOCUMENT_PROCESSING"
    FACE_VERIFICATION = "FACE_VERIFICATION"
    QUESTION_1 = "QUESTION_1"
    QUESTION_2 = "QUESTION_2"
    QUESTION_3 = "QUESTION_3"
    FINAL_VERIFICATION = "FINAL_VERIFICATION"
    APPROVED = "APPROVED"
    RETRY_REQUIRED = "RETRY_REQUIRED"
    MANUAL_REVIEW = "MANUAL_REVIEW"

class SessionStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    INTERRUPTED = "INTERRUPTED"

class DataStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"

class KYCSession(BaseModel):
    session_id: str
    state: KYCState = KYCState.CREATED
    status: SessionStatus = SessionStatus.IN_PROGRESS
    completed_steps: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_heartbeat: Optional[datetime] = None
    version: int = 1
    
    # Internal routing logic
    document_mode: Optional[str] = None # UPLOAD_MODE or CAMERA_MODE
    
    # Agent-controlled capture tracking
    capture_requested: Optional[str] = None
    processing_status: Optional[str] = None
    capture_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    idempotency_keys: List[str] = Field(default_factory=list)

class VerificationRecord(BaseModel):
    session_id: str
    # Scores
    pan_name_score: Optional[float] = None
    aadhaar_name_score: Optional[float] = None
    pan_father_name_score: Optional[float] = None
    aadhaar_father_name_score: Optional[float] = None
    face_match_score: Optional[float] = None
    
    # Booleans / Statuses
    name_match: Optional[bool] = None
    father_name_match: Optional[bool] = None
    face_match: Optional[bool] = None
    liveness: Optional[bool] = None
    
    question_status: str = "PENDING"
    decision: Optional[str] = None

class QuestionRecord(BaseModel):
    question_id: str
    question_type: str
    status: str = "PENDING" # PENDING, IN_PROGRESS, COMPLETED
    answer_status: Optional[str] = None # VALID, INVALID

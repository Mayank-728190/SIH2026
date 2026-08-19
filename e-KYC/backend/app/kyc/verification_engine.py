import logging
from typing import Tuple
from app.config import config
from app.models.session import VerificationRecord, KYCState

logger = logging.getLogger(__name__)

class VerificationEngine:
    """
    Deterministic verification engine. The LLM NEVER evaluates this logic.
    """
    
    @classmethod
    def evaluate(cls, record: VerificationRecord) -> Tuple[bool, KYCState]:
        """
        Evaluates the verification record against configured thresholds.
        Returns (is_complete, next_state)
        """
        if not record:
            return False, KYCState.MANUAL_REVIEW
            
        # Check if all required scores exist
        if any(v is None for v in [
            record.pan_name_score, 
            record.pan_father_name_score, 
            record.aadhaar_name_score, 
            record.aadhaar_father_name_score,
            record.face_match_score,
            record.liveness
        ]):
            # Missing data, can't make final decision yet
            return False, KYCState.MANUAL_REVIEW

        # Update boolean flags based on thresholds
        record.name_match = (
            record.pan_name_score >= config.NAME_THRESHOLD and 
            record.aadhaar_name_score >= config.NAME_THRESHOLD
        )
        
        record.father_name_match = (
            record.pan_father_name_score >= config.FATHER_NAME_THRESHOLD and 
            record.aadhaar_father_name_score >= config.FATHER_NAME_THRESHOLD
        )
        
        record.face_match = (
            record.face_match_score >= config.FACE_THRESHOLD
        )
        
        # Determine final decision
        details_pass = record.name_match and record.father_name_match
        face_pass = record.face_match and record.liveness
        
        # Question status must be completed
        questions_pass = record.question_status == "COMPLETED"
        
        if details_pass and face_pass and questions_pass:
            record.decision = "APPROVED"
            return True, KYCState.APPROVED
            
        # For this prototype, if it fails, go to manual review
        # We could implement granular retries here (e.g. if face fails but details pass)
        record.decision = "MANUAL_REVIEW"
        return True, KYCState.MANUAL_REVIEW

verification_engine = VerificationEngine()

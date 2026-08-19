import logging
from typing import Dict, List, Optional
from app.models.session import KYCState

logger = logging.getLogger(__name__)

class StateMachine:
    # Define valid transitions for each state
    # Format: { CURRENT_STATE: [ALLOWED_NEXT_STATES] }
    TRANSITIONS: Dict[KYCState, List[KYCState]] = {
        KYCState.CREATED: [KYCState.CONSENT, KYCState.DOCUMENT_CHECK, KYCState.FACE_CAPTURE],
        KYCState.CONSENT: [KYCState.DOCUMENT_CHECK, KYCState.FACE_CAPTURE],
        KYCState.DOCUMENT_CHECK: [
            KYCState.FACE_CAPTURE,
            KYCState.DOCUMENT_PROCESSING # If documents are already uploaded
        ],
        KYCState.FACE_CAPTURE: [KYCState.PAN_CAPTURE],
        KYCState.PAN_CAPTURE: [KYCState.AADHAAR_CAPTURE],
        KYCState.AADHAAR_CAPTURE: [KYCState.DOCUMENT_PROCESSING, KYCState.APPROVED],
        KYCState.DOCUMENT_PROCESSING: [KYCState.FACE_VERIFICATION],
        KYCState.FACE_VERIFICATION: [KYCState.QUESTION_1],
        KYCState.QUESTION_1: [KYCState.QUESTION_2],
        KYCState.QUESTION_2: [KYCState.QUESTION_3],
        KYCState.QUESTION_3: [KYCState.FINAL_VERIFICATION],
        KYCState.FINAL_VERIFICATION: [
            KYCState.APPROVED,
            KYCState.RETRY_REQUIRED,
            KYCState.MANUAL_REVIEW
        ],
        # Terminal states don't transition further
        KYCState.APPROVED: [],
        KYCState.RETRY_REQUIRED: [
            KYCState.FACE_CAPTURE,
            KYCState.PAN_CAPTURE,
            KYCState.AADHAAR_CAPTURE,
            KYCState.DOCUMENT_CHECK
        ],
        KYCState.MANUAL_REVIEW: []
    }

    @classmethod
    def can_transition(cls, current_state: KYCState, target_state: KYCState) -> bool:
        allowed = cls.TRANSITIONS.get(current_state, [])
        return target_state in allowed

    @classmethod
    def get_action_for_state(cls, state: KYCState) -> str:
        """
        Returns a safe workflow instruction for the LLM based on the state.
        This ensures the LLM never invents its own instructions.
        """
        actions = {
            KYCState.CREATED: "ASK_USER_FOR_CONSENT_TO_BEGIN",
            KYCState.CONSENT: "ASK_USER_IF_DOCUMENTS_ARE_AVAILABLE",
            KYCState.DOCUMENT_CHECK: "ASK_USER_IF_DOCUMENTS_ARE_AVAILABLE",
            KYCState.FACE_CAPTURE: "ASK_USER_TO_LOOK_AT_CAMERA",
            KYCState.PAN_CAPTURE: "ASK_USER_TO_SHOW_PAN",
            KYCState.AADHAAR_CAPTURE: "ASK_USER_TO_SHOW_AADHAAR",
            KYCState.DOCUMENT_PROCESSING: "INFORM_USER_PROCESSING_DOCUMENTS",
            KYCState.FACE_VERIFICATION: "INFORM_USER_VERIFYING_FACE",
            KYCState.QUESTION_1: "ASK_KYC_QUESTION_1",
            KYCState.QUESTION_2: "ASK_KYC_QUESTION_2",
            KYCState.QUESTION_3: "ASK_KYC_QUESTION_3",
            KYCState.FINAL_VERIFICATION: "INFORM_USER_FINAL_VERIFICATION",
            KYCState.APPROVED: "INFORM_USER_APPROVED",
            KYCState.RETRY_REQUIRED: "INFORM_USER_RETRY_REQUIRED",
            KYCState.MANUAL_REVIEW: "INFORM_USER_MANUAL_REVIEW"
        }
        return actions.get(state, "WAIT_FOR_BACKEND")

import logging
from typing import Optional
from app.db.mongodb import mongodb
from app.models.session import KYCState
from app.kyc.state_machine import StateMachine
from app.kyc.verification_engine import verification_engine

logger = logging.getLogger(__name__)

class KYCOrchestrator:
    @classmethod
    async def transition_state(cls, session_id: str, target_state: KYCState, completed_step: Optional[str] = None) -> bool:
        """
        Attempts to transition the session to the target_state.
        Returns True if successful, False if transition is invalid.
        """
        session = await mongodb.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found.")
            return False
            
        current_state = session.state
        if not StateMachine.can_transition(current_state, target_state):
            logger.warning(f"Invalid transition from {current_state} to {target_state} for session {session_id}")
            return False
            
        await mongodb.update_session_state(session_id, target_state, completed_step)
        logger.info(f"Session {session_id} transitioned to {target_state}")
        return True

    @classmethod
    async def run_final_verification(cls, session_id: str):
        """
        Runs the verification engine and updates the session state to the final decision.
        """
        record = await mongodb.get_verification_record(session_id)
        if not record:
            await cls.transition_state(session_id, KYCState.MANUAL_REVIEW)
            return
            
        is_complete, next_state = verification_engine.evaluate(record)
        
        # Save evaluated record
        await mongodb.save_verification_record(record)
        
        # Transition state
        if is_complete:
            await cls.transition_state(session_id, next_state)

orchestrator = KYCOrchestrator()

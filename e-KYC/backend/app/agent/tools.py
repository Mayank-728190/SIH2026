from typing import Annotated
from livekit.agents import llm
import logging
import asyncio

from app.db.mongodb import mongodb
from app.kyc.state_machine import StateMachine
from app.kyc.orchestrator import KYCOrchestrator
from app.models.session import KYCState
from app.agent.progress_manager import ProcessingConversationManager

logger = logging.getLogger(__name__)

class KYCTools(llm.Toolset):
    """
    Safe Tool Boundary for the LLM. 
    The LLM never receives PII, only state transition commands.
    """
    def __init__(self, session_id: str):
        super().__init__(id="kyc_tools")
        self.session_id = session_id
        self.agent_session = None
        self.conversation_manager = None
        self.agent = None
        
    def set_agent_session(self, agent_session):
        self.agent_session = agent_session
        self.conversation_manager = ProcessingConversationManager(agent_session)

    def set_agent(self, agent):
        self.agent = agent

    @llm.function_tool(description="Get the current KYC state and the required action.")
    async def get_kyc_state(self) -> str:
        session = await mongodb.get_session(self.session_id)
        if not session:
            return "ERROR: Session not found."
            
        action = StateMachine.get_action_for_state(session.state)
        return f"Current State: {session.state.value}. Required Action: {action}"

    @llm.function_tool(description="Mark the user consent as received.")
    async def confirm_consent(self) -> str:
        success = await KYCOrchestrator.transition_state(self.session_id, KYCState.FACE_CAPTURE)
        if success:
            return "Consent received. Please ask the user to look at the camera for Face Capture."
        return "Failed to transition state. Check current state."

    async def _request_capture(self, document_type: str, next_message: str) -> str:
        session = await mongodb.get_session(self.session_id)
        if not session:
            return "ERROR: Session not found."
            
        # Set the request in MongoDB so the frontend captures exactly ONE frame
        success = await mongodb.set_capture_request(self.session_id, document_type)
        if not success:
            return "Failed to request capture."
            
        # Start natural speech fillers
        if self.conversation_manager:
            await self.conversation_manager.start(document_type)
            
        # Block tool execution until processing completes, so the LLM automatically 
        # responds to the final state instead of needing a background injection.
        result_msg = await self._monitor_processing(document_type)
        return result_msg

    async def _monitor_processing(self, document_type: str) -> str:
        # Poll DB until processing is completed
        while True:
            session = await mongodb.get_session(self.session_id)
            if session and session.processing_status == "COMPLETED":
                break
            await asyncio.sleep(1)
            
        # Stop the filler speech instantly
        if self.conversation_manager:
            await self.conversation_manager.stop()
            
        # Return the silent signal to the LLM tool executor so it knows to proceed
        if document_type == "AADHAAR":
            return f"SYSTEM NOTIFICATION: {document_type}_PROCESSING_COMPLETED. You must now tell the user that we have successfully taken their picture and the KYC verification has been completed successfully, and thank them for their time. Do NOT ask any further questions."
        else:
            return f"SYSTEM NOTIFICATION: {document_type}_PROCESSING_COMPLETED. You must now tell the user that we have successfully taken their picture, and then move to the next state according to the rules."

    @llm.function_tool(description="Capture exactly one live face frame after explicit agent invocation.")
    async def capture_face(self) -> str:
        return await self._request_capture(
            "FACE", 
            "Great, I'm requesting the face capture now."
        )

    @llm.function_tool(description="Capture exactly one PAN frame after explicit agent invocation.")
    async def capture_pan(self) -> str:
        return await self._request_capture(
            "PAN", 
            "Great, I'm requesting the PAN capture now."
        )

    @llm.function_tool(description="Capture exactly one Aadhaar frame after explicit agent invocation.")
    async def capture_aadhaar(self) -> str:
        return await self._request_capture(
            "AADHAAR", 
            "Great, I'm requesting the Aadhaar capture now."
        )

    @llm.function_tool(description="Submit user's answer to a KYC question.")
    async def submit_question_answer(self, 
        question_number: Annotated[int, "1, 2, or 3"],
        user_answer: Annotated[str, "The user's response"]
    ) -> str:
        logger.info(f"LLM submitted answer for Q{question_number}: {user_answer}")
        
        if question_number == 1:
            next_state = KYCState.QUESTION_2
        elif question_number == 2:
            next_state = KYCState.QUESTION_3
        else:
            next_state = KYCState.FINAL_VERIFICATION
            
        success = await KYCOrchestrator.transition_state(self.session_id, next_state)
        if success:
            return f"Answer submitted. Proceed to {next_state.value}."
        return "Failed to submit answer."

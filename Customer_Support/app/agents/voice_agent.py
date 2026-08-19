import os
import asyncio
import logging
from dotenv import load_dotenv
load_dotenv()

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, google, silero
from app.agents.prompts import SYSTEM_PROMPT
from app.state.session_state import SessionManager
from app.state.heard_state import HeardStateManager

logger = logging.getLogger("voice_agent")

# Preload VAD model globally to avoid blocking the event loop on incoming calls
# Reduced min_silence_duration from default 0.55s to 0.25s for faster real-time responses
vad = silero.VAD.load(min_silence_duration=0.25)


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent worker."""
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    call_id = ctx.job.id if ctx.job else f"call_{os.urandom(4).hex()}"
    room_name = ctx.room.name if ctx.room else "unknown"

    logger.info(f"Agent joined room: {room_name}, job: {call_id}")

    customer_id = "CUSTOMER_UNKNOWN"
    if room_name.startswith("room_"):
        customer_id = room_name[len("room_"):]

    # --- Get or Resume Session ---
    session, is_resumed = await SessionManager.get_or_create_session(call_id, customer_id, language="english")

    heard_state = HeardStateManager()

    # --- Define tools (closures capture session_id from this call) ---
    @llm.function_tool(description="Get recent transactions for the verified customer")
    async def get_recent_transactions(limit: int = 5):
        """Retrieve the last N transactions for the current customer.
        
        Args:
            limit: Maximum number of transactions to fetch (default 5)
        """
        from app.tools.transaction_tools import get_recent_transactions as _fn
        try:
            return await _fn(session.session_id, limit)
        except Exception as e:
            logger.error(f"get_recent_transactions error: {e}")
            return f"Unable to fetch transactions at the moment. Error: {str(e)}"

    @llm.function_tool(description="Create a transaction dispute after confirming amount and transaction ID")
    async def create_dispute(transaction_id: str, amount: float, idempotency_key: str):
        """File a transaction dispute for the customer.
        
        Args:
            transaction_id: The ID of the disputed transaction
            amount: The disputed amount in the customer's currency
            idempotency_key: Unique key to prevent duplicate dispute creation
        """
        from app.tools.task_tools import create_dispute as _fn
        try:
            return await _fn(session.session_id, transaction_id, amount, idempotency_key)
        except Exception as e:
            logger.error(f"create_dispute error: {e}")
            return f"Unable to file dispute at the moment. Error: {str(e)}"

    @llm.function_tool(description="Get the overall account balance and a summary of recent spending categories")
    async def get_account_balance_and_summary():
        """Retrieve the current account balance and top spending merchants for the current customer."""
        from app.tools.transaction_tools import get_account_balance_and_summary as _fn
        try:
            return await _fn(session.session_id)
        except Exception as e:
            logger.error(f"get_account_balance_and_summary error: {e}")
            return f"Unable to fetch account summary at the moment. Error: {str(e)}"

    @llm.function_tool(description="Get detailed info about a specific transaction by its ID")
    async def get_transaction_details(transaction_id: str):
        """Get the status, amount, and merchant of a specific transaction."""
        from app.tools.transaction_tools import get_transaction_details as _fn
        try:
            return await _fn(session.session_id, transaction_id)
        except Exception as e:
            logger.error(f"get_transaction_details error: {e}")
            return f"Unable to fetch transaction details. Error: {str(e)}"

    @llm.function_tool(description="Verify the user's answer to the security question.")
    async def verify_security_question(answer: str):
        """Check if the user's answer to the security question ('What is your dog's name?') is correct."""
        from app.tools.task_tools import verify_security_question as _fn
        try:
            return await _fn(session.session_id, answer)
        except Exception as e:
            logger.error(f"verify_security_question error: {e}")
            return f"Error verifying security question: {str(e)}"

    @llm.function_tool(description="Block a credit card by its last 4 digits")
    async def block_credit_card(card_last4: str, reason: str):
        """Block the customer's credit card."""
        from app.tools.task_tools import block_credit_card as _fn
        try:
            return await _fn(session.session_id, card_last4, reason)
        except Exception as e:
            logger.error(f"block_credit_card error: {e}")
            return f"Unable to block credit card. Error: {str(e)}"

    @llm.function_tool(description="Order a replacement for a blocked or damaged credit card")
    async def order_replacement_card(card_last4: str, shipping_speed: str):
        """Order a replacement card."""
        from app.tools.task_tools import order_replacement_card as _fn
        try:
            return await _fn(session.session_id, card_last4, shipping_speed)
        except Exception as e:
            logger.error(f"order_replacement_card error: {e}")
            return f"Unable to order replacement card. Error: {str(e)}"

    @llm.function_tool(description="Report fraud on specific transactions")
    async def report_fraud(transaction_ids: list[str]):
        """Report fraudulent transactions."""
        from app.tools.task_tools import report_fraud as _fn
        try:
            return await _fn(session.session_id, transaction_ids)
        except Exception as e:
            logger.error(f"report_fraud error: {e}")
            return f"Unable to report fraud. Error: {str(e)}"

    @llm.function_tool(description="Update the customer's billing address")
    async def update_billing_address(new_address: str):
        """Update billing address."""
        from app.tools.task_tools import update_billing_address as _fn
        try:
            return await _fn(session.session_id, new_address)
        except Exception as e:
            logger.error(f"update_billing_address error: {e}")
            return f"Unable to update billing address. Error: {str(e)}"

    # --- Restore Chat Context if Resumed ---
    chat_ctx = None
    if is_resumed and session.chat_history_dict:
        try:
            chat_ctx = llm.ChatContext.from_dict(session.chat_history_dict)
            logger.info("Restored chat context from previous connection.")
        except Exception as e:
            logger.error(f"Failed to restore chat history: {e}")
    
    if not chat_ctx:
        chat_ctx = llm.ChatContext()

    # --- Build the agent ---
    agent = Agent(
        instructions=SYSTEM_PROMPT,
        stt=deepgram.STT(),
        llm=google.LLM(model="gemini-3.5-flash", api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
        tts=deepgram.TTS(),
        vad=vad,
        chat_ctx=chat_ctx,
        min_endpointing_delay=0.3,
        max_endpointing_delay=0.8,
        tools=[
            get_recent_transactions, create_dispute, get_account_balance_and_summary, get_transaction_details,
            verify_security_question, block_credit_card, order_replacement_card, report_fraud, update_billing_address
        ],
    )

    # --- Start the agent session first ---
    session_handle = AgentSession()

    # --- Wire up events on AgentSession (not Agent) ---
    @session_handle.on("agent_speech_interrupted")
    def on_interrupted(ev):
        heard_state.mark_interrupted()
        logger.info("AGENT INTERRUPTED → State rollback")

    @session_handle.on("agent_speech_committed")
    def on_completed(ev):
        if heard_state.commit_state():
            logger.info(f"STATE COMMITTED: {heard_state.get_committed_state()}")
        # Serialize chat context to session memory
        session.chat_history_dict = agent.chat_ctx.to_dict()
        asyncio.create_task(SessionManager.update_session(session))

    await session_handle.start(agent=agent, room=ctx.room)

    # Greet the customer
    await asyncio.sleep(0.5)
    disp_id = session.customer_id if session.customer_id != "CUSTOMER_UNKNOWN" else "valued customer"
    
    if is_resumed:
        await session_handle.say(
            f"Welcome back, {disp_id}! It looks like we got disconnected. What were we talking about?",
            allow_interruptions=True
        )
    else:
        await session_handle.say(
            f"Welcome to Continuum Banking, {disp_id}. For your security, could you please tell me your dog's name before we proceed?",
            allow_interruptions=True
        )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        load_threshold=float("inf")
    ))

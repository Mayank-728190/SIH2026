import logging
import asyncio
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, google, silero

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import KYCTools
from app.db.mongodb import mongodb

logger = logging.getLogger(__name__)

import os
import itertools

# Collect API keys from environment
_API_KEYS = [
    os.getenv("GOOGLE_API_KEY_1"),
    os.getenv("GOOGLE_API_KEY_2"),
    os.getenv("GOOGLE_API_KEY_3"),
]
_API_KEYS = [k for k in _API_KEYS if k]  # filter empty

if not _API_KEYS:
    logger.warning("No GOOGLE_API_KEY_X found, falling back to GOOGLE_API_KEY")
    _API_KEYS = [os.getenv("GOOGLE_API_KEY", "")]

api_key_cycler = itertools.cycle(_API_KEYS)

async def entrypoint(ctx: JobContext):
    logger.info("entrypoint started")
    if not mongodb.client:
        logger.info("Connecting to MongoDB...")
        await mongodb.connect()
        logger.info("MongoDB connected.")

    # Retrieve the session ID from the participant's metadata or room name
    session_id = ctx.room.name # For now, assuming room name is session_id
    logger.info(f"Session ID is {session_id}")
    
    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info("Room connected.")

    # Initialize the safe tools
    logger.info("Initializing KYCTools...")
    fnc_ctx = KYCTools(session_id=session_id)
    logger.info("KYCTools initialized.")

    # Select the next API key in a round-robin fashion
    current_api_key = next(api_key_cycler)
    logger.info("Using a round-robin Gemini API Key.")

    # Initialize the Agent
    logger.info("Initializing Agent...")
    agent = Agent(
        instructions=SYSTEM_PROMPT,
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(),
        llm=google.LLM(model="gemini-3.5-flash", api_key=current_api_key),
        tts=deepgram.TTS(model="aura-asteria-en"), 
        tools=[fnc_ctx],
    )
    logger.info("Agent initialized.")

    # Initialize the session and start the agent
    logger.info("Initializing AgentSession...")
    session = AgentSession()
    logger.info("AgentSession initialized.")
    
    # Inject session into tools for natural voice continuity
    logger.info("Injecting session into KYCTools...")
    fnc_ctx.set_agent_session(session)
    fnc_ctx.set_agent(agent)
    logger.info("Session injected.")
    
    logger.info("Starting session...")
    await session.start(agent, room=ctx.room)
    logger.info("Session started.")

    # Prompt the agent to introduce itself immediately
    logger.info("Saying hello...")
    session.say("Hello. I am your KYC assistant. First, I need to take your photo, then your PAN card, and finally your Aadhaar card. Do you give permission to start this verification process?", allow_interruptions=False)
    logger.info("Entrypoint complete. Waiting for session to end...")
    
    # Keep the entrypoint alive so Python GC doesn't destroy the agent/session
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass



def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

def start_agent():
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))

if __name__ == "__main__":
    start_agent()

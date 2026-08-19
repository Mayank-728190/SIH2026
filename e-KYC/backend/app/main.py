import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from livekit import api
import os

from app.config import config
from app.db.mongodb import mongodb
from app.api.documents import router as documents_router
from app.models.session import KYCSession, KYCState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await mongodb.connect()
    yield
    # Shutdown
    await mongodb.disconnect()

app = FastAPI(title=config.APP_NAME, lifespan=lifespan)

# Include routers
app.include_router(documents_router, prefix="/api/v1/kyc", tags=["KYC Uploads"])

# Serve frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
async def serve_frontend():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found"}

@app.post("/api/v1/kyc/session")
async def create_session():
    """
    Creates a new KYC session, returns a token for the LiveKit room.
    """
    import uuid
    session_id = f"KYC-{str(uuid.uuid4())[:8].upper()}"
    
    # Save to MongoDB
    session = KYCSession(session_id=session_id)
    await mongodb.create_session(session)
    
    # Generate LiveKit Token
    token = api.AccessToken(
        config.LIVEKIT_API_KEY, 
        config.LIVEKIT_API_SECRET
    )
    token.with_identity(f"user-{session_id}")
    token.with_name("Customer")
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=session_id,
    ))
    
    jwt = token.to_jwt()
    
    return {
        "session_id": session_id,
        "livekit_url": config.LIVEKIT_URL,
        "livekit_token": jwt,
        "state": session.state
    }

@app.get("/api/v1/kyc/session/{session_id}")
async def get_session(session_id: str):
    """
    Retrieves the current state of a KYC session.
    """
    session = await mongodb.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id, 
        "state": session.state.value,
        "capture_requested": session.capture_requested,
        "processing_status": session.processing_status
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "eKYC Voice Agent"
    APP_ENV: str = "development"
    
    # Thresholds (from prompt)
    NAME_THRESHOLD: float = 0.80
    FATHER_NAME_THRESHOLD: float = 0.80
    FACE_THRESHOLD: float = 0.65
    
    # Retry Limits
    MAX_FACE_RETRIES: int = 3
    MAX_PAN_RETRIES: int = 3
    MAX_AADHAAR_RETRIES: int = 3
    
    # Session
    SESSION_TIMEOUT_SECONDS: int = 3600
    HEARTBEAT_INTERVAL_SECONDS: int = 15
    
    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "ekyc_db")
    
    # LiveKit
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "devkey")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "secret")
    
    # AI APIs
    GEMINI_API_KEY: str = ""
    DEEPGRAM_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        extra = "ignore"

config = Settings()

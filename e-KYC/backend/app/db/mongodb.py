import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import config
from app.models.session import KYCSession, VerificationRecord
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class MongoDBService:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect(cls):
        try:
            cls.client = AsyncIOMotorClient(config.MONGODB_URL)
            cls.db = cls.client[config.MONGODB_DB_NAME]
            logger.info("Connected to MongoDB.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB.")

    @classmethod
    async def get_session(cls, session_id: str) -> Optional[KYCSession]:
        doc = await cls.db.kyc_sessions.find_one({"session_id": session_id})
        if doc:
            return KYCSession(**doc)
        return None

    @classmethod
    async def create_session(cls, session: KYCSession):
        doc = session.model_dump()
        await cls.db.kyc_sessions.insert_one(doc)

    @classmethod
    async def update_session_state(cls, session_id: str, new_state: str, completed_step: Optional[str] = None):
        update = {
            "$set": {
                "state": new_state,
                "updated_at": datetime.utcnow()
            },
            "$inc": {"version": 1}
        }
        if completed_step:
            update["$addToSet"] = {"completed_steps": completed_step}
            
        await cls.db.kyc_sessions.update_one({"session_id": session_id}, update)
        
    @classmethod
    async def set_capture_request(cls, session_id: str, document_type: str) -> bool:
        update = {
            "$set": {
                "capture_requested": document_type,
                "processing_status": "WAITING_FOR_CAPTURE",
                "updated_at": datetime.utcnow()
            }
        }
        res = await cls.db.kyc_sessions.update_one({"session_id": session_id}, update)
        return res.modified_count > 0

    @classmethod
    async def start_processing(cls, session_id: str, idempotency_key: str) -> bool:
        # Prevents duplicate capture processing
        update = {
            "$set": {
                "capture_requested": None,
                "processing_status": "PROCESSING",
                "capture_started_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            "$addToSet": {"idempotency_keys": idempotency_key}
        }
        # Only update if the idempotency_key is not already present
        res = await cls.db.kyc_sessions.update_one(
            {"session_id": session_id, "idempotency_keys": {"$ne": idempotency_key}}, 
            update
        )
        return res.modified_count > 0

    @classmethod
    async def set_processing_status(cls, session_id: str, status: str):
        update = {
            "$set": {
                "processing_status": status,
                "processing_completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
        await cls.db.kyc_sessions.update_one({"session_id": session_id}, update)
    @classmethod
    async def save_verification_record(cls, record: VerificationRecord):
        doc = record.model_dump()
        await cls.db.kyc_verifications.update_one(
            {"session_id": record.session_id},
            {"$set": doc},
            upsert=True
        )

    @classmethod
    async def get_verification_record(cls, session_id: str) -> Optional[VerificationRecord]:
        doc = await cls.db.kyc_verifications.find_one({"session_id": session_id})
        if doc:
            return VerificationRecord(**doc)
        return None

mongodb = MongoDBService()

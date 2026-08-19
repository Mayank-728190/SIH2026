import logging
import redis.asyncio as redis
from app.config import config
from typing import Optional

logger = logging.getLogger(__name__)

class RedisService:
    client: redis.Redis = None

    @classmethod
    async def connect(cls):
        try:
            cls.client = redis.from_url(config.REDIS_URL, decode_responses=True)
            await cls.client.ping()
            logger.info("Connected to Redis.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    @classmethod
    async def disconnect(cls):
        if cls.client:
            await cls.client.aclose()
            logger.info("Disconnected from Redis.")

    @classmethod
    async def acquire_lock(cls, session_id: str, connection_id: str, ttl_seconds: int = 30) -> bool:
        """
        Attempts to acquire a lock for a specific KYC session.
        Returns True if acquired, False if already locked by another connection.
        """
        lock_key = f"lock:kyc:{session_id}"
        acquired = await cls.client.set(lock_key, connection_id, nx=True, ex=ttl_seconds)
        return bool(acquired)

    @classmethod
    async def release_lock(cls, session_id: str, connection_id: str) -> bool:
        """
        Releases the lock only if the current connection holds it.
        """
        lock_key = f"lock:kyc:{session_id}"
        # Lua script to ensure atomicity
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        result = await cls.client.eval(script, 1, lock_key, connection_id)
        return bool(result)
    
    @classmethod
    async def renew_lock(cls, session_id: str, connection_id: str, ttl_seconds: int = 30) -> bool:
        lock_key = f"lock:kyc:{session_id}"
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        result = await cls.client.eval(script, 1, lock_key, connection_id, ttl_seconds)
        return bool(result)

redis_service = RedisService()

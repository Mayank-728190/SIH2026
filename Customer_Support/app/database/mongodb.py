import os
from motor.motor_asyncio import AsyncIOMotorClient

import certifi

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
if "?" in MONGODB_URI:
    MONGODB_URI += "&tlsAllowInvalidCertificates=true"
else:
    MONGODB_URI += "?tlsAllowInvalidCertificates=true"

MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "continuum_db")

_client = None
_db = None

def get_db():
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
        _db = _client[MONGODB_DATABASE]
    return _db

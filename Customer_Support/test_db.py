import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
if "?" in MONGODB_URI:
    MONGODB_URI += "&tlsAllowInvalidCertificates=true"
else:
    MONGODB_URI += "?tlsAllowInvalidCertificates=true"

async def main():
    try:
        print(f"Connecting to {MONGODB_URI}")
        client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        await client.server_info()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())

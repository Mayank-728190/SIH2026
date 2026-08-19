import asyncio
from qdrant_client import AsyncQdrantClient
import os
from dotenv import dotenv_values

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
print(f"Loading .env from: {dotenv_path}")
config = dotenv_values(dotenv_path)

QDRANT_URL = config.get("QDRANT_URL")
QDRANT_API_KEY = config.get("QDRANT_API_KEY")

async def test_conn():
    print(f"Connecting to Qdrant at {QDRANT_URL}")
    client = AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    try:
        collections = await client.get_collections()
        print(f"Connection successful! Collections found: {len(collections.collections)}")
        for c in collections.collections:
            print(f"- {c.name}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn())

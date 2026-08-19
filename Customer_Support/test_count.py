import asyncio
import os
import sys
sys.path.append(os.getcwd())
from app.database.mongodb import get_db

async def test():
    db = get_db()
    c = await db.customers.count_documents({})
    print(f"Customers count: {c}")

asyncio.run(test())

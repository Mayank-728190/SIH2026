import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timedelta

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "continuum_db")

async def seed_db():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    
    # Clear existing collections
    await db.customers.drop()
    await db.accounts.drop()
    await db.transactions.drop()
    await db.support_tasks.drop()

    # Seed Customers
    customers = [
        {
            "_id": "CUSTOMER_1001",
            "name": "Rahul Sharma",
            "phone_number": "+919876543210",
            "language_preference": "hinglish",
            "created_at": datetime.utcnow()
        },
        {
            "_id": "CUSTOMER_1002",
            "name": "Anita Desai",
            "phone_number": "+918765432109",
            "language_preference": "english",
            "created_at": datetime.utcnow()
        }
    ]
    await db.customers.insert_many(customers)

    # Seed Accounts
    accounts = [
        {
            "_id": "ACC_1001_1",
            "customer_id": "CUSTOMER_1001",
            "account_type": "SAVINGS",
            "status": "ACTIVE",
            "balance": 50000.0
        },
        {
            "_id": "ACC_1002_1",
            "customer_id": "CUSTOMER_1002",
            "account_type": "CHECKING",
            "status": "ACTIVE",
            "balance": 125000.0
        }
    ]
    await db.accounts.insert_many(accounts)

    # Seed Transactions
    now = datetime.utcnow()
    transactions = [
        {
            "_id": "TXN_1001_001",
            "customer_id": "CUSTOMER_1001",
            "account_id": "ACC_1001_1",
            "amount": 8500.0,
            "merchant": "Unknown Online Store",
            "timestamp": now - timedelta(hours=2),
            "status": "COMPLETED"
        },
        {
            "_id": "TXN_1001_002",
            "customer_id": "CUSTOMER_1001",
            "account_id": "ACC_1001_1",
            "amount": 250.0,
            "merchant": "Coffee Shop",
            "timestamp": now - timedelta(days=1),
            "status": "COMPLETED"
        }
    ]
    await db.transactions.insert_many(transactions)

    print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_db())

import asyncio
import os
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path, override=True)

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "continuum_db")

async def test_and_seed():
    print(f"Connecting to MongoDB at: {MONGODB_URI}")
    try:
        client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Check connection
        await client.admin.command('ping')
        print("MongoDB connection successful!")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return

    db = client[MONGODB_DATABASE]
    
    # Drop existing for a clean slate
    await db.customers.drop()
    await db.accounts.drop()
    await db.transactions.drop()

    print("Seeding 100 customers and transactions...")
    customers = []
    accounts = []
    transactions = []

    first_names = ["Rahul", "Anita", "Vikram", "Priya", "Amit", "Neha", "Sanjay", "Kavita", "Ravi", "Sneha"]
    last_names = ["Sharma", "Desai", "Singh", "Patel", "Verma", "Rao", "Iyer", "Nair", "Reddy", "Das"]
    merchants = ["Amazon", "Flipkart", "Zomato", "Swiggy", "Uber", "Ola", "Starbucks", "Reliance Mart", "BookMyShow", "IRCTC"]

    now = datetime.utcnow()

    for i in range(100):
        cust_id = f"CUST_{1000 + i}"
        acc_id = f"ACC_{1000 + i}_1"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        phone = f"+9198{random.randint(10000000, 99999999)}"
        
        customers.append({
            "_id": cust_id,
            "name": name,
            "phone_number": phone,
            "language_preference": random.choice(["english", "hindi", "hinglish"]),
            "created_at": now - timedelta(days=random.randint(10, 365))
        })

        accounts.append({
            "_id": acc_id,
            "customer_id": cust_id,
            "account_type": random.choice(["SAVINGS", "CHECKING"]),
            "status": "ACTIVE",
            "balance": round(random.uniform(5000, 500000), 2)
        })

        # Generate 1 to 5 transactions per customer
        for j in range(random.randint(1, 5)):
            txn_id = f"TXN_{cust_id}_{j}"
            transactions.append({
                "_id": txn_id,
                "customer_id": cust_id,
                "account_id": acc_id,
                "amount": round(random.uniform(50, 15000), 2),
                "merchant": random.choice(merchants),
                "timestamp": now - timedelta(hours=random.randint(1, 720)),
                "status": "COMPLETED"
            })

    await db.customers.insert_many(customers)
    await db.accounts.insert_many(accounts)
    await db.transactions.insert_many(transactions)

    print(f"Successfully inserted {len(customers)} customers, {len(accounts)} accounts, and {len(transactions)} transactions.")

if __name__ == "__main__":
    asyncio.run(test_and_seed())

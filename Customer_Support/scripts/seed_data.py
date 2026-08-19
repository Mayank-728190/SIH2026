import os
import sys
import asyncio
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

import certifi

# Ensure we can import app modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "continuum_db")

fake = Faker("en_IN")

NUM_CUSTOMERS = 1000
NUM_TRANSACTIONS = 25000

LANGUAGES = ["english", "hindi", "marathi", "tamil", "telugu", "kannada", "bengali"]
MERCHANTS = ["Amazon", "Flipkart", "Zomato", "Swiggy", "Uber", "Ola", "Reliance Fresh", "DMart", "Netflix", "Spotify", "IRCTC", "MakeMyTrip"]

async def seed_data():
    print(f"Connecting to MongoDB at {MONGODB_URI}...")
    client = AsyncIOMotorClient(
        MONGODB_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        tlsAllowInvalidCertificates=True
    )
    db = client[MONGODB_DATABASE]
    
    print("Clearing existing customers and transactions...")
    await db.customers.delete_many({})
    await db.transactions.delete_many({})
    
    print(f"Generating {NUM_CUSTOMERS} customers...")
    customers = []
    customer_ids = []
    for _ in range(NUM_CUSTOMERS):
        c_id = f"CUST_{uuid.uuid4().hex[:8].upper()}"
        customer_ids.append(c_id)
        
        phone = f"+91 {random.randint(6000000000, 9999999999)}"
        
        customer = {
            "_id": c_id,
            "id": c_id,
            "name": fake.name(),
            "phone_number": phone,
            "language_preference": random.choice(LANGUAGES),
            "created_at": datetime.utcnow()
        }
        customers.append(customer)
        
    await db.customers.insert_many(customers)
    print("Customers inserted.")
    
    print(f"Generating {NUM_TRANSACTIONS} transactions...")
    transactions = []
    for i in range(NUM_TRANSACTIONS):
        c_id = random.choice(customer_ids)
        t_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        
        days_ago = random.randint(0, 365)
        t_time = datetime.utcnow() - timedelta(days=days_ago, minutes=random.randint(0, 1440))
        
        tx = {
            "_id": t_id,
            "id": t_id,
            "customer_id": c_id,
            "account_id": f"ACC_{c_id[-8:]}",
            "amount": round(random.uniform(50.0, 15000.0), 2),
            "merchant": random.choice(MERCHANTS),
            "timestamp": t_time,
            "status": "COMPLETED"
        }
        transactions.append(tx)
        
        if len(transactions) == 5000:
            await db.transactions.insert_many(transactions)
            transactions = []
            print(f"Inserted {i+1}/{NUM_TRANSACTIONS} transactions...")
            
    if transactions:
        await db.transactions.insert_many(transactions)
        
    print("All transactions inserted successfully.")
    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())

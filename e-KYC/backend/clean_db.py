import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import shutil
from app.config import config

async def main():
    # Clear MongoDB
    print(f"Connecting to {config.MONGODB_URL}")
    client = AsyncIOMotorClient(config.MONGODB_URL)
    db = client[config.MONGODB_DB_NAME]
    
    await db.kyc_sessions.drop()
    print("Dropped kyc_sessions collection")
    
    await db.kyc_verifications.drop()
    print("Dropped kyc_verifications collection")
    
    # Delete images
    processed_dir = "data/processed"
    if os.path.exists(processed_dir):
        shutil.rmtree(processed_dir)
        os.makedirs(processed_dir)
        print(f"Cleared all images in {processed_dir}")
    else:
        print(f"{processed_dir} does not exist.")
        
    print("Cleanup complete!")

if __name__ == "__main__":
    asyncio.run(main())

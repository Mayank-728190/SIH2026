import asyncio
import os
from dotenv import load_dotenv

# Load .env before importing app modules
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)
from qdrant_client.models import VectorParams, Distance, PointStruct
from app.database.qdrant import get_qdrant
from app.services.retrieval_service import RetrievalService, _generate_embedding
import uuid

async def seed_qdrant():
    qdrant = get_qdrant()
    collection_name = RetrievalService.COLLECTION_NAME
    
    # Check if collection exists, if not create
    collections = await qdrant.get_collections()
    if not any(c.name == collection_name for c in collections.collections):
        await qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
    
    knowledge_docs = [
        "If a customer reports an unauthorized transaction, verify the transaction details (amount, merchant) and file a dispute. Standard dispute resolution takes 7-14 business days.",
        "To replace a lost debit card, verify the customer's identity and confirm their address before issuing a new card. The card will arrive in 3-5 business days.",
        "For loan application status, retrieve the application ID and check the current processing stage. Escalate to the loan officer if the status has been pending for more than 5 days."
    ]

    points = []
    for doc in knowledge_docs:
        vector = await _generate_embedding(doc)
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"content": doc}
            )
        )

    await qdrant.upsert(
        collection_name=collection_name,
        points=points
    )
    print("Qdrant seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_qdrant())

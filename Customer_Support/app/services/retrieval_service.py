from app.database.qdrant import get_qdrant
import uuid
import json

# Placeholder for embedding generation. In real app, use Gemini embeddings API.
async def _generate_embedding(text: str):
    # Mocking a 768-dim embedding
    import random
    return [random.uniform(-1, 1) for _ in range(768)]

class RetrievalService:
    COLLECTION_NAME = "banking_knowledge"

    @staticmethod
    async def search_knowledge(query: str, limit: int = 3) -> list[str]:
        qdrant = get_qdrant()
        try:
            # We assume collection exists. In real app, check it.
            query_vector = await _generate_embedding(query)
            search_result = await qdrant.search(
                collection_name=RetrievalService.COLLECTION_NAME,
                query_vector=query_vector,
                limit=limit
            )
            return [hit.payload.get("content", "") for hit in search_result if hit.payload]
        except Exception as e:
            print(f"Error searching Qdrant: {e}")
            return []

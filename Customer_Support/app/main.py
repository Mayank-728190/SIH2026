import os
from datetime import timedelta
import uuid
import asyncio
import logging
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from livekit.api import AccessToken, VideoGrants

from app.state.session_state import SessionManager
from app.models.customer import Customer
from app.database.mongodb import get_db

app = FastAPI(title="Continuum Voice Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Customers are now stored in MongoDB ---

# --- Pydantic Request/Response Models ---
class TokenRequest(BaseModel):
    participant_name: str
    customer_id: Optional[str] = None

class CreateCustomerRequest(BaseModel):
    name: str
    phone_number: str
    language_preference: str = "english"

# --- Health ---
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# --- Customer Endpoints ---
@app.get("/customers")
async def list_customers():
    """List all registered customers (limited to 100 for dashboard performance)."""
    db = get_db()
    cursor = db.customers.find().sort("created_at", -1).limit(100)
    customers = await cursor.to_list(length=100)
    
    # Map _id back to id if needed, though they are the same in our seeder
    result = []
    for c in customers:
        c["id"] = c.get("_id", c.get("id"))
        result.append(Customer(**c))
    return {"customers": result}

@app.post("/customers", status_code=201)
async def create_customer(req: CreateCustomerRequest):
    """Create a new customer and return their profile."""
    customer_id = f"CUST_{uuid.uuid4().hex[:8].upper()}"
    customer = Customer(
        id=customer_id,
        name=req.name,
        phone_number=req.phone_number,
        language_preference=req.language_preference,
    )
    
    db = get_db()
    doc = customer.model_dump()
    doc["_id"] = customer_id
    await db.customers.insert_one(doc)
    
    return {"customer": customer}

@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Get a specific customer by ID."""
    db = get_db()
    customer_doc = await db.customers.find_one({"_id": customer_id})
    if not customer_doc:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    customer_doc["id"] = customer_doc.get("_id", customer_doc.get("id"))
    return {"customer": Customer(**customer_doc)}

# --- Session Endpoints ---
@app.get("/sessions")
async def list_sessions():
    """List all active in-memory sessions."""
    from app.state.session_state import _sessions
    return {"sessions": [s.dict() for s in _sessions.values()]}

# --- Token / LiveKit ---
@app.post("/getToken")
async def get_token(req: TokenRequest):
    """Generate a LiveKit token. Creates a new session tied to the customer."""
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="LiveKit credentials not configured")

    # Each customer gets their own isolated room
    customer_id = req.customer_id or req.participant_name
    room_name = f"room_{customer_id}"

    grant = VideoGrants(room_join=True, room=room_name)
    token = (
        AccessToken(api_key, api_secret)
        .with_identity(req.participant_name)
        .with_name(req.participant_name)
        .with_grants(grant)
        .with_ttl(timedelta(hours=1))
    )

    return {
        "token": token.to_jwt(),
        "room_name": room_name,
        "customer_id": customer_id,
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

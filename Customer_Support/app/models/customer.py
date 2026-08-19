from pydantic import BaseModel, Field
from datetime import datetime

class Customer(BaseModel):
    id: str
    name: str
    phone_number: str
    language_preference: str = "english"
    created_at: datetime = Field(default_factory=datetime.utcnow)

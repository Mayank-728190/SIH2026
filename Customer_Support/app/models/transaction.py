from pydantic import BaseModel, Field
from datetime import datetime

class Transaction(BaseModel):
    id: str
    customer_id: str
    account_id: str
    amount: float
    merchant: str
    timestamp: datetime
    status: str = "COMPLETED" # PENDING, COMPLETED, FAILED

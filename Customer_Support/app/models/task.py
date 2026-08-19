from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class TaskEvent(BaseModel):
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)

class SupportTask(BaseModel):
    task_id: str
    customer_id: str
    task_type: str
    status: str = "IN_PROGRESS" # IN_PROGRESS, COMPLETED, CANCELLED, ESCALATED
    current_step: str
    completed_steps: List[str] = Field(default_factory=list)
    confirmed_data: Dict[str, Any] = Field(default_factory=dict)
    pending_steps: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_call_id: Optional[str] = None
    events: List[TaskEvent] = Field(default_factory=list)

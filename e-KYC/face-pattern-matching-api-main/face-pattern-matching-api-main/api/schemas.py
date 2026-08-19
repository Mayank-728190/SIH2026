from pydantic import BaseModel
from typing import Optional, List

class FaceMatchDetail(BaseModel):
    face1_id: str
    face2_id: str
    score: float
    status: str

class FaceMatchResponse(BaseModel):
    matches: List[FaceMatchDetail] = []
    image1_processed: Optional[str] = None
    image2_processed: Optional[str] = None
    error: Optional[str] = None

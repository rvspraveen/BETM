from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class ReviewOut(BaseModel):
    id: int
    investigation_id: str
    query_text: str
    ai_answer: str
    confidence: float
    escalation_reason: str
    status: str
    reviewer_notes: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReviewResolveRequest(BaseModel):
    status: Literal["approved", "rejected"]
    reviewer_notes: Optional[str] = None

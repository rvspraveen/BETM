from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentIn(BaseModel):
    title: str
    doc_type: str
    source: str
    effective_date: Optional[datetime] = None
    content: str
    metadata: Optional[dict] = None


class DocumentOut(BaseModel):
    id: int
    title: str
    doc_type: str
    source: str
    effective_date: Optional[datetime]
    ingested_at: datetime
    chunk_count: int = 0

    class Config:
        from_attributes = True

"""Human review queue — items escalated by the AI when confidence is low."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Float, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReviewItem(Base):
    __tablename__ = "review_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    investigation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    ai_answer: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    escalation_reason: Mapped[str] = mapped_column(Text, nullable=False)
    # pending, approved, rejected
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

"""Health + info endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

EXAMPLE_QUERIES = [
    {"id": 1, "category": "doc", "text": "What does ERCOT protocol section 4.4 say about ancillary service obligations?"},
    {"id": 2, "category": "doc", "text": "Summarize recent market notices about transmission outage deferral"},
    {"id": 3, "category": "doc", "text": "What are the settlement rule changes effective this quarter?"},
    {"id": 4, "category": "analytics", "text": "Show DA/RT price divergence at HB_HOUSTON for the last 48 hours"},
    {"id": 5, "category": "analytics", "text": "Which nodes have the highest congestion exposure for book ERCOT_NORTH?"},
    {"id": 6, "category": "analytics", "text": "List the top 10 RT price spikes above $500/MWh in the last 7 days"},
    {"id": 7, "category": "hybrid", "text": "What caused the congestion event on the Brazos-to-Houston constraint yesterday?"},
    {"id": 8, "category": "hybrid", "text": "Give me a settlement variance summary and explain the key discrepancies"},
    {"id": 9, "category": "uncertainty", "text": "There is a timing disagreement between outage notice MN-2024-1120 and SCADA data — explain"},
    {"id": 10, "category": "uncertainty", "text": "Resolve the node alias conflict between HB_NORTH and LZ_NORTH in our position data"},
    {"id": 11, "category": "analytics", "text": "What is the current generation mix and how much wind is being curtailed?"},
    {"id": 12, "category": "hybrid", "text": "Explain the P&L variance for book ERCOT_WEST last week vs the week before"},
]


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Liveness + dependency check."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": (
            settings.OPENAI_MODEL
            if settings.LLM_PROVIDER == "openai"
            else settings.ANTHROPIC_MODEL
        ),
        "database": db_status,
    }


@router.get("/examples")
async def get_examples():
    """Return pre-built example queries for the UI."""
    return EXAMPLE_QUERIES

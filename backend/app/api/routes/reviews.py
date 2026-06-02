"""Human review queue endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.reviews import ReviewItem
from app.schemas.reviews import ReviewOut, ReviewResolveRequest

router = APIRouter()


@router.get("/reviews", response_model=list[ReviewOut])
async def list_reviews(
    status: str = Query("pending", description="Filter by status: pending, approved, rejected, all"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ReviewItem).order_by(ReviewItem.created_at.desc())
    if status != "all":
        stmt = stmt.where(ReviewItem.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/reviews/count")
async def review_count(db: AsyncSession = Depends(get_db)):
    """Quick badge count for the sidebar."""
    from sqlalchemy import func
    result = await db.execute(
        select(func.count()).where(ReviewItem.status == "pending")
    )
    return {"pending": result.scalar() or 0}


@router.get("/reviews/{review_id}", response_model=ReviewOut)
async def get_review(review_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(ReviewItem, review_id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    return item


@router.post("/reviews/{review_id}/resolve", response_model=ReviewOut)
async def resolve_review(
    review_id: int,
    body: ReviewResolveRequest,
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(ReviewItem, review_id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    if item.status != "pending":
        raise HTTPException(status_code=409, detail=f"Review already {item.status}")

    item.status = body.status
    item.reviewer_notes = body.reviewer_notes
    item.resolved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(item)
    return item

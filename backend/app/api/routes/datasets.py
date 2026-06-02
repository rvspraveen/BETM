"""Dataset listing and analytics summary endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from datetime import datetime, timedelta

from app.core.database import get_db
from app.schemas.analytics import DatasetSummary
from app.services import analytics as svc

router = APIRouter()

DATASETS = [
    {"name": "Day-Ahead Prices", "table": "market_prices_da", "description": "Hourly DA LMP by node ($/MWh) — energy, congestion, loss components"},
    {"name": "Real-Time Prices", "table": "market_prices_rt", "description": "5-min RT LMP by node ($/MWh)"},
    {"name": "Binding Constraints", "table": "constraints", "description": "Binding constraint shadow prices ($/MWh) by interval"},
    {"name": "Outages", "table": "outages", "description": "Generation and transmission outage events with MW and timing"},
    {"name": "Positions", "table": "positions", "description": "Trading book positions — MW, avg price, mark, Greeks"},
    {"name": "Settlements", "table": "settlements", "description": "DA vs RT settlement charges by book and node"},
    {"name": "Load Forecast", "table": "load_forecast", "description": "ERCOT STLF forecast vs actuals by zone (MW)"},
    {"name": "Generation Mix", "table": "generation_mix", "description": "Generation by fuel type — capacity factor and curtailment"},
    {"name": "Trade P&L", "table": "trade_pnl", "description": "Daily realized and unrealized P&L by book and strategy"},
    {"name": "Node Aliases", "table": "node_aliases", "description": "Canonical node IDs and their aliases across systems"},
    {"name": "Congestion Archive", "table": "congestion_archive", "description": "Historical congestion events with shadow prices and rentals"},
    {"name": "DA LMP", "table": "da_lmp", "description": "Compact day-ahead locational marginal prices by datetime and node"},
    {"name": "RT LMP", "table": "rt_lmp", "description": "Compact real-time locational marginal prices with corresponding DA prices"},
    {"name": "FTR / CRR Positions", "table": "ftr_positions", "description": "Financial transmission rights / congestion revenue rights positions by book and node"},
    {"name": "Physical Positions", "table": "physical_positions", "description": "Physical generation and load exposure by book, node, direction and MW"},
    {"name": "Asset Metadata", "table": "asset_metadata", "description": "Node, hub, region, book and asset type metadata"},
]


@router.get("/datasets", response_model=list[DatasetSummary])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    """Return metadata for all available datasets with current row counts."""
    result = []
    for ds in DATASETS:
        try:
            count_res = await db.execute(text(f"SELECT COUNT(*) FROM {ds['table']}"))
            count = count_res.scalar() or 0
        except Exception:
            count = 0

        result.append(DatasetSummary(
            name=ds["name"],
            table=ds["table"],
            row_count=count,
            description=ds["description"],
        ))
    return result


@router.post("/ingest/datasets")
async def trigger_dataset_reload(db: AsyncSession = Depends(get_db)):
    """
    Trigger a dataset reload from CSV files.
    In production this kicks off a Celery task; here it returns a task ticket.
    """
    return {
        "status": "queued",
        "message": "Dataset reload queued. Run 'python data/seed.py' to reload from CSVs.",
        "task_id": "manual_reload",
    }


@router.get("/analytics/price-spikes")
async def price_spikes(
    threshold: float = Query(200.0, description="LMP threshold $/MWh"),
    hours_back: int = Query(168, description="Lookback hours"),
    market: str = Query("rt", description="rt or da"),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_price_spikes(db, threshold_usd=threshold, hours_back=hours_back, market=market)


@router.get("/analytics/da-rt-divergence")
async def da_rt_divergence(
    node_id: str = Query(None),
    hours_back: int = Query(48),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_da_rt_divergence(db, node_id=node_id, hours_back=hours_back)


@router.get("/analytics/congestion-exposure")
async def congestion_exposure(
    book: str = Query(None),
    days_back: int = Query(30),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_congestion_exposure(db, book=book, days_back=days_back)


@router.get("/analytics/settlement-variance")
async def settlement_variance(
    days_back: int = Query(30),
    book: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_settlement_variance(db, days_back=days_back, book=book)


@router.get("/analytics/pnl-summary")
async def pnl_summary(
    days_back: int = Query(30),
    book: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_pnl_summary(db, days_back=days_back, book=book)


@router.get("/analytics/generation-mix")
async def generation_mix(
    hours_back: int = Query(24),
    db: AsyncSession = Depends(get_db),
):
    return await svc.get_generation_mix_summary(db, hours_back=hours_back)


@router.get("/analytics/positions")
async def get_positions(
    book: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return current positions for the PositionsView."""
    from app.models.market_data import Position
    stmt = select(Position).order_by(Position.trade_date.desc())
    if book:
        stmt = stmt.where(Position.book == book)
    result = await db.execute(stmt)
    positions = result.scalars().all()
    return [
        {
            "id": p.id,
            "trade_date": p.trade_date.isoformat(),
            "book": p.book,
            "node_id": p.node_id,
            "node_name": p.node_name,
            "product": p.product,
            "quantity_mw": p.quantity_mw,
            "avg_price": p.avg_price,
            "mark_price": p.mark_price,
            "unrealized_pnl": p.unrealized_pnl,
            "delta": p.delta,
        }
        for p in positions
    ]

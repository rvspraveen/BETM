"""
Analytics Engine — deterministic SQL/pandas computations.
No LLM here; pure math so results are reproducible and auditable.
"""
from datetime import date, datetime, time, timedelta
from typing import Optional, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

log = structlog.get_logger()


async def _lookback_cutoff(
    db: AsyncSession,
    table: str,
    column: str,
    lookback: timedelta,
) -> datetime:
    """Anchor lookbacks to the newest row in synthetic/historical datasets."""
    result = await db.execute(text(f"SELECT MAX({column}) FROM {table}"))
    anchor = result.scalar()
    if isinstance(anchor, datetime):
        return anchor - lookback
    if isinstance(anchor, date):
        return datetime.combine(anchor, time.min) - lookback
    return datetime.utcnow() - lookback


async def _lookback_cutoff_date(
    db: AsyncSession,
    table: str,
    column: str,
    lookback: timedelta,
) -> date:
    cutoff = await _lookback_cutoff(db, table, column, lookback)
    return cutoff.date()


# ── Price Spike Analysis ────────────────────────────────────────────────────

async def get_price_spikes(
    db: AsyncSession,
    threshold_usd: float = 200.0,
    hours_back: int = 168,          # 7 days
    market: str = "rt",
) -> dict[str, Any]:
    """Return intervals where LMP exceeded threshold."""
    table = "market_prices_rt" if market == "rt" else "market_prices_da"
    cutoff = await _lookback_cutoff(db, table, "interval_start", timedelta(hours=hours_back))

    result = await db.execute(text(f"""
        SELECT
            node_id,
            node_name,
            zone,
            interval_start,
            lmp,
            congestion_component
        FROM {table}
        WHERE lmp >= :threshold
          AND interval_start >= :cutoff
        ORDER BY lmp DESC
        LIMIT 50
    """), {"threshold": threshold_usd, "cutoff": cutoff})

    rows = result.fetchall()
    spikes = [
        {
            "node_id": r.node_id,
            "node_name": r.node_name,
            "zone": r.zone,
            "interval": r.interval_start.isoformat(),
            "lmp": round(r.lmp, 2),
            "congestion": round(r.congestion_component, 2),
        }
        for r in rows
    ]
    return {
        "type": "price_spikes",
        "market": market.upper(),
        "threshold": threshold_usd,
        "count": len(spikes),
        "spikes": spikes,
    }


# ── DA/RT Divergence ────────────────────────────────────────────────────────

async def get_da_rt_divergence(
    db: AsyncSession,
    node_id: str = None,
    hours_back: int = 48,
) -> dict[str, Any]:
    """Compare day-ahead vs real-time LMPs to surface convergence risk."""
    cutoff = await _lookback_cutoff(db, "market_prices_rt", "interval_start", timedelta(hours=hours_back))
    node_filter = "AND da.node_id = :node_id" if node_id else ""
    params: dict = {"cutoff": cutoff}
    if node_id:
        params["node_id"] = node_id

    result = await db.execute(text(f"""
        SELECT
            da.node_id,
            da.node_name,
            da.interval_start,
            da.lmp AS da_lmp,
            rt.lmp AS rt_lmp,
            (rt.lmp - da.lmp) AS divergence
        FROM market_prices_da da
        JOIN market_prices_rt rt
          ON rt.node_id = da.node_id
         AND rt.interval_start = da.interval_start
        WHERE da.interval_start >= :cutoff
          {node_filter}
        ORDER BY ABS(rt.lmp - da.lmp) DESC
        LIMIT 100
    """), params)

    rows = result.fetchall()
    records = [
        {
            "node_id": r.node_id,
            "node_name": r.node_name,
            "interval": r.interval_start.isoformat(),
            "da_lmp": round(r.da_lmp, 2),
            "rt_lmp": round(r.rt_lmp, 2),
            "divergence": round(r.divergence, 2),
        }
        for r in rows
    ]
    avg_div = (sum(r["divergence"] for r in records) / len(records)) if records else 0
    return {
        "type": "da_rt_divergence",
        "node_filter": node_id,
        "record_count": len(records),
        "avg_divergence": round(avg_div, 2),
        "records": records[:25],  # first 25 for context
    }


# ── Congestion Exposure ─────────────────────────────────────────────────────

async def get_congestion_exposure(
    db: AsyncSession,
    book: str = None,
    days_back: int = 30,
) -> dict[str, Any]:
    """Summarise congestion component impact on book positions."""
    cutoff = await _lookback_cutoff(db, "market_prices_rt", "interval_start", timedelta(days=days_back))
    book_filter = "AND p.book = :book" if book else ""
    params: dict = {"cutoff": cutoff}
    if book:
        params["book"] = book

    result = await db.execute(text(f"""
        SELECT
            p.book,
            p.node_id,
            p.node_name,
            SUM(p.quantity_mw) AS total_mw,
            AVG(rt.congestion_component) AS avg_congestion,
            SUM(p.quantity_mw * rt.congestion_component) AS congestion_exposure
        FROM positions p
        LEFT JOIN market_prices_rt rt
            ON rt.node_id = p.node_id
           AND rt.interval_start >= :cutoff
        WHERE p.trade_date >= :cutoff
          {book_filter}
        GROUP BY p.book, p.node_id, p.node_name
        ORDER BY ABS(SUM(p.quantity_mw * rt.congestion_component)) DESC
        LIMIT 20
    """), params)

    rows = result.fetchall()
    records = [
        {
            "book": r.book,
            "node_id": r.node_id,
            "node_name": r.node_name,
            "total_mw": round(r.total_mw or 0, 1),
            "avg_congestion": round(r.avg_congestion or 0, 2),
            "exposure": round(r.congestion_exposure or 0, 2),
        }
        for r in rows
    ]
    return {
        "type": "congestion_exposure",
        "book_filter": book,
        "record_count": len(records),
        "records": records,
    }


# ── Settlement Variance ─────────────────────────────────────────────────────

async def get_settlement_variance(
    db: AsyncSession,
    days_back: int = 30,
    book: str = None,
) -> dict[str, Any]:
    """Compare DA vs RT settlement charges to find unexpected variances."""
    cutoff = await _lookback_cutoff_date(db, "settlements", "settlement_date", timedelta(days=days_back))
    book_filter = "AND book = :book" if book else ""
    params: dict = {"cutoff": cutoff}
    if book:
        params["book"] = book

    result = await db.execute(text(f"""
        SELECT
            book,
            node_id,
            SUM(da_charge) AS total_da,
            SUM(rt_charge) AS total_rt,
            SUM(net_settlement) AS net,
            COUNT(*) AS days
        FROM settlements
        WHERE settlement_date >= :cutoff
          {book_filter}
        GROUP BY book, node_id
        ORDER BY ABS(SUM(net_settlement)) DESC
        LIMIT 20
    """), params)

    rows = result.fetchall()
    records = [
        {
            "book": r.book,
            "node_id": r.node_id,
            "total_da": round(r.total_da or 0, 2),
            "total_rt": round(r.total_rt or 0, 2),
            "net": round(r.net or 0, 2),
            "days": r.days,
        }
        for r in rows
    ]
    return {
        "type": "settlement_variance",
        "record_count": len(records),
        "records": records,
    }


# ── Load Forecast Accuracy ──────────────────────────────────────────────────

async def get_load_forecast_accuracy(
    db: AsyncSession,
    zone: str = None,
    hours_back: int = 168,
) -> dict[str, Any]:
    cutoff = await _lookback_cutoff(db, "load_forecast", "interval_start", timedelta(hours=hours_back))
    zone_filter = "AND zone = :zone" if zone else ""
    params: dict = {"cutoff": cutoff}
    if zone:
        params["zone"] = zone

    result = await db.execute(text(f"""
        SELECT
            zone,
            AVG(forecast_mw) AS avg_forecast,
            AVG(actual_mw) AS avg_actual,
            AVG(ABS(forecast_error_mw)) AS mae,
            MAX(ABS(forecast_error_mw)) AS max_error
        FROM load_forecast
        WHERE interval_start >= :cutoff
          AND actual_mw IS NOT NULL
          {zone_filter}
        GROUP BY zone
        ORDER BY mae DESC
    """), params)

    rows = result.fetchall()
    records = [
        {
            "zone": r.zone,
            "avg_forecast_mw": round(r.avg_forecast or 0, 1),
            "avg_actual_mw": round(r.avg_actual or 0, 1),
            "mae_mw": round(r.mae or 0, 1),
            "max_error_mw": round(r.max_error or 0, 1),
        }
        for r in rows
    ]
    return {"type": "load_forecast_accuracy", "records": records}


# ── Generation Mix ──────────────────────────────────────────────────────────

async def get_generation_mix_summary(
    db: AsyncSession,
    hours_back: int = 24,
) -> dict[str, Any]:
    cutoff = await _lookback_cutoff(db, "generation_mix", "interval_start", timedelta(hours=hours_back))
    result = await db.execute(text("""
        SELECT
            fuel_type,
            AVG(generation_mw) AS avg_gen,
            AVG(capacity_factor) AS avg_cf,
            SUM(curtailment_mw) AS total_curtailment
        FROM generation_mix
        WHERE interval_start >= :cutoff
        GROUP BY fuel_type
        ORDER BY avg_gen DESC
    """), {"cutoff": cutoff})

    rows = result.fetchall()
    records = [
        {
            "fuel_type": r.fuel_type,
            "avg_generation_mw": round(r.avg_gen or 0, 1),
            "avg_capacity_factor": round(r.avg_cf or 0, 3),
            "total_curtailment_mw": round(r.total_curtailment or 0, 1),
        }
        for r in rows
    ]
    return {"type": "generation_mix", "hours_back": hours_back, "records": records}


# ── P&L Summary ─────────────────────────────────────────────────────────────

async def get_pnl_summary(
    db: AsyncSession,
    days_back: int = 30,
    book: str = None,
) -> dict[str, Any]:
    cutoff = await _lookback_cutoff_date(db, "trade_pnl", "trade_date", timedelta(days=days_back))
    book_filter = "AND book = :book" if book else ""
    params: dict = {"cutoff": cutoff}
    if book:
        params["book"] = book

    result = await db.execute(text(f"""
        SELECT
            book,
            strategy,
            SUM(realized_pnl) AS realized,
            SUM(unrealized_pnl) AS unrealized,
            SUM(total_pnl) AS total,
            SUM(volume_mwh) AS volume
        FROM trade_pnl
        WHERE trade_date >= :cutoff
          {book_filter}
        GROUP BY book, strategy
        ORDER BY total DESC
    """), params)

    rows = result.fetchall()
    records = [
        {
            "book": r.book,
            "strategy": r.strategy,
            "realized_pnl": round(r.realized or 0, 2),
            "unrealized_pnl": round(r.unrealized or 0, 2),
            "total_pnl": round(r.total or 0, 2),
            "volume_mwh": round(r.volume or 0, 1),
        }
        for r in rows
    ]
    return {"type": "pnl_summary", "days_back": days_back, "records": records}

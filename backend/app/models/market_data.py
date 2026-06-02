"""
Market data models covering all 11 CSVs from §6.1 of the assignment:
  1. market_prices_da        (day-ahead LMPs)
  2. market_prices_rt        (real-time LMPs)
  3. constraints             (binding constraints + shadow prices)
  4. outages                 (generation/transmission outages)
  5. positions               (trading book positions)
  6. settlements             (DA vs RT settlement charges)
  7. load_forecast           (ERCOT load forecast vs actual)
  8. generation_mix          (fuel-type generation)
  9. trade_pnl               (daily P&L by book)
10. node_aliases            (pricing node alias mapping)
11. congestion_archive      (historical congestion events)

Additional synthetic datasets:
 12. da_lmp                  (compact day-ahead LMPs)
 13. rt_lmp                  (compact real-time LMPs)
 14. ftr_positions           (FTR / CRR positions)
 15. physical_positions      (physical generation / load exposure)
 16. asset_metadata          (nodes, hubs, plants, books, traders, regions)
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    String, Float, DateTime, Date, Integer, Boolean, Text, JSON, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MarketPriceDA(Base):
    __tablename__ = "market_prices_da"
    __table_args__ = (UniqueConstraint("interval_start", "node_id", name="uq_da_node_interval"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interval_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    interval_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    node_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    node_name: Mapped[str] = mapped_column(String(128), nullable=False)
    zone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    lmp: Mapped[float] = mapped_column(Float, nullable=False)          # $/MWh
    energy_component: Mapped[float] = mapped_column(Float, default=0.0)
    congestion_component: Mapped[float] = mapped_column(Float, default=0.0)
    loss_component: Mapped[float] = mapped_column(Float, default=0.0)


class MarketPriceRT(Base):
    __tablename__ = "market_prices_rt"
    __table_args__ = (UniqueConstraint("interval_start", "node_id", name="uq_rt_node_interval"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interval_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    interval_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    node_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    node_name: Mapped[str] = mapped_column(String(128), nullable=False)
    zone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    lmp: Mapped[float] = mapped_column(Float, nullable=False)
    energy_component: Mapped[float] = mapped_column(Float, default=0.0)
    congestion_component: Mapped[float] = mapped_column(Float, default=0.0)
    loss_component: Mapped[float] = mapped_column(Float, default=0.0)


class Constraint(Base):
    __tablename__ = "constraints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interval_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    constraint_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    constraint_name: Mapped[str] = mapped_column(String(256), nullable=False)
    shadow_price: Mapped[float] = mapped_column(Float, nullable=False)    # $/MWh
    flow_mw: Mapped[float] = mapped_column(Float, default=0.0)
    limit_mw: Mapped[float] = mapped_column(Float, default=0.0)
    contingency: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    is_binding: Mapped[bool] = mapped_column(Boolean, default=True)


class Outage(Base):
    __tablename__ = "outages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    outage_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    resource_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)  # gen, tx
    capacity_mw: Mapped[float] = mapped_column(Float, default=0.0)
    outage_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    outage_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notice_issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")  # active, restored


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    book: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    node_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    node_name: Mapped[str] = mapped_column(String(128), nullable=False)
    product: Mapped[str] = mapped_column(String(32), nullable=False)   # DA, RT, CRR
    quantity_mw: Mapped[float] = mapped_column(Float, nullable=False)
    avg_price: Mapped[float] = mapped_column(Float, nullable=False)
    mark_price: Mapped[float] = mapped_column(Float, nullable=False)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    delta: Mapped[float] = mapped_column(Float, default=0.0)
    gamma: Mapped[float] = mapped_column(Float, default=0.0)
    theta: Mapped[float] = mapped_column(Float, default=0.0)


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    settlement_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    node_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    book: Mapped[str] = mapped_column(String(64), nullable=False)
    da_charge: Mapped[float] = mapped_column(Float, default=0.0)
    rt_charge: Mapped[float] = mapped_column(Float, default=0.0)
    net_settlement: Mapped[float] = mapped_column(Float, default=0.0)
    da_quantity_mwh: Mapped[float] = mapped_column(Float, default=0.0)
    rt_quantity_mwh: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="preliminary")


class LoadForecast(Base):
    __tablename__ = "load_forecast"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interval_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    zone: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    forecast_mw: Mapped[float] = mapped_column(Float, nullable=False)
    actual_mw: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    forecast_error_mw: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    forecast_type: Mapped[str] = mapped_column(String(32), default="STLF")  # STLF or MTLF
    temperature_f: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class GenerationMix(Base):
    __tablename__ = "generation_mix"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interval_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    fuel_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # wind, solar, gas, coal, nuclear, hydro, other
    generation_mw: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_mw: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    curtailment_mw: Mapped[float] = mapped_column(Float, default=0.0)


class TradePnL(Base):
    __tablename__ = "trade_pnl"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    book: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    volume_mwh: Mapped[float] = mapped_column(Float, default=0.0)
    fees: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class NodeAlias(Base):
    __tablename__ = "node_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    alias_type: Mapped[str] = mapped_column(String(32), default="market")
    # market, internal, legacy, doc_reference
    source: Mapped[str] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class CongestionEvent(Base):
    __tablename__ = "congestion_archive"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    event_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    constraint_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    affected_nodes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    max_shadow_price: Mapped[float] = mapped_column(Float, default=0.0)
    total_congestion_rent: Mapped[float] = mapped_column(Float, default=0.0)
    related_outage_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DaLmp(Base):
    __tablename__ = "da_lmp"
    __table_args__ = (UniqueConstraint("datetime", "node", name="uq_da_lmp_node_datetime"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    node: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    da_lmp: Mapped[float] = mapped_column(Float, nullable=False)


class RtLmp(Base):
    __tablename__ = "rt_lmp"
    __table_args__ = (UniqueConstraint("datetime", "node", name="uq_rt_lmp_node_datetime"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    node: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    da_lmp: Mapped[float] = mapped_column(Float, nullable=False)
    rt_lmp: Mapped[float] = mapped_column(Float, nullable=False)


class FtrPosition(Base):
    __tablename__ = "ftr_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    node: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    mw: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)


class PhysicalPosition(Base):
    __tablename__ = "physical_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    node: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    mw: Mapped[float] = mapped_column(Float, nullable=False)


class AssetMetadata(Base):
    __tablename__ = "asset_metadata"
    __table_args__ = (UniqueConstraint("node", "book", "asset_type", name="uq_asset_metadata_node_book_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    node: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    hub: Mapped[str] = mapped_column(String(128), nullable=False)
    region: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    book: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

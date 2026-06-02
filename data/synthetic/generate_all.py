"""
Generate all 11 synthetic CSVs with realistic ERCOT market data.

Events baked in:
  Event A — Price spike at HB_HOUSTON on 2024-06-15 14:00 (RT >$800/MWh)
             caused by Brazos Valley Unit-3 trip + binding Sabine constraint
  Event B — Settlement anomaly on 2024-06-22: ERCOT_WEST book DA/RT divergence
             due to wind curtailment triggering negative prices
  Event C — Congestion on 2024-07-04: Travis County constraint activates
             during summer peak, shadow price $243/MWh

Run: python generate_all.py
Outputs: ../market_prices_da.csv, ../market_prices_rt.csv, etc.
"""
import csv
import random
import math
from datetime import datetime, timedelta, date
from pathlib import Path

random.seed(42)
OUT = Path(__file__).parent.parent

NODES = [
    ("HB_HOUSTON", "Houston Hub", "SOUTH"),
    ("HB_NORTH", "North Hub", "NORTH"),
    ("HB_WEST", "West Hub", "WEST"),
    ("HB_SOUTH", "South Hub", "SOUTH"),
    ("LZ_HOUSTON", "Houston Load Zone", "SOUTH"),
    ("LZ_NORTH", "North Load Zone", "NORTH"),
    ("LZ_WEST", "West Load Zone", "WEST"),
    ("LZ_SOUTH", "South Load Zone", "SOUTH"),
    ("BUS_SABINE", "Sabine Bus", "EAST"),
    ("BUS_BRAZOS", "Brazos Valley Bus", "SOUTH"),
]

BOOKS = ["ERCOT_NORTH", "ERCOT_SOUTH", "ERCOT_WEST", "ERCOT_HUB", "ERCOT_CRR"]
FUEL_TYPES = ["wind", "solar", "gas", "coal", "nuclear", "hydro", "other"]

START = datetime(2024, 5, 1)
END = datetime(2024, 8, 1)

# ── Helpers ──────────────────────────────────────────────────────────────────

def hourly_range(start=START, end=END):
    t = start
    while t < end:
        yield t
        t += timedelta(hours=1)

def base_lmp(hour: int, is_summer: bool) -> float:
    """Diurnal price curve."""
    peak = 18 if is_summer else 8
    base = 45 + 20 * math.sin(math.pi * (hour - 5) / 14)
    if is_summer and 14 <= hour <= 19:
        base += 40
    return max(base + random.gauss(0, 8), 5.0)


# ── 1. DA Prices ─────────────────────────────────────────────────────────────

def gen_da_prices():
    rows = []
    for ts in hourly_range():
        is_summer = ts.month in (6, 7)
        for node_id, node_name, zone in NODES:
            lmp = base_lmp(ts.hour, is_summer)
            # Node-specific adjustments
            if node_id == "HB_HOUSTON":
                lmp += 5
            elif node_id == "HB_WEST":
                lmp -= 10 + (15 if is_summer and ts.hour > 22 else 0)
            elif node_id == "BUS_SABINE":
                lmp += random.uniform(-3, 8)

            cong = random.gauss(0, 3)
            loss = lmp * 0.01 * random.uniform(0.5, 1.5)
            energy = lmp - cong - loss

            # Event A: price spike prep (high DA on 2024-06-15 peak hours)
            if ts.date() == date(2024, 6, 15) and 13 <= ts.hour <= 17 and node_id in ("HB_HOUSTON", "LZ_HOUSTON"):
                lmp = 420 + random.uniform(-30, 30)
                cong = 180 + random.uniform(-10, 20)
                energy = lmp - cong - loss

            rows.append({
                "interval_start": ts.isoformat(),
                "interval_end": (ts + timedelta(hours=1)).isoformat(),
                "node_id": node_id,
                "node_name": node_name,
                "zone": zone,
                "lmp": round(lmp, 4),
                "energy_component": round(energy, 4),
                "congestion_component": round(cong, 4),
                "loss_component": round(loss, 4),
            })

    with open(OUT / "market_prices_da.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  ✓ market_prices_da.csv  ({len(rows):,} rows)")


# ── 2. RT Prices (5-min) ──────────────────────────────────────────────────────

def gen_rt_prices():
    rows = []
    # Use 15-min intervals (ERCOT publishes SPPs every 15 min) — enough resolution
    t = START
    while t < END:
        is_summer = t.month in (6, 7)
        for node_id, node_name, zone in NODES:
            lmp = base_lmp(t.hour, is_summer) + random.gauss(0, 15)
            # RT is noisier than DA
            cong = random.gauss(0, 8)
            loss = lmp * 0.01 * random.uniform(0.3, 2.0)
            energy = lmp - cong - loss

            # Event A: RT spike at Houston on 2024-06-15 14:00-16:00
            if t.date() == date(2024, 6, 15) and 14 <= t.hour <= 16 and node_id in ("HB_HOUSTON", "LZ_HOUSTON", "BUS_BRAZOS"):
                lmp = 850 + random.uniform(-50, 100)
                cong = 340 + random.uniform(-20, 40)
                energy = lmp - cong - loss

            # Event B: Negative RT prices in West on 2024-06-22 night (wind glut)
            if t.date() == date(2024, 6, 22) and 1 <= t.hour <= 5 and node_id in ("HB_WEST", "LZ_WEST"):
                lmp = -45 + random.uniform(-30, 10)
                cong = -20 + random.uniform(-5, 5)
                energy = lmp - cong - loss

            rows.append({
                "interval_start": t.isoformat(),
                "interval_end": (t + timedelta(minutes=15)).isoformat(),
                "node_id": node_id,
                "node_name": node_name,
                "zone": zone,
                "lmp": round(lmp, 4),
                "energy_component": round(energy, 4),
                "congestion_component": round(cong, 4),
                "loss_component": round(loss, 4),
            })
        t += timedelta(minutes=15)

    with open(OUT / "market_prices_rt.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  ✓ market_prices_rt.csv  ({len(rows):,} rows)")


# ── 3. Constraints ────────────────────────────────────────────────────────────

CONSTRAINTS = [
    ("SABINE_345", "Sabine-Jasper 345kV", "EAST"),
    ("BRAZOS_HOUSTON", "Brazos Valley to Houston 138kV", "SOUTH"),
    ("TRAVIS_345", "Travis County 345kV", "CENTRAL"),
    ("PANHANDLE_230", "Panhandle Wind Export 230kV", "WEST"),
    ("HAYS_138", "Hays County 138kV", "CENTRAL"),
]

def gen_constraints():
    rows = []
    for ts in hourly_range():
        is_summer = ts.month in (6, 7)
        for cid, cname, region in CONSTRAINTS:
            shadow = random.gauss(0, 5)
            flow = random.uniform(400, 900)
            limit = 1000.0
            is_binding = shadow > 20

            # Event A: Sabine constraint binding during Houston spike
            if ts.date() == date(2024, 6, 15) and 13 <= ts.hour <= 17 and cid == "SABINE_345":
                shadow = 310 + random.uniform(-20, 30)
                flow = 990 + random.uniform(0, 15)
                is_binding = True

            # Event C: Travis constraint on July 4th peak
            if ts.date() == date(2024, 7, 4) and 14 <= ts.hour <= 20 and cid == "TRAVIS_345":
                shadow = 243 + random.uniform(-15, 20)
                flow = 960 + random.uniform(0, 40)
                is_binding = True

            rows.append({
                "interval_start": ts.isoformat(),
                "constraint_id": cid,
                "constraint_name": cname,
                "shadow_price": round(shadow, 4),
                "flow_mw": round(flow, 2),
                "limit_mw": limit,
                "contingency": None,
                "is_binding": is_binding,
            })

    with open(OUT / "constraints.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  ✓ constraints.csv       ({len(rows):,} rows)")


# ── 4. Outages ────────────────────────────────────────────────────────────────

def gen_outages():
    outages = [
        # Event A trigger
        {
            "outage_id": "OUT-2024-0892", "resource_name": "Brazos Valley Unit 3",
            "resource_type": "gen", "capacity_mw": 750.0,
            "outage_start": "2024-06-15T13:22:00", "outage_end": "2024-06-17T08:00:00",
            "reason": "Forced outage — high exhaust temperature alarm",
            "notice_issued_at": "2024-06-15T13:45:00", "status": "restored"
        },
        # Event B trigger
        {
            "outage_id": "OUT-2024-0941", "resource_name": "Panhandle Wind Farm Complex",
            "resource_type": "gen", "capacity_mw": 1200.0,
            "outage_start": "2024-06-21T20:00:00", "outage_end": "2024-06-23T06:00:00",
            "reason": "Curtailment — system-wide oversupply; wind generation exceeds load",
            "notice_issued_at": "2024-06-21T19:30:00", "status": "restored"
        },
        # Background outages
        {
            "outage_id": "OUT-2024-0712", "resource_name": "WA Parish Unit 8",
            "resource_type": "gen", "capacity_mw": 900.0,
            "outage_start": "2024-05-10T06:00:00", "outage_end": "2024-05-20T18:00:00",
            "reason": "Planned maintenance — boiler tube replacement",
            "notice_issued_at": "2024-04-25T08:00:00", "status": "restored"
        },
        {
            "outage_id": "OUT-2024-1021", "resource_name": "Sabine-Jasper 345kV Line",
            "resource_type": "tx", "capacity_mw": 1000.0,
            "outage_start": "2024-06-14T22:00:00", "outage_end": "2024-06-15T20:00:00",
            "reason": "Emergency maintenance — insulator damage detected during patrol",
            "notice_issued_at": "2024-06-14T22:15:00", "status": "restored"
        },
        {
            "outage_id": "OUT-2024-1105", "resource_name": "Travis County 345kV Bus",
            "resource_type": "tx", "capacity_mw": 960.0,
            "outage_start": "2024-07-04T12:00:00", "outage_end": "2024-07-04T23:00:00",
            "reason": "Thermal overload — summer peak demand exceeds N-1 limit",
            "notice_issued_at": "2024-07-04T11:30:00", "status": "restored"
        },
    ]
    with open(OUT / "outages.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=outages[0].keys())
        w.writeheader(); w.writerows(outages)
    print(f"  ✓ outages.csv           ({len(outages)} rows)")


# ── 5. Positions ──────────────────────────────────────────────────────────────

def gen_positions():
    rows = []
    d = date(2024, 5, 1)
    end_date = date(2024, 8, 1)
    while d < end_date:
        for book in BOOKS:
            for node_id, node_name, zone in random.sample(NODES, 4):
                for product in ["DA", "RT", "CRR"]:
                    if random.random() < 0.3:
                        continue
                    qty = random.uniform(-300, 300)
                    avg_p = random.uniform(30, 120)
                    mark_p = avg_p + random.gauss(0, 15)
                    unreal = qty * (mark_p - avg_p)
                    rows.append({
                        "trade_date": d.isoformat(),
                        "book": book,
                        "node_id": node_id,
                        "node_name": node_name,
                        "product": product,
                        "quantity_mw": round(qty, 2),
                        "avg_price": round(avg_p, 4),
                        "mark_price": round(mark_p, 4),
                        "unrealized_pnl": round(unreal, 2),
                        "delta": round(qty * 0.95, 2),
                        "gamma": round(abs(qty) * 0.001, 4),
                        "theta": round(-abs(qty) * 0.005, 4),
                    })
        d += timedelta(days=1)

    with open(OUT / "positions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  ✓ positions.csv         ({len(rows):,} rows)")


# ── 6. Settlements ────────────────────────────────────────────────────────────

def gen_settlements():
    rows = []
    d = date(2024, 5, 1)
    while d < date(2024, 8, 1):
        for book in BOOKS:
            for node_id, _, _ in random.sample(NODES, 3):
                da_q = random.uniform(100, 500)
                rt_q = da_q + random.gauss(0, 50)
                da_p = base_lmp(12, d.month in (6, 7))
                rt_p = da_p + random.gauss(0, 20)
                da_charge = da_q * da_p
                rt_charge = rt_q * rt_p
                net = da_charge - rt_charge

                # Event B: large variance on 2024-06-22 for ERCOT_WEST
                if d == date(2024, 6, 22) and book == "ERCOT_WEST" and node_id in ("HB_WEST", "LZ_WEST"):
                    net = -18500 + random.uniform(-500, 500)
                    rt_charge = da_charge - net

                rows.append({
                    "settlement_date": d.isoformat(),
                    "node_id": node_id,
                    "book": book,
                    "da_charge": round(da_charge, 2),
                    "rt_charge": round(rt_charge, 2),
                    "net_settlement": round(net, 2),
                    "da_quantity_mwh": round(da_q, 2),
                    "rt_quantity_mwh": round(rt_q, 2),
                    "status": "final" if d < date(2024, 7, 15) else "preliminary",
                })
        d += timedelta(days=1)

    with open(OUT / "settlements.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  ✓ settlements.csv       ({len(rows):,} rows)")


# ── 7. Load Forecast ──────────────────────────────────────────────────────────

ZONES = ["NORTH", "SOUTH", "EAST", "WEST", "HOUSTON", "COAST", "FWEST", "NCENT"]

def gen_load_forecast():
    rows = []
    for ts in hourly_range():
        is_summer = ts.month in (6, 7)
        for zone in ZONES:
            base = 4000 + 2000 * math.sin(math.pi * (ts.hour - 5) / 14)
            if is_summer and 14 <= ts.hour <= 19:
                base += 3000
            forecast = base + random.gauss(0, 200)
            actual = forecast + random.gauss(0, 150)
            error = actual - forecast
            rows.append({
                "interval_start": ts.isoformat(),
                "zone": zone,
                "forecast_mw": round(forecast, 1),
                "actual_mw": round(actual, 1) if ts < datetime(2024, 7, 20) else None,
                "forecast_error_mw": round(error, 1) if ts < datetime(2024, 7, 20) else None,
                "forecast_type": "STLF",
                "temperature_f": round(75 + 20 * math.sin(math.pi * ts.hour / 12) + random.gauss(0, 3), 1),
            })

    with open(OUT / "load_forecast.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  ✓ load_forecast.csv     ({len(rows):,} rows)")


# ── 8. Generation Mix ─────────────────────────────────────────────────────────

FUEL_CAPACITY = {"wind": 32000, "solar": 14000, "gas": 60000, "coal": 12000, "nuclear": 5100, "hydro": 600, "other": 2000}

def gen_generation_mix():
    rows = []
    for ts in hourly_range():
        is_summer = ts.month in (6, 7)
        for fuel, cap in FUEL_CAPACITY.items():
            if fuel == "wind":
                cf = 0.35 + 0.2 * math.sin(math.pi * ts.hour / 12) + random.gauss(0, 0.05)
                curt = 0
                # Event B: curtailment on 2024-06-22 night
                if ts.date() == date(2024, 6, 22) and 0 <= ts.hour <= 6:
                    cf = 0.85 + random.gauss(0, 0.02)
                    curt = cap * cf * 0.4
            elif fuel == "solar":
                cf = max(0, math.sin(math.pi * (ts.hour - 6) / 12)) * 0.7 + random.gauss(0, 0.03)
                curt = 0
            elif fuel == "gas":
                cf = 0.55 + (0.25 if is_summer and 14 <= ts.hour <= 19 else 0) + random.gauss(0, 0.05)
                curt = 0
            elif fuel == "nuclear":
                cf = 0.92 + random.gauss(0, 0.01)
                curt = 0
            else:
                cf = 0.4 + random.gauss(0, 0.05)
                curt = 0
            cf = max(0.0, min(1.0, cf))
            gen = cap * cf
            rows.append({
                "interval_start": ts.isoformat(),
                "fuel_type": fuel,
                "generation_mw": round(gen, 1),
                "capacity_mw": cap,
                "capacity_factor": round(cf, 4),
                "curtailment_mw": round(curt, 1),
            })

    with open(OUT / "generation_mix.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  ✓ generation_mix.csv    ({len(rows):,} rows)")


# ── 9. Trade P&L ─────────────────────────────────────────────────────────────

STRATEGIES = ["DA_Arb", "RT_Hedging", "CRR_Portfolio", "Basis_Trade", "Volatility"]

def gen_trade_pnl():
    rows = []
    d = date(2024, 5, 1)
    while d < date(2024, 8, 1):
        for book in BOOKS:
            for strategy in random.sample(STRATEGIES, 3):
                realized = random.gauss(5000, 15000)
                unrealized = random.gauss(2000, 8000)

                # Event A impact: Houston books spike profit on 2024-06-15
                if d == date(2024, 6, 15) and book in ("ERCOT_SOUTH", "ERCOT_HUB"):
                    realized = 180000 + random.uniform(-5000, 5000)

                # Event B impact: West book loss on 2024-06-22
                if d == date(2024, 6, 22) and book == "ERCOT_WEST":
                    realized = -95000 + random.uniform(-5000, 5000)

                rows.append({
                    "trade_date": d.isoformat(),
                    "book": book,
                    "strategy": strategy,
                    "realized_pnl": round(realized, 2),
                    "unrealized_pnl": round(unrealized, 2),
                    "total_pnl": round(realized + unrealized, 2),
                    "volume_mwh": round(abs(random.gauss(50000, 20000)), 1),
                    "fees": round(abs(realized) * 0.001, 2),
                    "notes": None,
                })
        d += timedelta(days=1)

    with open(OUT / "trade_pnl.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  ✓ trade_pnl.csv         ({len(rows):,} rows)")


# ── 10. Node Aliases ──────────────────────────────────────────────────────────

def gen_node_aliases():
    aliases = [
        ("HB_HOUSTON", "HOUSTON_HUB", "market", "ERCOT Settlement", True, None),
        ("HB_HOUSTON", "HST_HUB", "internal", "Trading System", True, None),
        ("HB_NORTH", "LZ_NORTH", "market", "Legacy ERCOT", False, "Deprecated since 2022 nodal settlement"),
        ("HB_NORTH", "NORTH_HUB", "internal", "Risk System", True, None),
        ("HB_WEST", "WEST_HUB", "internal", "Trading System", True, None),
        ("HB_WEST", "WTX_HUB", "doc_reference", "Market Notice MN-2023-441", True, None),
        ("LZ_HOUSTON", "HST_LZ", "internal", "Trading System", True, None),
        ("LZ_HOUSTON", "HOUSTON_LOAD", "doc_reference", "Settlement Protocol v4.2", True, None),
        ("BUS_SABINE", "SABINE_345", "internal", "Constraint Monitor", True, None),
        ("BUS_BRAZOS", "BRAZOS_BUS", "internal", "Trading System", True, None),
        ("BUS_BRAZOS", "BV_BUS_3", "doc_reference", "Outage Report OUT-2024-0892", True, "Maps to Brazos Valley Unit 3 injection bus"),
    ]
    rows = [
        {"canonical_id": a[0], "alias": a[1], "alias_type": a[2], "source": a[3], "is_active": a[4], "notes": a[5]}
        for a in aliases
    ]
    with open(OUT / "node_aliases.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"  ✓ node_aliases.csv      ({len(rows)} rows)")


# ── 11. Congestion Archive ────────────────────────────────────────────────────

def gen_congestion_archive():
    events = [
        {
            "event_start": "2024-06-15T13:00:00", "event_end": "2024-06-15T17:00:00",
            "constraint_id": "SABINE_345",
            "affected_nodes": '["HB_HOUSTON","LZ_HOUSTON","BUS_SABINE","BUS_BRAZOS"]',
            "max_shadow_price": 310.5, "total_congestion_rent": 245000.0,
            "related_outage_id": "OUT-2024-1021",
            "description": "Sabine-Jasper 345kV line emergency outage reduced transfer capacity from East Texas into Houston. Brazos Valley Unit 3 forced outage coincided, reducing local supply. RT prices reached $850/MWh at HB_HOUSTON."
        },
        {
            "event_start": "2024-07-04T14:00:00", "event_end": "2024-07-04T22:00:00",
            "constraint_id": "TRAVIS_345",
            "affected_nodes": '["HB_NORTH","LZ_NORTH","BUS_SABINE"]',
            "max_shadow_price": 243.0, "total_congestion_rent": 88500.0,
            "related_outage_id": "OUT-2024-1105",
            "description": "July 4th summer peak load exceeded N-1 security limit on Travis County 345kV bus. ERCOT deployed emergency response. Shadow price reached $243/MWh for 8 hours."
        },
        {
            "event_start": "2024-05-22T09:00:00", "event_end": "2024-05-22T13:00:00",
            "constraint_id": "PANHANDLE_230",
            "affected_nodes": '["HB_WEST","LZ_WEST"]',
            "max_shadow_price": 87.0, "total_congestion_rent": 24000.0,
            "related_outage_id": None,
            "description": "Wind ramp in Panhandle exceeded 230kV export capability. ERCOT ordered wind curtailment to manage constraint."
        },
    ]
    with open(OUT / "congestion_archive.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=events[0].keys())
        w.writeheader(); w.writerows(events)
    print(f"  ✓ congestion_archive.csv ({len(events)} rows)")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating synthetic ERCOT market data...")
    gen_da_prices()
    gen_rt_prices()
    gen_constraints()
    gen_outages()
    gen_positions()
    gen_settlements()
    gen_load_forecast()
    gen_generation_mix()
    gen_trade_pnl()
    gen_node_aliases()
    gen_congestion_archive()
    print("\n✅ All 11 CSVs generated in /data/")

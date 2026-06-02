"""
Database seeder — loads all synthetic CSVs and market documents into PostgreSQL.

Usage:
    python data/seed.py

Requires:
    - PostgreSQL running with pgvector extension
    - .env file with POSTGRES_* and OPENAI_API_KEY vars set
    - CSVs generated via: python data/synthetic/generate_all.py

This script uses synchronous psycopg2 for bulk loading (much faster than async).
"""
import os
import sys
import csv
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add backend to path (works locally and inside container)
parent_dir = Path(__file__).parent.parent
backend_dir = parent_dir / "backend"
if backend_dir.exists():
    sys.path.insert(0, str(backend_dir))
    env_path = backend_dir / ".env"
else:
    sys.path.insert(0, str(parent_dir))
    env_path = parent_dir / ".env"

from dotenv import load_dotenv
load_dotenv(env_path)

from app.core.database import init_db

DATA_DIR = Path(__file__).parent

DB = {
    "dbname": os.getenv("POSTGRES_DB", "ercot_copilot"),
    "user": os.getenv("POSTGRES_USER", "copilot"),
    "password": os.getenv("POSTGRES_PASSWORD", "copilot_secret"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}


def get_conn():
    import psycopg2

    return psycopg2.connect(**DB)


def load_csv_table(conn, table: str, csv_path: Path, col_types: dict = None):
    """Bulk load CSV into table using COPY."""
    if not csv_path.exists():
        print(f"  ⚠  {csv_path.name} not found — skipping")
        return 0

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return 0

    # Convert types
    if col_types:
        for row in rows:
            for col, typ in col_types.items():
                if col in row and row[col] not in ("", "None", None):
                    try:
                        if typ == "float":
                            row[col] = float(row[col])
                        elif typ == "int":
                            row[col] = int(row[col])
                        elif typ == "bool":
                            row[col] = row[col].lower() in ("true", "1", "yes")
                        elif typ == "json":
                            row[col] = json.loads(row[col]) if row[col] else None
                    except (ValueError, TypeError):
                        row[col] = None
                elif row.get(col) in ("", "None"):
                    row[col] = None

    cols = list(rows[0].keys())
    vals = [[row.get(c) for c in cols] for row in rows]

    from psycopg2.extras import execute_values

    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM {table}")  # clear before reload
        execute_values(
            cur,
            f"INSERT INTO {table} ({','.join(cols)}) VALUES %s ON CONFLICT DO NOTHING",
            vals,
        )
    conn.commit()
    print(f"  ✓ {table:<30} {len(rows):>8,} rows")
    return len(rows)


def load_rows_table(conn, table: str, rows: list[dict], col_types: dict = None):
    """Bulk load already-normalized row dictionaries into a table."""
    if not rows:
        print(f"  ⚠  {table:<30} no rows — skipping")
        return 0

    if col_types:
        coerce_rows(rows, col_types)

    cols = list(rows[0].keys())
    vals = [[row.get(c) for c in cols] for row in rows]

    from psycopg2.extras import execute_values

    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM {table}")
        execute_values(
            cur,
            f"INSERT INTO {table} ({','.join(cols)}) VALUES %s ON CONFLICT DO NOTHING",
            vals,
        )
    conn.commit()
    print(f"  ✓ {table:<30} {len(rows):>8,} rows")
    return len(rows)


def read_csv_rows(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        print(f"  ⚠  {csv_path.name} not found — skipping")
        return []
    with open(csv_path) as f:
        return list(csv.DictReader(f))


def coerce_rows(rows: list[dict], col_types: dict) -> None:
    for row in rows:
        for col, typ in col_types.items():
            if col in row and row[col] not in ("", "None", None):
                try:
                    if typ == "float":
                        row[col] = float(row[col])
                    elif typ == "int":
                        row[col] = int(row[col])
                    elif typ == "bool":
                        row[col] = str(row[col]).lower() in ("true", "1", "yes")
                    elif typ == "json":
                        row[col] = json.loads(row[col]) if row[col] else None
                except (ValueError, TypeError, json.JSONDecodeError):
                    row[col] = None
            elif row.get(col) in ("", "None"):
                row[col] = None


def load_constraints(conn):
    rows = read_csv_rows(DATA_DIR / "constraints.csv")
    if not rows:
        return 0
    if "interval_start" in rows[0]:
        return load_csv_table(conn, "constraints", DATA_DIR / "constraints.csv",
                              col_types={"shadow_price": "float", "flow_mw": "float",
                                          "limit_mw": "float", "is_binding": "bool"})

    normalized = []
    for row in rows:
        normalized.append({
            "interval_start": parse_dt(row.get("date")),
            "constraint_id": row.get("constraint_id"),
            "constraint_name": row.get("constraint_id"),
            "shadow_price": row.get("shadow_price"),
            "flow_mw": row.get("flow_mw"),
            "limit_mw": row.get("limit_mw"),
            "contingency": row.get("cause"),
            "is_binding": True,
        })
    return load_rows_table(conn, "constraints", normalized,
                           col_types={"shadow_price": "float", "flow_mw": "float",
                                      "limit_mw": "float", "is_binding": "bool"})


def load_outages(conn):
    rows = read_csv_rows(DATA_DIR / "outages.csv")
    if not rows:
        return 0
    if "outage_id" in rows[0]:
        return load_csv_table(conn, "outages", DATA_DIR / "outages.csv",
                              col_types={"capacity_mw": "float"})

    normalized = []
    for row in rows:
        unit_id = row.get("unit_id")
        start_time = row.get("start_time")
        normalized.append({
            "outage_id": make_outage_id(unit_id, start_time),
            "resource_name": row.get("unit_name") or unit_id,
            "resource_type": infer_resource_type(unit_id, row.get("unit_name")),
            "capacity_mw": 0.0,
            "outage_start": parse_dt(start_time),
            "outage_end": parse_dt(row.get("end_time")),
            "reason": row.get("status"),
            "notice_issued_at": parse_dt(start_time),
            "status": normalize_outage_status(row.get("status")),
        })
    return load_rows_table(conn, "outages", normalized,
                           col_types={"capacity_mw": "float"})


def load_settlements(conn):
    rows = read_csv_rows(DATA_DIR / "settlements.csv")
    if not rows:
        return 0
    if "node_id" in rows[0]:
        return load_csv_table(conn, "settlements", DATA_DIR / "settlements.csv",
                              col_types={"da_charge": "float", "rt_charge": "float",
                                          "net_settlement": "float", "da_quantity_mwh": "float",
                                          "rt_quantity_mwh": "float"})

    normalized = []
    for row in rows:
        expected = parse_float(row.get("expected"))
        settled = parse_float(row.get("settled"))
        variance = parse_float(row.get("variance"))
        normalized.append({
            "settlement_date": row.get("settlement_date"),
            "node_id": row.get("node"),
            "book": row.get("book"),
            "da_charge": expected,
            "rt_charge": settled,
            "net_settlement": variance if variance is not None else (settled or 0) - (expected or 0),
            "da_quantity_mwh": 0.0,
            "rt_quantity_mwh": 0.0,
            "status": row.get("cause") or "preliminary",
        })
    return load_rows_table(conn, "settlements", normalized,
                           col_types={"da_charge": "float", "rt_charge": "float",
                                      "net_settlement": "float", "da_quantity_mwh": "float",
                                      "rt_quantity_mwh": "float"})


def load_load_forecast(conn):
    rows = read_csv_rows(DATA_DIR / "load_forecast.csv")
    if not rows:
        return 0
    if "interval_start" in rows[0]:
        return load_csv_table(conn, "load_forecast", DATA_DIR / "load_forecast.csv",
                              col_types={"forecast_mw": "float", "actual_mw": "float",
                                          "forecast_error_mw": "float", "temperature_f": "float"})

    normalized = []
    for row in rows:
        forecast = parse_float(row.get("forecasted_load_mw"))
        actual = parse_float(row.get("actual_load_mw"))
        normalized.append({
            "interval_start": parse_dt(row.get("datetime")),
            "zone": "ERCOT",
            "forecast_mw": forecast,
            "actual_mw": actual,
            "forecast_error_mw": None if forecast is None or actual is None else actual - forecast,
            "forecast_type": "STLF",
            "temperature_f": None,
        })
    return load_rows_table(conn, "load_forecast", normalized,
                           col_types={"forecast_mw": "float", "actual_mw": "float",
                                      "forecast_error_mw": "float", "temperature_f": "float"})


def load_generation_mix(conn):
    rows = read_csv_rows(DATA_DIR / "generation_mix.csv")
    if not rows:
        return 0
    if "fuel_type" in rows[0]:
        return load_csv_table(conn, "generation_mix", DATA_DIR / "generation_mix.csv",
                              col_types={"generation_mw": "float", "capacity_mw": "float",
                                          "capacity_factor": "float", "curtailment_mw": "float"})

    fuel_cols = {
        "coal_mw": "coal",
        "gas_mw": "gas",
        "wind_mw": "wind",
        "solar_mw": "solar",
        "nuclear_mw": "nuclear",
    }
    normalized = []
    for row in rows:
        interval_start = parse_dt(row.get("datetime"))
        for csv_col, fuel_type in fuel_cols.items():
            generation = parse_float(row.get(csv_col)) or 0.0
            capacity = generation / 0.85 if generation else 0.0
            normalized.append({
                "interval_start": interval_start,
                "fuel_type": fuel_type,
                "generation_mw": generation,
                "capacity_mw": capacity,
                "capacity_factor": 0.85 if generation else 0.0,
                "curtailment_mw": 0.0,
            })
    return load_rows_table(conn, "generation_mix", normalized,
                           col_types={"generation_mw": "float", "capacity_mw": "float",
                                      "capacity_factor": "float", "curtailment_mw": "float"})


def load_trade_pnl(conn):
    rows = read_csv_rows(DATA_DIR / "trade_pnl.csv")
    if not rows:
        return 0
    if "trade_date" in rows[0]:
        return load_csv_table(conn, "trade_pnl", DATA_DIR / "trade_pnl.csv",
                              col_types={"realized_pnl": "float", "unrealized_pnl": "float",
                                          "total_pnl": "float", "volume_mwh": "float", "fees": "float"})

    normalized = []
    for row in rows:
        pnl = parse_float(row.get("pnl")) or 0.0
        normalized.append({
            "trade_date": row.get("date"),
            "book": row.get("book"),
            "strategy": row.get("trade_type") or "Unknown",
            "realized_pnl": pnl,
            "unrealized_pnl": 0.0,
            "total_pnl": pnl,
            "volume_mwh": 0.0,
            "fees": 0.0,
            "notes": None,
        })
    return load_rows_table(conn, "trade_pnl", normalized,
                           col_types={"realized_pnl": "float", "unrealized_pnl": "float",
                                      "total_pnl": "float", "volume_mwh": "float", "fees": "float"})


def parse_dt(value: str | None):
    if not value:
        return None
    text = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return text


def parse_float(value: str | float | None):
    if value in ("", "None", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def infer_resource_type(unit_id: str | None, unit_name: str | None) -> str:
    text = f"{unit_id or ''} {unit_name or ''}".lower()
    if any(token in text for token in ("line", "345", "138", "tx", "transformer")):
        return "tx"
    return "gen"


def make_outage_id(unit_id: str | None, start_time: str | None) -> str:
    base = (unit_id or "unknown").strip()
    started = (start_time or "unknown").strip().replace(" ", "_").replace(":", "")
    return f"{base}_{started}"


def normalize_outage_status(status: str | None) -> str:
    text = (status or "").lower()
    if "restored" in text or "complete" in text:
        return "restored"
    if "planned" in text:
        return "planned"
    return "active"


def seed_documents(conn):
    """Load synthetic market documents and docs_src markdown documents."""
    sys.path.insert(0, str(DATA_DIR))
    from documents.market_documents import DOCUMENTS
    from markdown_ingestion import (
        ensure_document_chunk_metadata_columns,
        load_markdown_documents,
    )

    ensure_document_chunk_metadata_columns(conn)

    with conn.cursor() as cur:
        cur.execute("DELETE FROM document_chunks")
        cur.execute("DELETE FROM documents")
        conn.commit()

        for doc in DOCUMENTS:
            cur.execute("""
                INSERT INTO documents (title, doc_type, source, effective_date, content, metadata, ingested_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                doc["title"], doc["doc_type"], doc["source"],
                doc.get("effective_date"),
                doc["content"],
                json.dumps(doc.get("metadata", {})),
                datetime.utcnow(),
            ))
            doc_id = cur.fetchone()[0]

            # Simple chunking (no embeddings at seed time — embeddings computed separately)
            text = doc["content"]
            chunk_size = 512
            overlap = 64
            metadata = doc.get("metadata", {}) or {}
            tags = [
                doc["doc_type"],
                *(metadata.get("affects_nodes") or []),
                *(metadata.get("category") if isinstance(metadata.get("category"), list) else [metadata.get("category")] if metadata.get("category") else []),
            ]
            start = 0
            idx = 0
            while start < len(text):
                chunk = text[start:start + chunk_size]
                cur.execute("""
                    INSERT INTO document_chunks
                        (document_id, chunk_index, content, token_count, section, tags, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    doc_id,
                    idx,
                    chunk,
                    len(chunk.split()),
                    doc["title"],
                    json.dumps([tag for tag in tags if tag]),
                    json.dumps({
                        **metadata,
                        "doc_type": doc["doc_type"],
                        "source": doc["source"],
                        "section": doc["title"],
                    }),
                ))
                start += chunk_size - overlap
                idx += 1

        conn.commit()

    docs_dir = parent_dir / "docs_src"
    markdown_docs, markdown_chunks = load_markdown_documents(conn, docs_dir)
    print(
        f"  ✓ documents              {len(DOCUMENTS) + markdown_docs:>8} docs "
        f"| markdown chunks: {markdown_chunks} | embeddings: run embed_documents.py"
    )


def seed_node_aliases(conn):
    """Node alias table from CSV."""
    load_csv_table(conn, "node_aliases", DATA_DIR / "node_aliases.csv",
                   col_types={"is_active": "bool"})


def main():
    print("🌱 Seeding ERCOT Copilot database...\n")
    print("🛠 Creating database tables if they do not exist...")
    asyncio.run(init_db())
    print("✓ Tables verified/created.\n")
    conn = get_conn()

    # Generate CSVs if not present
    if not (DATA_DIR / "market_prices_da.csv").exists():
        print("📊 CSVs not found — generating synthetic data first...")
        os.system(f"cd {DATA_DIR / 'synthetic'} && python generate_all.py")

    print("📥 Loading market data tables:")
    load_csv_table(conn, "market_prices_da", DATA_DIR / "market_prices_da.csv",
                   col_types={"lmp": "float", "energy_component": "float",
                               "congestion_component": "float", "loss_component": "float"})
    load_csv_table(conn, "market_prices_rt", DATA_DIR / "market_prices_rt.csv",
                   col_types={"lmp": "float", "energy_component": "float",
                               "congestion_component": "float", "loss_component": "float"})
    load_constraints(conn)
    load_outages(conn)
    load_csv_table(conn, "positions", DATA_DIR / "positions.csv",
                   col_types={"quantity_mw": "float", "avg_price": "float",
                               "mark_price": "float", "unrealized_pnl": "float",
                               "delta": "float", "gamma": "float", "theta": "float"})
    load_settlements(conn)
    load_load_forecast(conn)
    load_generation_mix(conn)
    load_trade_pnl(conn)
    load_csv_table(conn, "node_aliases", DATA_DIR / "node_aliases.csv",
                   col_types={"is_active": "bool"})
    load_csv_table(conn, "congestion_archive", DATA_DIR / "congestion_archive.csv",
                   col_types={"max_shadow_price": "float", "total_congestion_rent": "float"})

    print("\n📥 Loading supplemental synthetic tables:")
    load_csv_table(conn, "da_lmp", DATA_DIR / "da_lmp.csv",
                   col_types={"da_lmp": "float"})
    load_csv_table(conn, "rt_lmp", DATA_DIR / "rt_lmp.csv",
                   col_types={"da_lmp": "float", "rt_lmp": "float"})
    load_csv_table(conn, "ftr_positions", DATA_DIR / "ftr_positions.csv",
                   col_types={"mw": "float", "price": "float"})
    load_csv_table(conn, "physical_positions", DATA_DIR / "physical_positions.csv",
                   col_types={"mw": "float"})
    load_csv_table(conn, "asset_metadata", DATA_DIR / "asset_metadata.csv")

    print("\n📚 Loading market documents:")
    seed_documents(conn)

    conn.close()
    print("\n✅ Database seeded successfully!")
    print("\n📌 Next step: run 'python data/embed_documents.py' to generate embeddings")
    print("   (requires OPENAI_API_KEY in backend/.env)")


if __name__ == "__main__":
    main()

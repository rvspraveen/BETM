# ⚡ ERCOT Power Market Copilot

AI-Powered Power Market Intelligence & Risk Copilot — Full-stack reference implementation.

## Architecture

```
React + TypeScript (Vite)
    ↕ SSE + REST
FastAPI + LangGraph 6-node workflow
    ↕
PostgreSQL + pgvector (semantic search)
Redis (cache + Celery broker)
```

### LangGraph Workflow

```
User Query
    ↓
[1] classify_intent     — GPT-4o/Claude: doc | analytics | hybrid | uncertainty
    ↓
[2] extract_entities    — nodes, dates, books, keywords
    ↓
   ┌─────────────────────┐
   ↓                     ↓
[3a] retrieve_documents  [3b] run_analytics
   (pgvector RAG)         (SQL/pandas)
   └──────────┬──────────┘
              ↓
[4] synthesize_answer   — streaming token output
              ↓
[5] check_confidence    — escalate if < 0.72
              ↓
            END
```

## Quick Start (Docker — recommended)

```bash
# 1. Clone / unzip the project
cd power-market-copilot

# 2. Configure backend
cp backend/.env.example backend/.env
# Edit backend/.env — add your OPENAI_API_KEY

# 3. Start everything
docker compose up

# Services:
#   Frontend:  http://localhost:3000
#   Backend:   http://localhost:8000
#   API Docs:  http://localhost:8000/docs
#   DB:        localhost:5432

# 4. (Optional) Generate embeddings for document search
docker compose exec backend python /app/data/embed_documents.py
```

## Local Development

### Backend

```bash
cd backend

# 1. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env — set OPENAI_API_KEY, POSTGRES_* vars

# 4. Start PostgreSQL with pgvector (Docker required for pgvector)
docker run -d --name ercot_db \
  -e POSTGRES_USER=copilot \
  -e POSTGRES_PASSWORD=copilot_secret \
  -e POSTGRES_DB=ercot_copilot \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 5. Generate & seed data
cd ../data && python synthetic/generate_all.py && cd ..
python data/seed.py

# 6. (Optional) Generate embeddings
python data/embed_documents.py

# 7. Start API
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Live mode (connects to backend)
npm run dev         # → http://localhost:3000

# Mock mode (no backend needed)
cp .env.mock .env
npm run dev
```

### Run Tests

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest -v
```

## Switching LLM Provider

In `backend/.env`:
```env
# Use GPT-4o (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Switch to Claude 3.5 Sonnet
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

No code changes required — the LLM factory handles both.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Service health + LLM provider |
| POST | `/api/v1/investigate` | SSE investigation stream |
| GET | `/api/v1/documents` | List indexed documents |
| POST | `/api/v1/ingest/documents` | Ingest a document |
| GET | `/api/v1/datasets` | Dataset metadata + row counts |
| POST | `/api/v1/ingest/datasets` | Trigger dataset reload |
| GET | `/api/v1/examples` | Pre-built example queries |
| GET | `/api/v1/reviews` | Human review queue |
| POST | `/api/v1/reviews/{id}/resolve` | Approve or reject a review item |
| GET | `/api/v1/analytics/price-spikes` | Price spike analysis |
| GET | `/api/v1/analytics/da-rt-divergence` | DA/RT divergence |
| GET | `/api/v1/analytics/congestion-exposure` | Congestion by book |
| GET | `/api/v1/analytics/positions` | Current positions |
| GET | `/api/v1/analytics/pnl-summary` | P&L summary |

Full docs at `/docs` (Swagger UI) when the backend is running.

## Synthetic Data

Three embedded events for answerable benchmark queries:

| Event | Date | Description |
|-------|------|-------------|
| **Event A** | 2024-06-15 | RT price spike $850/MWh at HB_HOUSTON — Brazos Valley Unit 3 trip + Sabine 345kV emergency outage |
| **Event B** | 2024-06-22 | West zone negative RT prices — wind oversupply curtailment, -$45/MWh at HB_WEST |
| **Event C** | 2024-07-04 | Travis County 345kV congestion — summer peak, shadow price $243/MWh for 8 hours |

## Project Structure

```
power-market-copilot/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # FastAPI route handlers
│   │   ├── core/              # Config, DB, LLM factory
│   │   ├── graphs/            # LangGraph workflow + nodes
│   │   ├── models/            # SQLAlchemy ORM models (11 tables)
│   │   ├── schemas/           # Pydantic request/response types
│   │   └── services/          # Retriever, analytics, ingestion
│   ├── tests/                 # Unit + integration tests
│   ├── alembic/               # DB migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example           # ← Copy to .env, add your API key
├── frontend/
│   ├── src/
│   │   ├── services/api.ts    # All HTTP calls centralized here
│   │   ├── components/        # React UI components
│   │   └── data/mockData.ts   # Mock stubs (VITE_MOCK_MODE=true)
│   ├── .env                   # VITE_API_URL, VITE_MOCK_MODE
│   └── Dockerfile
├── data/
│   ├── synthetic/generate_all.py  # Generates all 11 CSVs
│   ├── documents/market_documents.py  # 8 synthetic ERCOT docs
│   ├── seed.py                # Loads CSVs + docs into Postgres
│   └── embed_documents.py     # Generates OpenAI embeddings
├── docker-compose.yml
└── README.md
```

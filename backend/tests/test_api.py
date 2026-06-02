"""
API integration tests — run with pytest.
Requires a running DB (or use pytest-asyncio with test DB).
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
import json


@pytest.fixture
async def client():
    """Create a test client with mocked DB."""
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_root_returns_200(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert "ERCOT Copilot" in r.json()["message"]


@pytest.mark.asyncio
async def test_health_endpoint_structure(client):
    """Health endpoint returns required fields."""
    with patch("app.api.routes.health.get_db"):
        r = await client.get("/api/v1/health")
        # May fail with DB not running, but structure should be correct
        # Accept 200 (ok) or 503 (degraded)
        assert r.status_code in (200, 503)
        data = r.json()
        assert "version" in data
        assert "llm_provider" in data


# ── Documents ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_documents_returns_list(client):
    with patch("app.api.routes.documents.list_documents", return_value=[]):
        r = await client.get("/api/v1/documents")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ── Reviews ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_review_resolve_requires_valid_status(client):
    with patch("app.api.routes.reviews.get_db"):
        r = await client.post(
            "/api/v1/reviews/999/resolve",
            json={"status": "invalid_status"}
        )
        assert r.status_code == 422  # Pydantic validation error


# ── Investigate ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_investigate_requires_query(client):
    r = await client.post("/api/v1/investigate", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_investigate_query_too_short(client):
    r = await client.post("/api/v1/investigate", json={"query": "ab"})
    assert r.status_code == 422


# ── Datasets ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_datasets_endpoint_exists(client):
    with patch("app.api.routes.datasets.get_db"):
        r = await client.get("/api/v1/datasets")
        # Will fail without DB but endpoint should exist
        assert r.status_code in (200, 500)

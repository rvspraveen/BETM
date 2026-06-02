"""
Unit tests for LangGraph nodes — mocked LLM calls.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json


def make_state(**kwargs):
    return {
        "query": "What caused the price spike at HB_HOUSTON?",
        "session_id": "test-session",
        "filters": None,
        "intent": None,
        "entities": None,
        "doc_sources": None,
        "analytics_data": None,
        "answer": None,
        "confidence": None,
        "escalate": None,
        "escalation_reason": None,
        "events": [],
        "investigation_id": "test-inv-001",
        "latency_ms": None,
        **kwargs,
    }


@pytest.mark.asyncio
async def test_classify_intent_doc():
    from app.graphs.nodes import classify_intent

    mock_response = MagicMock()
    mock_response.content = json.dumps({"intent": "hybrid", "reasoning": "Requires both doc and data."})

    with patch("app.graphs.nodes.get_llm") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        state = await classify_intent(make_state())

    assert state["intent"] == "hybrid"
    assert any(e["type"] == "status" for e in state["events"])


@pytest.mark.asyncio
async def test_extract_entities():
    from app.graphs.nodes import extract_entities

    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "nodes": ["HB_HOUSTON"],
        "dates": ["2024-06-15"],
        "books": [],
        "fuel_types": [],
        "keywords": ["price spike", "congestion"],
        "date_range": None,
    })

    with patch("app.graphs.nodes.get_llm") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        state = await extract_entities(make_state())

    assert state["entities"]["nodes"] == ["HB_HOUSTON"]
    assert "2024-06-15" in state["entities"]["dates"]


@pytest.mark.asyncio
async def test_classify_intent_fallback_on_error():
    """Should default to 'hybrid' if LLM call fails."""
    from app.graphs.nodes import classify_intent

    with patch("app.graphs.nodes.get_llm") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(side_effect=Exception("API timeout"))
        state = await classify_intent(make_state())

    assert state["intent"] == "hybrid"


@pytest.mark.asyncio
async def test_check_confidence_escalates_low():
    """Should set escalate=True when confidence < 0.72."""
    from app.graphs.nodes import check_confidence

    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "score": 0.55,
        "reason": "Missing key data",
        "should_escalate": True,
    })

    with patch("app.graphs.nodes.get_llm") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        state = await check_confidence(make_state(answer="Some uncertain answer"))

    assert state["escalate"] is True
    assert state["confidence"] == pytest.approx(0.55)


@pytest.mark.asyncio
async def test_check_confidence_no_escalation_high():
    from app.graphs.nodes import check_confidence

    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "score": 0.92,
        "reason": "Strong evidence from two sources",
        "should_escalate": False,
    })

    with patch("app.graphs.nodes.get_llm") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        state = await check_confidence(make_state(answer="Well-grounded answer"))

    assert state["escalate"] is False
    assert state["confidence"] > 0.72

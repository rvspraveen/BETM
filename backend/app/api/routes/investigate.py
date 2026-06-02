"""
POST /api/v1/investigate — Main SSE streaming endpoint.

Each LangGraph node emits status events as it runs.
The synthesizer streams answer tokens live.
Final metadata (sources, confidence, escalation) sent once at the end.
"""
import uuid
import json
import time
import asyncio
import structlog
import traceback
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.investigate import InvestigateRequest
from app.graphs.workflow import get_workflow
from app.graphs.state import GraphState
from app.core.database import get_db
from app.core.config import settings
from app.models.reviews import ReviewItem
from app.models.investigations import InvestigationLog

log = structlog.get_logger()
router = APIRouter()


@router.post("/investigate")
async def investigate(
    request: InvestigateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Stream an investigation response via Server-Sent Events.

    SSE event types:
      status   — LangGraph node progress message
      token    — One token of the streaming answer
      metadata — Final sources, confidence, investigation_id
      error    — Error message
      done     — Stream complete
    """
    investigation_id = str(uuid.uuid4())
    start_ms = time.monotonic()

    async def event_generator() -> AsyncGenerator[dict, None]:
        state: GraphState = {
            "query": request.query,
            "session_id": request.session_id or str(uuid.uuid4()),
            "filters": request.filters,
            "intent": None,
            "entities": None,
            "doc_sources": None,
            "analytics_data": None,
            "visualizations": None,
            "answer": None,
            "confidence": None,
            "escalate": None,
            "escalation_reason": None,
            "events": [],
            "investigation_id": investigation_id,
            "latency_ms": None,
        }

        # Inject DB into node functions at runtime (nodes are plain async funcs)
        from app.graphs import nodes as n
        original_retrieve = n.retrieve_documents
        original_analytics = n.run_analytics

        async def _retrieve_with_db(s):
            return await original_retrieve(s, db=db)

        async def _analytics_with_db(s):
            return await run_analytics_with_db(s, db)

        # We'll stream events as the workflow runs.
        # Run the workflow, yielding state events as they accumulate.
        workflow = get_workflow()

        try:
            # Use ainvoke — after each step, check events queue
            # We use a custom streaming approach: run each node manually
            # so we can yield events between nodes.
            async for event in _stream_workflow(state, db, start_ms):
                yield {"data": json.dumps(event)}
                await asyncio.sleep(0)  # let the event loop breathe

        except Exception as exc:
            log.error(
                "investigate.error",
                error=str(exc),
                traceback=traceback.format_exc(),
                inv_id=investigation_id,
            )
            yield {"data": json.dumps({"type": "error", "content": str(exc)})}
        finally:
            yield {"data": json.dumps({"type": "done"})}

    return EventSourceResponse(event_generator())


async def run_analytics_with_db(state: GraphState, db: AsyncSession) -> GraphState:
    from app.graphs.nodes import run_analytics
    return await run_analytics(state, db=db)


async def _stream_workflow(
    state: GraphState,
    db: AsyncSession,
    start_ms: float,
) -> AsyncGenerator[dict, None]:
    """
    Manually step through each LangGraph node, yielding SSE events between steps.
    This gives us real-time streaming rather than waiting for the full graph.
    """
    from app.graphs import nodes as n

    async def drain_events(s: GraphState):
        """Yield and clear all pending events from state."""
        while s["events"]:
            yield s["events"].pop(0)

    # ── Step 1: Classify Intent ──
    state = await n.classify_intent(state)
    async for ev in drain_events(state):
        yield ev

    # ── Step 2: Extract Entities ──
    state = await n.extract_entities(state)
    async for ev in drain_events(state):
        yield ev

    intent = state.get("intent", "hybrid")

    # ── Step 3a: Retrieve Documents (if needed) ──
    if intent in ("doc", "hybrid", "uncertainty"):
        state = await n.retrieve_documents(state, db=db)
        async for ev in drain_events(state):
            yield ev

    # ── Step 3b: Run Analytics (if needed) ──
    if intent in ("analytics", "hybrid", "uncertainty"):
        state = await n.run_analytics(state, db=db)
        async for ev in drain_events(state):
            yield ev

    # ── Step 4: Synthesize Answer (streaming tokens) ──
    state = await n.synthesize_answer(state)
    async for ev in drain_events(state):
        yield ev

    # ── Step 5: Check Confidence ──
    state = await n.check_confidence(state)
    async for ev in drain_events(state):
        yield ev

    # ── Step 6: Persist + send metadata ──
    from app.services.visualizations import build_visualizations

    latency_ms = int((time.monotonic() - start_ms) * 1000)
    sources = state.get("doc_sources") or []
    visualizations = build_visualizations(state.get("analytics_data"))
    state["visualizations"] = visualizations

    # Save to investigation log
    try:
        log_entry = InvestigationLog(
            investigation_id=state["investigation_id"],
            query_text=state["query"],
            intent=state.get("intent"),
            route=intent,
            answer_text=state.get("answer"),
            confidence=state.get("confidence"),
            sources_used=[s.dict() for s in sources],
            latency_ms=latency_ms,
            escalated=bool(state.get("escalate")),
            llm_provider=settings.LLM_PROVIDER,
        )
        db.add(log_entry)

        # Save to review queue if escalated
        if state.get("escalate"):
            review = ReviewItem(
                investigation_id=state["investigation_id"],
                query_text=state["query"],
                ai_answer=state.get("answer") or "",
                confidence=state.get("confidence") or 0.0,
                escalation_reason=state.get("escalation_reason") or "Low confidence",
                metadata_={
                    "intent": intent,
                    "sources": [s.dict() for s in sources[:3]],
                    "visualizations": visualizations,
                },
            )
            db.add(review)

        await db.commit()
    except Exception as exc:
        log.warning("investigate.persist_failed", error=str(exc))

    # Emit final metadata event
    yield {
        "type": "metadata",
        "investigation_id": state["investigation_id"],
        "sources": [s.dict() for s in sources],
        "confidence": state.get("confidence"),
        "escalated": bool(state.get("escalate")),
        "intent": intent,
        "analytics_data": state.get("analytics_data"),
        "visualizations": visualizations,
        "latency_ms": latency_ms,
    }

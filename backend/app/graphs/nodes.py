"""
LangGraph nodes — each is an async function that receives and returns GraphState.

Node execution order:
  classify_intent → extract_entities → [router] →
    ├─ retrieve_documents   (doc / hybrid)
    ├─ run_analytics        (analytics / hybrid)
  synthesize_answer → check_confidence → END
"""
import json
import re
import structlog
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage

from app.graphs.state import GraphState
from app.core.llm import get_llm
from app.core.config import settings
from app.schemas.investigate import SourceRef

log = structlog.get_logger()


def _emit(state: GraphState, event_type: str, step: str, content: str = None, **extra) -> None:
    """Append an SSE event to the state events queue."""
    event = {"type": event_type, "step": step, "content": content, **extra}
    state["events"].append(event)


# ── Node 1: Classify Intent ──────────────────────────────────────────────────

INTENT_SYSTEM = """You are a query classifier for an energy market intelligence system.
Classify the user's query into exactly ONE of these intents:

- doc        : Question answerable from ISO documents, protocols, notices, settlement guides
- analytics  : Question requiring SQL/numerical analysis of price, position, or P&L data
- hybrid     : Question requiring BOTH document retrieval AND data analysis
- uncertainty: Query where data and documents may conflict, or confidence is inherently low

Respond with ONLY a JSON object:
{"intent": "<one of doc|analytics|hybrid|uncertainty>", "reasoning": "<one sentence>"}
"""


async def classify_intent(state: GraphState) -> GraphState:
    _emit(state, "status", "classifier", "🔍 Classifying your query…")

    try:
        llm = get_llm()
        response = await llm.ainvoke([
            SystemMessage(content=INTENT_SYSTEM),
            HumanMessage(content=state["query"]),
        ])
        raw = response.content.strip()
        # extract JSON even if surrounded by markdown
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        parsed = json.loads(m.group(0)) if m else {}
        intent = parsed.get("intent", "hybrid")
        reasoning = parsed.get("reasoning", "")
    except Exception as exc:
        log.warning("classify_intent.failed", error=str(exc))
        intent, reasoning = "hybrid", "Defaulting to hybrid due to classification error."

    _emit(state, "status", "classifier",
          f"📋 Intent: **{intent}** — {reasoning}")
    state["intent"] = intent
    return state


# ── Node 2: Extract Entities ─────────────────────────────────────────────────

ENTITY_SYSTEM = """Extract structured entities from this energy market query.
Return ONLY a JSON object with these keys (use empty arrays/null when absent):
{
  "nodes": ["HB_HOUSTON", ...],
  "dates": ["2024-06-15", ...],
  "books": ["ERCOT_NORTH", ...],
  "fuel_types": ["wind", "gas", ...],
  "keywords": ["congestion", "spike", ...],
  "date_range": {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"} or null
}"""


async def extract_entities(state: GraphState) -> GraphState:
    _emit(state, "status", "entity_extractor", "🏷️ Extracting entities (nodes, dates, books)…")

    try:
        llm = get_llm()
        response = await llm.ainvoke([
            SystemMessage(content=ENTITY_SYSTEM),
            HumanMessage(content=state["query"]),
        ])
        raw = response.content.strip()
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        entities = json.loads(m.group(0)) if m else {}
    except Exception as exc:
        log.warning("extract_entities.failed", error=str(exc))
        entities = {}

    state["entities"] = entities
    found = []
    if entities.get("nodes"):
        found.append(f"nodes: {', '.join(entities['nodes'][:3])}")
    if entities.get("dates"):
        found.append(f"dates: {', '.join(entities['dates'][:2])}")
    if entities.get("books"):
        found.append(f"books: {', '.join(entities['books'][:2])}")
    summary = "; ".join(found) if found else "no specific entities"
    _emit(state, "status", "entity_extractor", f"🏷️ Found {summary}")
    return state


# ── Node 3: Retrieve Documents ───────────────────────────────────────────────

async def retrieve_documents(state: GraphState, db=None) -> GraphState:
    _emit(state, "status", "retriever", "📚 Searching indexed market documents…")

    if db is None:
        state["doc_sources"] = []
        _emit(state, "status", "retriever", "⚠️ No DB session — skipping document retrieval")
        return state

    from app.services.retriever import retrieve_relevant_chunks, count_indexed_chunks

    total = await count_indexed_chunks(db)
    _emit(state, "status", "retriever", f"📚 Searching {total:,} indexed document chunks…")

    sources = await retrieve_relevant_chunks(state["query"], db)
    state["doc_sources"] = sources

    if sources:
        top = sources[0]
        _emit(state, "status", "retriever",
              f"📄 Found {len(sources)} relevant chunks — top: \"{top.title}\" ({top.relevance_score:.0%} match)")
    else:
        _emit(state, "status", "retriever", "📄 No highly relevant documents found")

    return state


# ── Node 4: Run Analytics ────────────────────────────────────────────────────

async def run_analytics(state: GraphState, db=None) -> GraphState:
    _emit(state, "status", "analytics", "📊 Running quantitative analysis…")

    if db is None:
        state["analytics_data"] = {}
        _emit(state, "status", "analytics", "⚠️ No DB session — skipping analytics")
        return state

    from app.services import analytics as svc
    intent = state.get("intent", "analytics")
    entities = state.get("entities", {}) or {}
    query_lower = state["query"].lower()
    results: dict[str, Any] = {}

    try:
        # Route to the right analytics functions based on intent + keywords
        if any(k in query_lower for k in ["spike", "high price", "price surge", "lmp"]):
            results["price_spikes"] = await svc.get_price_spikes(db)

        if any(k in query_lower for k in ["divergen", "da rt", "da/rt", "convergence", "basis"]):
            node = (entities.get("nodes") or [None])[0]
            results["da_rt_divergence"] = await svc.get_da_rt_divergence(db, node_id=node)

        if any(k in query_lower for k in ["congestion", "constraint", "binding", "shadow"]):
            book = (entities.get("books") or [None])[0]
            results["congestion_exposure"] = await svc.get_congestion_exposure(db, book=book)

        if any(k in query_lower for k in ["settlement", "settle", "charge"]):
            book = (entities.get("books") or [None])[0]
            results["settlement_variance"] = await svc.get_settlement_variance(db, book=book)

        if any(k in query_lower for k in ["load", "forecast", "demand"]):
            zone = (entities.get("nodes") or [None])[0]
            results["load_forecast"] = await svc.get_load_forecast_accuracy(db, zone=zone)

        if any(k in query_lower for k in ["generation", "fuel", "wind", "solar", "gas", "mix"]):
            results["generation_mix"] = await svc.get_generation_mix_summary(db)

        if any(k in query_lower for k in ["pnl", "p&l", "profit", "loss", "book"]):
            book = (entities.get("books") or [None])[0]
            results["pnl_summary"] = await svc.get_pnl_summary(db, book=book)

        # Always-run fallback if nothing matched
        if not results:
            results["price_spikes"] = await svc.get_price_spikes(db)
            results["da_rt_divergence"] = await svc.get_da_rt_divergence(db)

    except Exception as exc:
        log.warning("run_analytics.failed", error=str(exc))
        results["error"] = str(exc)

    state["analytics_data"] = results
    result_types = ", ".join(results.keys())
    _emit(state, "status", "analytics",
          f"📊 Computed: {result_types}")
    return state


# ── Node 5: Synthesize Answer ────────────────────────────────────────────────

SYNTHESIS_SYSTEM = """You are an expert energy market analyst and AI copilot for ERCOT traders.

Your job: write a clear, grounded, actionable answer to the trader's question.

Rules:
1. Ground every claim in the provided context (docs + data). Never hallucinate.
2. Cite documents by title when referencing them: e.g. [ERCOT Market Notice 2024-001]
3. Use specific numbers from the data when available.
4. Structure your answer: Brief summary → Key findings → Implications → Recommendations
5. If data is ambiguous or conflicting, say so explicitly.
6. Keep your tone professional but direct — traders want facts, not fluff.
7. End with a confidence assessment (High/Medium/Low) and brief reason.
"""


async def synthesize_answer(state: GraphState) -> GraphState:
    _emit(state, "status", "synthesizer", "✍️ Synthesizing answer with LLM…")

    # Build context string
    context_parts = []

    if state.get("doc_sources"):
        doc_ctx = "\n\n".join(
            f"[{s.title}]\n{s.excerpt}"
            for s in state["doc_sources"][:5]
        )
        context_parts.append(f"## Relevant Documents\n{doc_ctx}")

    if state.get("analytics_data"):
        analytics_ctx = json.dumps(state["analytics_data"], indent=2, default=str)
        context_parts.append(f"## Quantitative Data\n```json\n{analytics_ctx}\n```")

    context = "\n\n".join(context_parts) if context_parts else "No specific context retrieved."

    user_msg = f"""Query: {state['query']}

Context:
{context}

Please provide a comprehensive answer following the system instructions."""

    try:
        llm = get_llm()
        full_answer = ""
        async for chunk in llm.astream([
            SystemMessage(content=SYNTHESIS_SYSTEM),
            HumanMessage(content=user_msg),
        ]):
            token = chunk.content
            full_answer += token
            state["events"].append({"type": "token", "content": token})

        state["answer"] = full_answer
    except Exception as exc:
        import traceback
        log.error("synthesize_answer.failed", error=str(exc), traceback=traceback.format_exc())
        state["answer"] = f"I encountered an error generating the answer: {exc}"
        state["events"].append({"type": "token", "content": state["answer"]})

    return state


# ── Node 6: Check Confidence & Escalate ─────────────────────────────────────

CONFIDENCE_SYSTEM = """Assess the confidence of the answer below.
Respond with ONLY JSON:
{"score": 0.0-1.0, "reason": "<brief>", "should_escalate": true/false}

Escalate if: score < 0.72, conflicting info, missing critical data, or answer is speculative.
"""


async def check_confidence(state: GraphState) -> GraphState:
    _emit(state, "status", "confidence_check", "🎯 Assessing answer confidence…")

    try:
        llm = get_llm()
        response = await llm.ainvoke([
            SystemMessage(content=CONFIDENCE_SYSTEM),
            HumanMessage(content=f"Query: {state['query']}\n\nAnswer: {state.get('answer', '')}"),
        ])
        raw = response.content.strip()
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        parsed = json.loads(m.group(0)) if m else {}
        score = float(parsed.get("score", 0.8))
        reason = parsed.get("reason", "")
        escalate = bool(parsed.get("should_escalate", score < settings.CONFIDENCE_THRESHOLD))
    except Exception as exc:
        log.warning("check_confidence.failed", error=str(exc))
        score, reason, escalate = 0.75, "Confidence check unavailable", False

    state["confidence"] = score
    state["escalate"] = escalate
    state["escalation_reason"] = reason if escalate else None

    if escalate:
        _emit(state, "status", "confidence_check",
              f"⚠️ Confidence {score:.0%} — routing to human review ({reason})")
    else:
        _emit(state, "status", "confidence_check",
              f"✅ Confidence {score:.0%} — answer verified")

    return state

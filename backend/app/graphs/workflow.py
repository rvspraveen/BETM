"""
LangGraph workflow definition.
Builds the compiled StateGraph once at import time.
"""
from langgraph.graph import StateGraph, END

from app.graphs.state import GraphState
from app.graphs.nodes import (
    classify_intent,
    extract_entities,
    retrieve_documents,
    run_analytics,
    synthesize_answer,
    check_confidence,
)


def _route_by_intent(state: GraphState) -> list[str]:
    """
    Conditional edge: after classification+entity-extraction, decide which
    retrieval branches to run in parallel.
    """
    intent = state.get("intent", "hybrid")
    if intent == "doc":
        return ["retrieve_documents"]
    elif intent == "analytics":
        return ["run_analytics"]
    else:
        # hybrid, uncertainty — run both branches
        return ["retrieve_documents", "run_analytics"]


def build_workflow() -> StateGraph:
    g = StateGraph(GraphState)

    # Add nodes
    g.add_node("classify_intent", classify_intent)
    g.add_node("extract_entities", extract_entities)
    g.add_node("retrieve_documents", retrieve_documents)
    g.add_node("run_analytics", run_analytics)
    g.add_node("synthesize_answer", synthesize_answer)
    g.add_node("check_confidence", check_confidence)

    # Sequential start
    g.set_entry_point("classify_intent")
    g.add_edge("classify_intent", "extract_entities")

    # Conditional fan-out after entity extraction
    g.add_conditional_edges(
        "extract_entities",
        _route_by_intent,
        {
            "retrieve_documents": "retrieve_documents",
            "run_analytics": "run_analytics",
        }
    )

    # Both branches converge into synthesis
    g.add_edge("retrieve_documents", "synthesize_answer")
    g.add_edge("run_analytics", "synthesize_answer")

    # Confidence check → END
    g.add_edge("synthesize_answer", "check_confidence")
    g.add_edge("check_confidence", END)

    return g


# Compile once at module load — expensive, cached
_workflow = None


def get_workflow():
    global _workflow
    if _workflow is None:
        _workflow = build_workflow().compile()
    return _workflow

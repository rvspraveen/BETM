"""
LangGraph state definition — the shared object passed between all nodes.
"""
from typing import TypedDict, Optional, Any
from app.schemas.investigate import SourceRef


class GraphState(TypedDict):
    # Input
    query: str
    session_id: str
    filters: Optional[dict[str, Any]]

    # Classification
    intent: Optional[str]        # doc | analytics | hybrid | uncertainty
    entities: Optional[dict]     # {nodes, dates, books, keywords}

    # Retrieval results
    doc_sources: Optional[list[SourceRef]]
    analytics_data: Optional[dict[str, Any]]
    visualizations: Optional[list[dict[str, Any]]]

    # Output
    answer: Optional[str]
    confidence: Optional[float]
    escalate: Optional[bool]
    escalation_reason: Optional[str]

    # Streaming events queue (populated by nodes, drained by SSE handler)
    events: list[dict]           # list of SSEEvent-like dicts

    # Metadata
    investigation_id: str
    latency_ms: Optional[int]

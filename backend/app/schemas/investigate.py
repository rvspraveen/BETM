"""Pydantic schemas for the /investigate endpoint (SSE streaming)."""
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field
import uuid


class InvestigateRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000, description="User query text")
    session_id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Optional session ID for conversation continuity"
    )
    filters: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional filters e.g. {date_from, date_to, nodes, books}"
    )


class SourceRef(BaseModel):
    """A document or data chunk cited in the answer."""
    id: str
    title: str
    source_type: Literal["document", "market_data", "calculation"]
    relevance_score: float = 0.0
    excerpt: Optional[str] = None
    date: Optional[str] = None


class VisualizationSeries(BaseModel):
    key: str
    label: str
    color: Optional[str] = None


class VisualizationColumn(BaseModel):
    key: str
    label: str


class VisualizationMetric(BaseModel):
    label: str
    value: str
    detail: Optional[str] = None
    tone: Optional[Literal["neutral", "success", "warning", "error"]] = None


class VisualizationSpec(BaseModel):
    """UI-ready chart/table/card JSON emitted with investigation metadata."""
    id: str
    type: Literal["kpi", "bar", "line", "pie", "table"]
    title: str
    description: Optional[str] = None
    data: Optional[list[dict[str, Any]]] = None
    xKey: Optional[str] = None
    unit: Optional[str] = None
    yKeys: Optional[list[VisualizationSeries]] = None
    columns: Optional[list[VisualizationColumn]] = None
    metrics: Optional[list[VisualizationMetric]] = None


class SSEEvent(BaseModel):
    """
    Single Server-Sent Event payload.
    Types:
      status   — LangGraph node progress (e.g. "Classifying intent…")
      token    — One streaming token of the final answer
      metadata — Sources, confidence, investigation_id (sent once at end)
      error    — Error message
      done     — Stream complete sentinel
    """
    type: Literal["status", "token", "metadata", "error", "done"]
    step: Optional[str] = None        # LangGraph node name for 'status' events
    content: Optional[str] = None     # Text for 'status' and 'token' events
    sources: Optional[list[SourceRef]] = None
    confidence: Optional[float] = None
    investigation_id: Optional[str] = None
    escalated: Optional[bool] = None
    intent: Optional[str] = None
    analytics_data: Optional[dict[str, Any]] = None
    visualizations: Optional[list[VisualizationSpec]] = None

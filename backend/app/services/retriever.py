"""
Vector retrieval service — semantic search over document chunks using pgvector.
"""
import json
import re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.models.documents import DocumentChunk, Document
from app.schemas.investigate import SourceRef
from app.core.config import settings
from app.core.llm import get_embeddings

log = structlog.get_logger()


async def retrieve_relevant_chunks(
    query: str,
    db: AsyncSession,
    k: int = None,
    doc_type_filter: str = None,
) -> list[SourceRef]:
    """
    Embed the query and return the top-k most similar document chunks.

    Args:
        query: User query string
        db: Async SQLAlchemy session
        k: Number of results (defaults to settings.MAX_RETRIEVAL_CHUNKS)
        doc_type_filter: Optional filter on document type

    Returns:
        List of SourceRef objects with excerpts and relevance scores
    """
    if k is None:
        k = settings.MAX_RETRIEVAL_CHUNKS

    try:
        embeddings = get_embeddings()
        query_vector = await _embed_text(query, embeddings)
    except Exception as exc:
        log.warning("retriever.embed_failed", error=str(exc))
        return []

    candidate_k = max(k * 6, 30)
    query_tags = _extract_query_tags(query)
    query_terms = _query_terms(query)

    # pgvector cosine distance query with optional doc_type filter.
    # Retrieve a wider candidate set, then rerank with metadata signals.
    if doc_type_filter:
        stmt = text("""
            SELECT
                dc.id,
                dc.content,
                dc.section,
                dc.tags,
                dc.metadata AS chunk_metadata,
                dc.document_id,
                d.title,
                d.doc_type,
                d.source,
                d.effective_date,
                d.metadata AS doc_metadata,
                1 - (dc.embedding <=> CAST(:qvec AS vector)) AS similarity
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE dc.embedding IS NOT NULL
              AND d.doc_type = :dtype
            ORDER BY dc.embedding <=> CAST(:qvec AS vector)
            LIMIT :candidate_k
        """)
        result = await db.execute(
            stmt,
            {"qvec": str(query_vector), "dtype": doc_type_filter, "candidate_k": candidate_k}
        )
    else:
        stmt = text("""
            SELECT
                dc.id,
                dc.content,
                dc.section,
                dc.tags,
                dc.metadata AS chunk_metadata,
                dc.document_id,
                d.title,
                d.doc_type,
                d.source,
                d.effective_date,
                d.metadata AS doc_metadata,
                1 - (dc.embedding <=> CAST(:qvec AS vector)) AS similarity
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE dc.embedding IS NOT NULL
            ORDER BY dc.embedding <=> CAST(:qvec AS vector)
            LIMIT :candidate_k
        """)
        result = await db.execute(stmt, {"qvec": str(query_vector), "candidate_k": candidate_k})

    rows = result.fetchall()
    ranked_rows = sorted(
        (_score_row(row, query_tags, query_terms) for row in rows),
        key=lambda item: item["score"],
        reverse=True,
    )[:k]

    sources = []
    for item in ranked_rows:
        row = item["row"]
        tags = _coerce_tags(row.tags)
        section = row.section or _coerce_metadata(row.chunk_metadata).get("section")
        title = _format_source_title(row.title, section)
        excerpt = _format_excerpt(row.content, section, tags)
        sources.append(SourceRef(
            id=str(row.id),
            title=title,
            source_type="document",
            relevance_score=round(float(item["score"]), 4),
            excerpt=excerpt,
            date=row.effective_date.isoformat() if row.effective_date else None,
        ))

    log.info("retriever.results", query=query[:60], k=len(sources))
    return sources


async def _embed_text(text: str, embeddings) -> list[float]:
    """Async wrapper around OpenAI embeddings (synchronous SDK)."""
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, embeddings.embed_query, text)
    return result


def _score_row(row, query_tags: set[str], query_terms: set[str]) -> dict:
    similarity = float(row.similarity or 0.0)
    row_tags = {tag.lower() for tag in _coerce_tags(row.tags)}
    row_metadata = _coerce_metadata(row.chunk_metadata)
    section = str(row.section or row_metadata.get("section") or "").lower()
    content = str(row.content or "").lower()

    tag_matches = query_tags & row_tags
    tag_boost = min(0.12, 0.04 * len(tag_matches))

    keyword_hits = sum(
        1 for term in query_terms
        if term in content or term in section or term in row_tags
    )
    keyword_boost = min(0.10, 0.015 * keyword_hits)
    recency_boost = _recency_boost(row.effective_date)

    return {
        "row": row,
        "score": min(1.0, similarity + tag_boost + keyword_boost + recency_boost),
    }


def _extract_query_tags(query: str) -> set[str]:
    query_lower = query.lower()
    tags = set(_query_terms(query))

    concept_map = {
        "congestion": ["congestion", "constraint", "binding", "shadow"],
        "da_rt": ["da/rt", "day-ahead", "real-time", "divergence"],
        "exposure": ["exposure", "position", "book", "asset"],
        "outage": ["outage", "forced outage", "transmission outage"],
        "price_spike": ["spike", "price event", "high price"],
        "settlement": ["settlement", "uplift", "variance"],
    }
    for tag, needles in concept_map.items():
        if any(needle in query_lower for needle in needles):
            tags.add(tag)

    for pattern in [
        r"\b(?:HB|LZ)_[A-Z0-9_]+\b",
        r"\b[A-Z]{2,}_[A-Z0-9_]+\b",
        r"\b(?:MN|OB|INC|OUT)-\d{4}-\d{3,4}\b",
    ]:
        tags.update(match.lower() for match in re.findall(pattern, query, flags=re.IGNORECASE))

    return tags


def _query_terms(query: str) -> set[str]:
    stop = {
        "about", "after", "also", "and", "any", "are", "did", "does", "for",
        "from", "how", "into", "most", "the", "this", "that", "what", "when",
        "which", "with", "using", "was", "were", "why",
    }
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_/-]{3,}", query)
        if token.lower() not in stop
    }


def _coerce_tags(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if item]
        except json.JSONDecodeError:
            return [tag.strip() for tag in value.split(",") if tag.strip()]
    return []


def _coerce_metadata(value) -> dict:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _recency_boost(effective_date) -> float:
    if not effective_date:
        return 0.0
    if isinstance(effective_date, str):
        try:
            effective_date = datetime.fromisoformat(effective_date)
        except ValueError:
            return 0.0
    age_days = max(0, (datetime.utcnow() - effective_date.replace(tzinfo=None)).days)
    if age_days <= 180:
        return 0.04
    if age_days <= 365:
        return 0.03
    if age_days <= 730:
        return 0.02
    return 0.01


def _format_source_title(title: str, section: str | None) -> str:
    if not section or section.lower() in title.lower():
        return title
    return f"{title} - {section}"


def _format_excerpt(content: str, section: str | None, tags: list[str]) -> str:
    prefix_parts = []
    if section:
        prefix_parts.append(f"Section: {section}")
    if tags:
        prefix_parts.append(f"Tags: {', '.join(tags[:8])}")
    prefix = " | ".join(prefix_parts)
    body = content[:420] + "..." if len(content) > 420 else content
    return f"{prefix}\n{body}" if prefix else body


async def count_indexed_chunks(db: AsyncSession) -> int:
    result = await db.execute(
        text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
    )
    return result.scalar() or 0

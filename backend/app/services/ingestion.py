"""
Document ingestion service — chunk, embed, and store market documents.
"""
import asyncio
from typing import Optional
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.documents import Document, DocumentChunk
from app.schemas.documents import DocumentIn
from app.core.config import settings
from app.core.llm import get_embeddings

log = structlog.get_logger()


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Simple character-based chunking with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


async def ingest_document(doc_in: DocumentIn, db: AsyncSession) -> Document:
    """
    Full pipeline: store document → chunk → embed → save chunks.
    Returns the created Document ORM object.
    """
    # Store document
    doc = Document(
        title=doc_in.title,
        doc_type=doc_in.doc_type,
        source=doc_in.source,
        effective_date=doc_in.effective_date,
        content=doc_in.content,
        metadata_=doc_in.metadata,
    )
    db.add(doc)
    await db.flush()  # get doc.id without committing
    log.info("ingestion.doc_created", doc_id=doc.id, title=doc.title)

    # Chunk
    raw_chunks = _chunk_text(
        doc_in.content,
        settings.CHUNK_SIZE,
        settings.CHUNK_OVERLAP,
    )

    # Embed (batch call)
    embeddings_client = get_embeddings()
    try:
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(
            None, embeddings_client.embed_documents, raw_chunks
        )
    except Exception as exc:
        log.warning("ingestion.embed_failed", error=str(exc))
        vectors = [None] * len(raw_chunks)

    # Save chunks
    for idx, (chunk_text, vector) in enumerate(zip(raw_chunks, vectors)):
        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=idx,
            content=chunk_text,
            embedding=vector,
            token_count=len(chunk_text.split()),
        )
        db.add(chunk)

    await db.commit()
    await db.refresh(doc)
    log.info("ingestion.complete", doc_id=doc.id, chunks=len(raw_chunks))
    return doc


async def list_documents(db: AsyncSession) -> list[Document]:
    result = await db.execute(select(Document).order_by(Document.ingested_at.desc()))
    return result.scalars().all()

"""Document ingestion and listing endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.documents import Document, DocumentChunk
from app.schemas.documents import DocumentIn, DocumentOut
from app.services.ingestion import ingest_document, list_documents

router = APIRouter()


@router.get("/documents", response_model=list[DocumentOut])
async def get_documents(db: AsyncSession = Depends(get_db)):
    """List all ingested documents with chunk counts."""
    docs = await list_documents(db)
    result = []
    for doc in docs:
        count_res = await db.execute(
            select(func.count()).where(DocumentChunk.document_id == doc.id)
        )
        chunk_count = count_res.scalar() or 0
        result.append(DocumentOut(
            id=doc.id,
            title=doc.title,
            doc_type=doc.doc_type,
            source=doc.source,
            effective_date=doc.effective_date,
            ingested_at=doc.ingested_at,
            chunk_count=chunk_count,
        ))
    return result


@router.post("/ingest/documents", response_model=DocumentOut, status_code=201)
async def ingest_document_endpoint(
    doc_in: DocumentIn,
    db: AsyncSession = Depends(get_db),
):
    """Ingest a single document — chunks, embeds, and indexes it."""
    doc = await ingest_document(doc_in, db)
    count_res = await db.execute(
        select(func.count()).where(DocumentChunk.document_id == doc.id)
    )
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        doc_type=doc.doc_type,
        source=doc.source,
        effective_date=doc.effective_date,
        ingested_at=doc.ingested_at,
        chunk_count=count_res.scalar() or 0,
    )


@router.post("/ingest/documents/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: str = Form(...),
    source: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a raw text/markdown file and ingest it."""
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    doc_in = DocumentIn(title=title, doc_type=doc_type, source=source, content=text)
    doc = await ingest_document(doc_in, db)
    return {"id": doc.id, "title": doc.title, "message": "Ingested successfully"}

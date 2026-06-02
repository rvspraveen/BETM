"""
Markdown document ingestion helpers for docs_src/*.md.

Splits markdown by heading structure, refines oversized sections into
token-sized chunks, and stores rich per-chunk metadata for hybrid retrieval.
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


HEADERS_TO_SPLIT_ON = [
    ("#", "title"),
    ("##", "section"),
    ("###", "subsection"),
    ("####", "detail"),
]

CONCEPT_TAGS = {
    "auction": ["auction", "crr auction"],
    "basis": ["basis", "spread"],
    "congestion": ["congestion", "binding congestion", "congestion rent"],
    "constraint": ["constraint", "binding", "shadow price"],
    "curtailment": ["curtailment", "curtail"],
    "da_rt": ["da/rt", "day-ahead", "real-time", "divergence"],
    "exposure": ["exposure", "position", "positions", "risk"],
    "ftr": ["ftr", "crr", "congestion revenue rights"],
    "lmp": ["lmp", "settlement point price", "spp"],
    "manual_change": ["manual change", "manual override", "manual"],
    "outage": ["outage", "forced outage", "transmission outage"],
    "price_spike": ["price spike", "spiked", "high price", "scarcity"],
    "settlement": ["settlement", "resettlement", "invoice"],
    "uplift": ["uplift", "make-whole", "make whole"],
    "volatility": ["volatility", "volatility-adjusted", "var"],
}

DATE_PATTERNS = [
    "%B %d, %Y",
    "%b %d, %Y",
    "%B %Y",
    "%b %Y",
    "%Y-%m-%d",
]


def ensure_document_chunk_metadata_columns(conn) -> None:
    """Make metadata columns available for existing databases."""
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS section VARCHAR(512)")
        cur.execute("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS tags JSON")
        cur.execute("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS metadata JSON")
    conn.commit()


def load_markdown_documents(conn, docs_dir: Path) -> tuple[int, int]:
    """Load all markdown files in docs_dir into documents + document_chunks."""
    ensure_document_chunk_metadata_columns(conn)

    if not docs_dir.exists():
        print(f"  - docs_src not found at {docs_dir}; skipping markdown docs")
        return 0, 0

    files = sorted(docs_dir.glob("*.md"))
    if not files:
        print(f"  - no markdown files found in {docs_dir}; skipping")
        return 0, 0

    doc_count = 0
    chunk_count = 0
    for path in files:
        markdown = path.read_text(encoding="utf-8")
        doc_meta = infer_document_metadata(path, markdown)
        chunks = split_markdown(markdown, doc_meta)

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documents (title, doc_type, source, effective_date, content, metadata, ingested_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                doc_meta["title"],
                doc_meta["doc_type"],
                doc_meta["source"],
                doc_meta.get("date"),
                markdown,
                json.dumps(doc_meta, default=str),
                datetime.utcnow(),
            ))
            doc_id = cur.fetchone()[0]

            for idx, chunk in enumerate(chunks):
                cur.execute("""
                    INSERT INTO document_chunks
                        (document_id, chunk_index, content, token_count, section, tags, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    doc_id,
                    idx,
                    chunk["content"],
                    chunk["token_count"],
                    chunk["section"],
                    json.dumps(chunk["tags"], default=str),
                    json.dumps(chunk["metadata"], default=str),
                ))

        conn.commit()
        doc_count += 1
        chunk_count += len(chunks)
        print(f"  - {path.name:<42} {len(chunks):>3} chunks")

    return doc_count, chunk_count


def split_markdown(markdown: str, doc_meta: dict[str, Any]) -> list[dict[str, Any]]:
    """Split markdown by headings, then refine oversized sections by token count."""
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=False,
    )
    token_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        length_function=count_tokens,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    sections = header_splitter.split_text(markdown)
    chunks: list[dict[str, Any]] = []

    for section_doc in sections:
        section_text = section_doc.page_content.strip()
        if not section_text:
            continue

        section_meta = dict(section_doc.metadata)
        section_name = format_section(section_meta, doc_meta["title"])
        section_tags = merge_tags(
            doc_meta["tags"],
            infer_tags(section_text),
            [section_name],
        )

        split_docs = token_splitter.create_documents(
            [section_text],
            metadatas=[section_meta],
        )
        for split_doc in split_docs:
            content = split_doc.page_content.strip()
            if not content:
                continue
            tags = merge_tags(section_tags, infer_tags(content))
            chunks.append({
                "content": content,
                "token_count": count_tokens(content),
                "section": section_name,
                "tags": tags,
                "metadata": {
                    **doc_meta,
                    "section": section_name,
                    "headers": section_meta,
                    "tags": tags,
                },
            })

    return coalesce_small_chunks(chunks)


def infer_document_metadata(path: Path, markdown: str) -> dict[str, Any]:
    title = infer_title(path, markdown)
    doc_type = infer_doc_type(path, markdown)
    date_value = infer_date(markdown)
    tags = merge_tags([doc_type], infer_tags(markdown), [path.stem])

    return {
        "title": title,
        "doc_type": doc_type,
        "date": date_value,
        "source": f"docs_src/{path.name}",
        "tags": tags,
    }


def infer_title(path: Path, markdown: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, flags=re.MULTILINE)
    return match.group(1).strip() if match else path.stem.replace("_", " ").title()


def infer_doc_type(path: Path, markdown: str) -> str:
    text = f"{path.name}\n{markdown[:1200]}".lower()
    if "market_notice" in text or "market notice" in text or re.search(r"\bmn-\d{4}-\d+", text):
        return "market_notice"
    if "outage_bulletin" in text or "outage bulletin" in text or re.search(r"\bob-\d{4}-\d+", text):
        return "outage_bulletin"
    if "postmortem" in text or "incident" in text:
        return "postmortem"
    return "protocol"


def infer_date(markdown: str) -> datetime | None:
    label_pattern = (
        r"(?:Effective Date|Effective|Date Issued|Issued|Date of Incident|"
        r"Postmortem Completed|Last Updated|Last Revised)\s*:\s*([^|\n]+)"
    )
    for match in re.finditer(label_pattern, markdown, flags=re.IGNORECASE):
        parsed = parse_date(match.group(1).strip())
        if parsed:
            return parsed
    return None


def parse_date(value: str) -> datetime | None:
    clean = re.sub(r"\s+", " ", value.strip())
    clean = re.sub(r"\s*\|.*$", "", clean)
    for pattern in DATE_PATTERNS:
        try:
            parsed = datetime.strptime(clean, pattern)
            return parsed
        except ValueError:
            continue
    return None


def infer_tags(text: str) -> list[str]:
    lower = text.lower()
    tags: list[str] = []

    for tag, needles in CONCEPT_TAGS.items():
        if any(needle in lower for needle in needles):
            tags.append(tag)

    entity_patterns = [
        r"\b(?:HB|LZ)_[A-Z0-9_]+\b",
        r"\b[A-Z]{2,}_[A-Z0-9_]+\b",
        r"\b(?:MN|OB|INC|OUT)-\d{4}-\d{3,4}\b",
        r"\b[A-Z]{2,}-\d{2}\b",
        r"\b[A-Z]{3,}(?:-[A-Z0-9]+)+\b",
    ]
    for pattern in entity_patterns:
        tags.extend(re.findall(pattern, text))

    return normalize_tags(tags)


def merge_tags(*tag_groups: Any) -> list[str]:
    tags: list[str] = []
    for group in tag_groups:
        if not group:
            continue
        if isinstance(group, str):
            tags.append(group)
        else:
            tags.extend(str(tag) for tag in group if tag)
    return normalize_tags(tags)


def normalize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for tag in tags:
        clean = tag.strip().strip(".,;:()[]{}").replace(" ", "_")
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(clean)
    return normalized[:40]


def format_section(metadata: dict[str, str], fallback: str) -> str:
    parts = [
        metadata.get("section"),
        metadata.get("subsection"),
        metadata.get("detail"),
    ]
    section = " > ".join(part.strip() for part in parts if part)
    return section or metadata.get("title") or fallback


def count_tokens(text: str) -> int:
    # Local approximation avoids tiktoken network/cache dependency during startup.
    return max(1, len(re.findall(r"\w+|[^\w\s]", text)))


def coalesce_small_chunks(
    chunks: list[dict[str, Any]],
    min_tokens: int = 380,
    max_tokens: int = 800,
) -> list[dict[str, Any]]:
    """Merge adjacent small chunks while preserving document order."""
    merged: list[dict[str, Any]] = []
    pending: dict[str, Any] | None = None

    for chunk in chunks:
        if pending is None:
            pending = chunk
            continue

        combined_content = f"{pending['content']}\n\n{chunk['content']}"
        combined_tokens = count_tokens(combined_content)
        should_merge = pending["token_count"] < min_tokens and combined_tokens <= max_tokens

        if should_merge:
            sections = merge_sections(pending["section"], chunk["section"])
            tags = merge_tags(pending["tags"], chunk["tags"])
            metadata = {
                **pending["metadata"],
                "section": sections,
                "tags": tags,
                "merged_sections": merge_tags(
                    pending["metadata"].get("merged_sections", [pending["section"]]),
                    chunk["metadata"].get("merged_sections", [chunk["section"]]),
                ),
            }
            pending = {
                "content": combined_content,
                "token_count": combined_tokens,
                "section": sections,
                "tags": tags,
                "metadata": metadata,
            }
        else:
            merged.append(pending)
            pending = chunk

    if pending:
        merged.append(pending)

    return merged


def merge_sections(left: str, right: str) -> str:
    if left == right:
        return left
    return " | ".join(dict.fromkeys([left, right]))

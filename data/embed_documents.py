"""
Generate embeddings for all document chunks using OpenAI text-embedding-3-small.
Run AFTER seed.py.

Usage: python data/embed_documents.py
"""
import sys
import os
from pathlib import Path

# Add backend to path (works locally and inside container)
parent_dir = Path(__file__).parent.parent
backend_dir = parent_dir / "backend"
if backend_dir.exists():
    sys.path.insert(0, str(backend_dir))
    env_path = backend_dir / ".env"
else:
    sys.path.insert(0, str(parent_dir))
    env_path = parent_dir / ".env"

from dotenv import load_dotenv
load_dotenv(env_path)

DB = {
    "dbname": os.getenv("POSTGRES_DB", "ercot_copilot"),
    "user": os.getenv("POSTGRES_USER", "copilot"),
    "password": os.getenv("POSTGRES_PASSWORD", "copilot_secret"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "text-embedding-3-small"
BATCH = 50


def main():
    if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-placeholder":
        print("OPENAI_API_KEY is not configured; skipping document embeddings.")
        return

    import psycopg2
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    cur.execute("SELECT id, content FROM document_chunks WHERE embedding IS NULL ORDER BY id")
    chunks = cur.fetchall()
    print(f"Embedding {len(chunks)} chunks...")

    for i in range(0, len(chunks), BATCH):
        batch = chunks[i:i+BATCH]
        ids = [r[0] for r in batch]
        texts = [r[1] for r in batch]

        response = client.embeddings.create(model=MODEL, input=texts)
        vectors = [e.embedding for e in response.data]

        for chunk_id, vec in zip(ids, vectors):
            cur.execute(
                "UPDATE document_chunks SET embedding = %s WHERE id = %s",
                (str(vec), chunk_id)
            )
        conn.commit()
        print(f"  ✓ Embedded chunks {i+1}–{min(i+BATCH, len(chunks))}")

    cur.close()
    conn.close()
    print(f"\n✅ All {len(chunks)} chunks embedded!")


if __name__ == "__main__":
    main()

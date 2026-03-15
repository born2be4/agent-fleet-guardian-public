"""Semantic Memory API — FastAPI service for SPO graph with hybrid search.
Embeddings: fastembed (local, no API key required, multilingual).
"""

import os
import json
import logging
from typing import Optional

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory-api")

app = FastAPI(title="Semantic Memory API", version="2.0.0")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required. Set it in docker-compose.yml or pass directly.")
EMBED_MODEL = os.environ.get(
    "EMBED_MODEL",
    "nomic-ai/nomic-embed-text-v1.5-Q",
)
# nomic-embed-text requires prefixes for queries vs documents
NOMIC_MODELS = {"nomic-ai/nomic-embed-text-v1", "nomic-ai/nomic-embed-text-v1.5", "nomic-ai/nomic-embed-text-v1.5-Q"}

# ── Embedder (lazy init) ──────────────────────────────────────────────────────

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        logger.info(f"Loading embedding model: {EMBED_MODEL}")
        _embedder = TextEmbedding(model_name=EMBED_MODEL)
        logger.info("Embedding model loaded.")
    return _embedder


def embed_texts(texts: list[str], mode: str = "document") -> list[list[float]]:
    """Generate embeddings locally via fastembed. Always works, no API key needed.
    mode: 'document' for storage, 'query' for search (nomic requires different prefixes).
    """
    try:
        embedder = get_embedder()
        if EMBED_MODEL in NOMIC_MODELS:
            prefix = "search_query: " if mode == "query" else "search_document: "
            texts = [prefix + t for t in texts]
        result = list(embedder.embed(texts))
        return [list(map(float, v)) for v in result]
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return [None] * len(texts)


# ── DB helpers ────────────────────────────────────────────────────────────────


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def upsert_entity(cur, name: str, embedding=None) -> int:
    name = name.strip()
    if not name:
        raise ValueError("empty entity name")
    cur.execute(
        """
        INSERT INTO entities(name, embedding)
        VALUES(%s, %s)
        ON CONFLICT (name) DO UPDATE
          SET embedding = COALESCE(entities.embedding, EXCLUDED.embedding),
              updated_at = now()
        RETURNING id
        """,
        (name, embedding),
    )
    return cur.fetchone()[0]


# ── Models ────────────────────────────────────────────────────────────────────


class StoreRequest(BaseModel):
    namespace: str = "main"
    subject: str
    predicate: str
    object: str
    content: str = ""
    context: str = ""
    source_url: Optional[str] = None
    metadata: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    namespace: Optional[str] = None
    limit: int = 10


# ── Endpoints ─────────────────────────────────────────────────────────────────


@app.post("/store")
def store_fact(req: StoreRequest):
    embs = embed_texts(
        [req.subject, req.object, f"{req.subject} {req.predicate} {req.object}. {req.content}"]
    )
    subj_emb, obj_emb, fact_emb = embs[0], embs[1], embs[2]

    conn = get_conn()
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            sid = upsert_entity(cur, req.subject, embedding=subj_emb)
            oid = upsert_entity(cur, req.object, embedding=obj_emb)
            meta_json = json.dumps(req.metadata or {}, ensure_ascii=False)
            cur.execute(
                """
                INSERT INTO facts(namespace, subject_id, predicate, object_id,
                                  content, context, source_url, metadata, embedding)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                RETURNING id
                """,
                (
                    req.namespace, sid, req.predicate, oid,
                    req.content, req.context, req.source_url,
                    meta_json, fact_emb,
                ),
            )
            fact_id = cur.fetchone()[0]
        conn.commit()
        return {"ok": True, "fact_id": fact_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/search")
def search_facts(req: SearchRequest):
    q_emb = embed_texts([req.query], mode="query")[0]

    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            ns_filter = ""
            params: dict = {
                "q": req.query,
                "limit": req.limit,
                "q_emb": q_emb,
                "fts_w": 0.35,
                "vec_w": 0.65,
            }

            if req.namespace:
                ns_filter = "AND f.namespace = %(ns)s"
                params["ns"] = req.namespace

            cur.execute(
                f"""
                WITH base AS (
                  SELECT
                    f.id, f.namespace,
                    es.name AS subject, f.predicate, eo.name AS object,
                    f.content, f.context, f.source_url, f.metadata, f.created_at,
                    ts_rank_cd(to_tsvector('simple', f.content), plainto_tsquery('simple', %(q)s)) AS fts_rank,
                    CASE
                      WHEN %(q_emb)s IS NULL OR f.embedding IS NULL THEN 0
                      ELSE (1 - (f.embedding <=> %(q_emb)s::vector))
                    END AS vec_sim
                  FROM facts f
                  JOIN entities es ON es.id = f.subject_id
                  JOIN entities eo ON eo.id = f.object_id
                  WHERE (
                    to_tsvector('simple', f.content) @@ plainto_tsquery('simple', %(q)s)
                    OR (%(q_emb)s IS NOT NULL AND f.embedding IS NOT NULL
                        AND (f.embedding <=> %(q_emb)s::vector) < 0.8)
                  )
                  {ns_filter}
                ),
                ranked AS (
                  SELECT *, (%(fts_w)s * fts_rank + %(vec_w)s * vec_sim) AS score
                  FROM base
                  ORDER BY score DESC, fts_rank DESC
                  LIMIT %(limit)s
                )
                SELECT namespace, subject, predicate, object,
                       content, context, source_url, metadata,
                       score, created_at::text
                FROM ranked;
                """,
                params,
            )
            rows = cur.fetchall()
            return {"query": req.query, "results": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.get("/stats")
def stats():
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) as total_entities FROM entities")
            entities = cur.fetchone()["total_entities"]
            cur.execute("SELECT COUNT(*) as total_facts FROM facts")
            facts = cur.fetchone()["total_facts"]
            cur.execute(
                "SELECT namespace, COUNT(*) as count FROM facts GROUP BY namespace ORDER BY count DESC"
            )
            namespaces = [dict(r) for r in cur.fetchall()]
            return {"entities": entities, "facts": facts, "namespaces": namespaces, "embed_model": EMBED_MODEL}
    finally:
        conn.close()


@app.get("/health")
def health():
    return {"status": "ok", "embed_model": EMBED_MODEL}


@app.on_event("startup")
async def startup():
    """Apply schema on startup, then warm up embedder."""
    import time

    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if not os.path.exists(schema_path):
        logger.warning("schema.sql not found, skipping auto-migration")
        return

    for attempt in range(30):
        try:
            conn = get_conn()
            with open(schema_path) as f:
                with conn.cursor() as cur:
                    cur.execute(f.read())
            conn.commit()
            conn.close()
            logger.info("Schema applied successfully")
            break
        except Exception as e:
            logger.info(f"Waiting for DB (attempt {attempt + 1}): {e}")
            time.sleep(2)
    else:
        logger.error("Failed to apply schema after 30 attempts")
        return

    # Warm up embedder in background
    logger.info("Warming up embedding model...")
    embed_texts(["warmup"])
    logger.info("Embedding model ready.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18800)

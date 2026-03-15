# 🧠 Semantic Memory Infrastructure

**Graph-RAG memory for AI agent fleets — ready to deploy.**

## What is this?

A production-ready semantic memory layer for multi-agent systems. Stores facts as Subject-Predicate-Object (SPO) triples with vector embeddings for hybrid search (FTS + cosine similarity).

Every agent in your fleet can store and retrieve knowledge through a shared API. Namespace isolation ensures each agent sees only its own facts while sharing the same infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              AI Agent Fleet                      │
│                                                  │
│  Agent A ──┐                                     │
│  Agent B ──┤──▶ Memory API (FastAPI :18810)      │
│  Agent C ──┤      │                              │
│  Agent D ──┘      ▼                              │
│              PostgreSQL + pgvector               │
│              (entities + facts + HNSW index)     │
│                                                  │
│  Embedding: fastembed (local, no API key)        │
│  Model: nomic-embed-text-v1.5-Q (768-dim)       │
└─────────────────────────────────────────────────┘
```

## Key Features

- **SPO Graph** — facts stored as (Subject → Predicate → Object) with full-text content
- **Hybrid Search** — FTS (35% weight) + vector cosine similarity (65% weight)
- **Local Embeddings** — fastembed with nomic-embed-text-v1.5-Q, no API key needed
- **Namespace Isolation** — each agent/bot has its own namespace
- **HNSW Indexes** — fast approximate nearest neighbor search via pgvector
- **Auto-migration** — schema applies on startup, idempotent
- **Zero config** — Docker Compose, one command to run

## Quick Start

```bash
cd memory-api
docker compose up -d
```

That's it. API available at `http://localhost:18810`.

## API

### Store a fact

```bash
curl -s http://localhost:18810/store \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "main",
    "subject": "Alice",
    "predicate": "manages",
    "object": "ProjectX",
    "content": "Alice manages ProjectX — an influencer marketplace",
    "context": "From team discussion on 2026-03-15"
  }'
```

### Search memory

```bash
curl -s http://localhost:18810/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "who manages ProjectX",
    "namespace": "main",
    "limit": 5
  }'
```

### Health & stats

```bash
curl -s http://localhost:18810/health
curl -s http://localhost:18810/stats
```

## Schema

```sql
-- Entities: unique named nodes in the knowledge graph
CREATE TABLE entities (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    metadata JSONB DEFAULT '{}',
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Facts: SPO triples with content and embeddings
CREATE TABLE facts (
    id BIGSERIAL PRIMARY KEY,
    namespace TEXT NOT NULL DEFAULT 'main',
    subject_id BIGINT REFERENCES entities(id),
    predicate TEXT NOT NULL,
    object_id BIGINT REFERENCES entities(id),
    content TEXT DEFAULT '',
    context TEXT DEFAULT '',
    source_url TEXT,
    metadata JSONB DEFAULT '{}',
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Indexes:**
- HNSW on `facts.embedding` and `entities.embedding` (cosine distance)
- GIN FTS on `facts.content`
- B-tree on `namespace`, `subject_id`, `object_id`

## Integration with OpenClaw Agents

### From SOUL.md or TOOLS.md

Add to any agent's TOOLS.md:

```markdown
## Semantic Memory
- **API:** http://127.0.0.1:18810
- **Namespace:** <agent-name>
- Store facts: POST /store
- Search: POST /search
```

### From Docker containers

If your agents run in Docker on the same network:

```markdown
## Semantic Memory
- **API:** http://orchestrator-memory-api:18800
```

### Skill Integration

Use the included `SKILL.md` as an OpenClaw skill — agents will automatically store important facts and search memory when needed.

## Embedding Model

**nomic-ai/nomic-embed-text-v1.5-Q**
- 768 dimensions
- ONNX quantized (~130MB)
- Multilingual (tested: English, Russian)
- No API key required
- Nomic prefix handling: `search_query:` for queries, `search_document:` for storage

## Memory Layers

This system provides **Layer 3 (Semantic/Graph)** in a multi-layer memory architecture:

| Layer | Storage | Use Case |
|-------|---------|----------|
| L1: Working | Session context | Current conversation |
| L2: Episodic | MEMORY.md + daily files | What happened, decisions, events |
| L3: Semantic | SPO Graph + pgvector | **Facts, relationships, knowledge** |
| L4: Procedural | SOUL.md, skills | How to behave, what to do |

Combine with OpenClaw's built-in memory (L1+L2+L4) for complete coverage.

## Production Notes

- **RAM:** ~500MB (API + embedding model warm) + PostgreSQL
- **Disk:** grows with facts; 1000 facts ≈ 50MB with embeddings
- **Startup:** ~10s (model download on first run, ~5s warm thereafter)
- **Backup:** `pg_dump` on the volume, or snapshot `memory-db-data` Docker volume
- **Scaling:** single instance handles thousands of facts comfortably; for 100k+ consider read replicas

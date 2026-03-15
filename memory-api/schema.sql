-- Orchestrator Semantic Memory Schema
-- Embeddings: fastembed nomic-embed-text-v1.5-Q (768-dim)

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS entities (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    metadata JSONB NOT NULL DEFAULT '{}',
    embedding vector(768),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS facts (
    id BIGSERIAL PRIMARY KEY,
    namespace TEXT NOT NULL DEFAULT 'main',
    subject_id BIGINT NOT NULL REFERENCES entities(id),
    predicate TEXT NOT NULL,
    object_id BIGINT NOT NULL REFERENCES entities(id),
    content TEXT NOT NULL DEFAULT '',
    context TEXT NOT NULL DEFAULT '',
    source_url TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    embedding vector(768),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_facts_namespace ON facts(namespace);
CREATE INDEX IF NOT EXISTS idx_facts_subject   ON facts(subject_id);
CREATE INDEX IF NOT EXISTS idx_facts_object    ON facts(object_id);
CREATE INDEX IF NOT EXISTS idx_facts_content_fts ON facts USING gin(to_tsvector('simple', content));
CREATE INDEX IF NOT EXISTS idx_facts_embedding   ON facts USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_entities_name     ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_embedding ON entities USING hnsw (embedding vector_cosine_ops);

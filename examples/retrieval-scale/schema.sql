-- pgvector schema — Chapter 03c's deployment target.
--
-- This file is the artifact worth carrying. The Python client is twenty lines; the index
-- decisions below are the ones you live with for the life of the system.
--
-- Local:  docker run -e POSTGRES_PASSWORD=x -p 5432:5432 pgvector/pgvector:pg16
-- GCP:    Cloud SQL for PostgreSQL or AlloyDB, with the `vector` extension enabled.
--         AlloyDB additionally offers ScaNN indexing; the trade below is the same shape.
--
-- NOT executed by this repo's tests: no PostgreSQL is available to them. Run it yourself
-- and confirm against the pgvector version you actually have — the index syntax has
-- changed between releases.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          BIGINT PRIMARY KEY,
    body        TEXT        NOT NULL,
    -- 384 matches the common small embedding models. CHANGING THIS IS A MIGRATION:
    -- the column type carries the dimensionality, so a model swap rewrites the table and
    -- re-embeds the corpus. Decide the model before the schema, not after.
    embedding   VECTOR(384) NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Exact search needs no index at all. It is correct by construction and, on a few hundred
-- thousand rows, often fast enough. Measure before you add an index: everything below
-- trades recall for latency, and an index you did not need is pure risk.
--
--     SELECT id FROM documents ORDER BY embedding <=> $1 LIMIT 10;

-- ---------------------------------------------------------------------------------------
-- Option A: IVFFlat. Same structure as the hand-written index in store.py.
--
-- `lists` is the number of clusters. The usual starting point is rows/1000 up to 1M rows,
-- then sqrt(rows). Query-time recall is bought with `ivfflat.probes`.
--
-- The trap: an IVFFlat index must be built on a table that ALREADY HAS REPRESENTATIVE
-- DATA. Build it on an empty or tiny table and the centroids are meaningless, the lists
-- are lopsided, and recall stays bad no matter how you tune probes. There is no error;
-- you just get worse answers.
CREATE INDEX IF NOT EXISTS documents_embedding_ivfflat
    ON documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- SET ivfflat.probes = 10;   -- per session; higher = better recall, slower

-- ---------------------------------------------------------------------------------------
-- Option B: HNSW. Better recall per unit of latency, slower to build, more memory.
--
--   m                 edges per node (16 is a sane default)
--   ef_construction   build-time effort; raises build time and index quality
--   hnsw.ef_search    query-time effort; the recall knob, same bargain as probes
--
-- CREATE INDEX documents_embedding_hnsw
--     ON documents USING hnsw (embedding vector_cosine_ops)
--     WITH (m = 16, ef_construction = 64);
-- SET hnsw.ef_search = 40;
--
-- Pick HNSW when query latency matters more than build time and you have the memory;
-- IVFFlat when the corpus is rebuilt often or memory is tight. Both are the same trade
-- with different constants — and BOTH need the recall measurement from bench.py, because
-- neither will tell you what it stopped finding.

-- ---------------------------------------------------------------------------------------
-- Keeping it current. A vector index is a cache of a model's opinion, and it goes stale in
-- two different ways, which need two different responses:
--
--   1. A DOCUMENT changed  -> re-embed that row. Cheap, incremental, and `updated_at` is
--      how the job that does it knows what to pick up.
--   2. The MODEL changed   -> re-embed everything. This is a migration and a purchase.
--      Price it with bench.py's embedding report before you schedule it, and write the
--      new vectors into a second column or table so you can compare recall before cutting
--      over. A model swap that silently degrades retrieval looks exactly like nothing.
CREATE INDEX IF NOT EXISTS documents_updated_at ON documents (updated_at);

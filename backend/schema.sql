-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge base table for RAG
CREATE TABLE IF NOT EXISTS front_desk_knowledge (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(768)
);

-- Similarity search function
CREATE OR REPLACE FUNCTION match_front_desk (
    query_embedding VECTOR(768),
    match_threshold FLOAT,
    match_count INT
)
RETURNS TABLE (
    id BIGINT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        fdk.id,
        fdk.content,
        fdk.metadata,
        1 - (fdk.embedding <=> query_embedding) AS similarity
    FROM front_desk_knowledge fdk
    WHERE 1 - (fdk.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- Interaction logs for parents and admins
CREATE TABLE IF NOT EXISTS front_desk_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    feedback TEXT, -- 'thumbs_up', 'thumbs_down', null
    needs_review BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    metadata JSONB
);

-- Users table (as requested in Data Design)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    role TEXT NOT NULL, -- 'parent', 'admin', 'staff'
    school_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

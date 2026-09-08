-- supabase/migrations/20260908_001_create_jobs.sql
-- Initial schema for the Job Hunting Pipeline
-- Mirrors the SQLite schema with cloud-native enhancements

CREATE TABLE IF NOT EXISTS jobs (
    id             BIGSERIAL PRIMARY KEY,
    job_hash       TEXT UNIQUE NOT NULL,
    company        TEXT NOT NULL,
    role           TEXT NOT NULL,
    url            TEXT UNIQUE NOT NULL,
    source         TEXT,
    seniority_tier TEXT CHECK (seniority_tier IN ('Target', 'Stretch')),
    match_score    INTEGER DEFAULT 0,
    matched_skills TEXT,
    hiring_contact TEXT,
    cold_email     TEXT,
    salary         TEXT DEFAULT 'N/A',
    date_posted    TEXT DEFAULT '3d ago',
    cover_letter   TEXT DEFAULT '',
    status         TEXT DEFAULT 'To Review',
    work_setups    TEXT[] DEFAULT '{}',
    employment_type TEXT DEFAULT 'Full-Time',
    min_salary_usd INTEGER,
    max_salary_usd INTEGER,
    resume_url     TEXT,
    cover_letter_url TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Index for deduplication lookups
CREATE INDEX IF NOT EXISTS idx_jobs_hash ON jobs (job_hash);
CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs (url);

-- Index for common filter/sort patterns
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_tier ON jobs (seniority_tier);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs (match_score DESC);

-- Enable real-time subscriptions for the frontend
ALTER PUBLICATION supabase_realtime ADD TABLE jobs;

-- Row Level Security
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Public read access (frontend uses anon key)
CREATE POLICY "Public read access" ON jobs
    FOR SELECT USING (true);

-- Service role has full write access (engine uses service role key)
CREATE POLICY "Service role write access" ON jobs
    FOR ALL USING (true);

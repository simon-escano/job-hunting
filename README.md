# Job Hunting Pipeline

A structured job application tracking system with an automated pipeline engine and a real-time React dashboard.

## Architecture

```
engine/          Python processing pipeline (agent-operated)
web/             React + TypeScript frontend (hosted on Vercel)
supabase/        Database schema and migrations
scripts/         One-time utilities and migration tools
design.md        Design system reference
```

## Quick Start

### 1. Set up Supabase

1. Create a free project at [supabase.com](https://supabase.com)
2. Run the migration in `supabase/migrations/20260908_001_create_jobs.sql` via the SQL editor
3. Create a `resumes` storage bucket (set to public)
4. Copy your credentials to `.env.local`:
   ```
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_ANON_KEY=eyJ...
   SUPABASE_SERVICE_ROLE_KEY=eyJ...
   VITE_SUPABASE_URL=https://xxxxx.supabase.co
   VITE_SUPABASE_ANON_KEY=eyJ...
   ```

### 2. Migrate existing data (if upgrading from SQLite)

```bash
pip install -r engine/requirements.txt
python scripts/migrate_sqlite_to_supabase.py
```

### 3. Run the frontend

```bash
cd web
npm install
npm run dev
```

### 4. Process jobs via the engine

```python
import sys; sys.path.insert(0, "engine")
from engine import process_job

process_job({
    "company": "Acme Corp",
    "role": "Backend Engineer",
    "url": "https://acme.com/careers/backend",
    "description": "Remote worldwide...",
    "salary": "$80k-$120k",
    "date_posted": "2d ago",
    "hiring_contact": "hiring@acme.com"
})
```

## Deployment

The React frontend deploys to Vercel:

1. Connect your GitHub repo to Vercel
2. Set build command: `cd web && npm run build`
3. Set output directory: `web/dist`
4. Add environment variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

## Design System

See [design.md](design.md) for the full color palette, typography scale, spacing grid, animation standards, and anti-vibecoding rules.

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load .env.local from the project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local'))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def is_duplicate(company: str, role: str, url: str) -> bool:
    import hashlib
    normalized = f"{company.strip().lower()}:{role.strip().lower()}"
    job_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    
    res_hash = supabase.table('jobs').select('id').eq('job_hash', job_hash).execute()
    if res_hash.data:
        return True
    res_url = supabase.table('jobs').select('id').eq('url', url.strip()).execute()
    if res_url.data:
        return True
    return False

def insert_job(job_data: dict) -> dict:
    res = supabase.table('jobs').insert(job_data).execute()
    return res.data[0] if res.data else {}

def update_job(job_id: int, updates: dict) -> dict:
    res = supabase.table('jobs').update(updates).eq('id', job_id).execute()
    return res.data[0] if res.data else {}

def fetch_all_jobs() -> list:
    res = supabase.table('jobs').select('*').execute()
    return res.data

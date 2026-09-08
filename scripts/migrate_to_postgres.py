import sqlite3
import psycopg2
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "pipeline.db"
SUPABASE_URL = "https://jeoxcbbrhykkejrwmpex.supabase.co"
PG_CONN_STR = "postgresql://postgres.jeoxcbbrhykkejrwmpex:Os5WfeqC4o7kYgCL@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"

def infer_metadata(company: str, role: str, salary: str):
    role_lower = role.lower()
    company_lower = company.lower()
    
    # Work setups
    setups = set()
    if any(w in role_lower or w in company_lower for w in ["global", "worldwide", "remote"]):
        setups.add("Worldwide")
        setups.add("APAC / Philippines")
    if any(w in company_lower for w in ["lemon.io", "micro1", "invisible"]):
        setups.add("Contractor / B2B")
    if not setups:
        setups.add("Worldwide")
        setups.add("APAC / Philippines")
        
    # Employment type
    if "part-time" in role_lower or "part time" in role_lower:
        emp_type = "Part-Time"
    elif any(w in company_lower for w in ["lemon.io", "micro1"]) or "contractor" in role_lower or "b2b" in role_lower:
        emp_type = "Contract / B2B"
    else:
        emp_type = "Full-Time"
        
    # Salary range parsing in USD annual
    min_usd, max_usd = None, None
    matches = re.findall(r"\$([0-9,]+)", salary)
    if matches:
        nums = [int(m.replace(",", "")) for m in matches]
        if nums:
            min_val = nums[0]
            max_val = nums[1] if len(nums) > 1 else min_val
            # Multiplier heuristic: if under 1000, probably hourly; if 1000-15000, check monthly vs yearly
            if "/month" in salary.lower():
                min_usd = min_val * 12
                max_usd = max_val * 12
            elif "/hour" in salary.lower():
                min_usd = min_val * 2080
                max_usd = max_val * 2080
            else:
                min_usd = min_val
                max_usd = max_val
                
    return list(setups), emp_type, min_usd, max_usd

def migrate():
    sqlite_conn = sqlite3.connect(DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT * FROM jobs ORDER BY id ASC")
    rows = sqlite_cur.fetchall()
    print(f"Found {len(rows)} jobs in SQLite.")

    pg_conn = psycopg2.connect(PG_CONN_STR)
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    migrated = 0
    for r in rows:
        job = dict(r)
        company = job["company"]
        role = job["role"]
        salary = job.get("salary") or "N/A"
        
        setups, emp_type, min_usd, max_usd = infer_metadata(company, role, salary)
        
        # Public URL for PDFs
        resume_filename = os.path.basename(job.get("resume_path") or "")
        resume_url = f"{SUPABASE_URL}/storage/v1/object/public/resumes/{resume_filename}" if resume_filename else None
        
        cover_filename = os.path.basename(job.get("cover_letter_path") or "")
        cover_letter_url = f"{SUPABASE_URL}/storage/v1/object/public/resumes/{cover_filename}" if cover_filename else None

        pg_cur.execute("""
            INSERT INTO jobs (
                job_hash, company, role, url, source,
                seniority_tier, match_score, matched_skills,
                hiring_contact, cold_email, salary, date_posted,
                cover_letter, status, work_setups, employment_type,
                min_salary_usd, max_salary_usd, resume_url, cover_letter_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_hash) DO UPDATE SET
                company = EXCLUDED.company,
                role = EXCLUDED.role,
                url = EXCLUDED.url,
                salary = EXCLUDED.salary,
                status = EXCLUDED.status,
                work_setups = EXCLUDED.work_setups,
                employment_type = EXCLUDED.employment_type,
                min_salary_usd = EXCLUDED.min_salary_usd,
                max_salary_usd = EXCLUDED.max_salary_usd,
                resume_url = EXCLUDED.resume_url,
                cover_letter_url = EXCLUDED.cover_letter_url;
        """, (
            job["job_hash"],
            company,
            role,
            job["url"],
            job.get("source") or "Direct",
            job.get("seniority_tier"),
            job.get("match_score") or 0,
            job.get("matched_skills") or "",
            job.get("hiring_contact") or "",
            job.get("cold_email") or "",
            salary,
            job.get("date_posted") or "3d ago",
            job.get("cover_letter") or "",
            job.get("status") or "To Review",
            setups,
            emp_type,
            min_usd,
            max_usd,
            resume_url,
            cover_letter_url
        ))
        migrated += 1

    pg_cur.execute("SELECT COUNT(*) FROM jobs;")
    total_in_pg = pg_cur.fetchone()[0]
    print(f"Migration complete: {migrated} jobs inserted. Total in Supabase PostgreSQL: {total_in_pg}.")

    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate()

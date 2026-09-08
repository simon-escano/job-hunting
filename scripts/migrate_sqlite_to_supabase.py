import sqlite3
import os
import sys
from pathlib import Path

# Add project root to sys.path to allow importing from engine
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

import engine.db as db
import engine.storage as storage

def migrate():
    db_path = PROJECT_ROOT / "pipeline.db"
    
    if not db_path.exists():
        print(f"Old database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs")
    rows = cur.fetchall()
    
    migrated_count = 0
    for row in rows:
        job = dict(row)
        
        # Upload resume
        resume_path = job.get("resume_path")
        resume_url = None
        if resume_path and os.path.exists(resume_path):
            resume_filename = os.path.basename(resume_path)
            resume_url = storage.upload_pdf(resume_path, resume_filename)
            
        # Upload cover letter
        cover_letter_path = job.get("cover_letter_path")
        cover_letter_url = None
        if cover_letter_path and os.path.exists(cover_letter_path):
            cover_letter_filename = os.path.basename(cover_letter_path)
            cover_letter_url = storage.upload_pdf(cover_letter_path, cover_letter_filename)
            
        # Remove old path fields, id, created_at
        job_data = {k: v for k, v in job.items() if k not in ["id", "created_at", "resume_path", "cover_letter_path"]}
        
        # Add new fields
        job_data["resume_url"] = resume_url
        job_data["cover_letter_url"] = cover_letter_url
        job_data["work_setups"] = []
        job_data["employment_type"] = ""
        job_data["min_salary_usd"] = None
        job_data["max_salary_usd"] = None
        
        db.insert_job(job_data)
        migrated_count += 1

    conn.close()
    print(f"Migration complete. Migrated {migrated_count} jobs.")

if __name__ == "__main__":
    migrate()

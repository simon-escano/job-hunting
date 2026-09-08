import csv
import sys
from pathlib import Path

# Add project root to sys.path to allow importing from engine
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

import engine.db as db

def export_csv():
    jobs = db.fetch_all_jobs()
    if not jobs:
        print("No jobs found in Supabase.")
        return
        
    output_path = PROJECT_ROOT / "jobs_export.csv"
    
    # Get all unique headers across all jobs
    headers = set()
    for job in jobs:
        headers.update(job.keys())
    headers = sorted(list(headers))
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(jobs)
        
    print(f"Exported {len(jobs)} jobs to {output_path}")

if __name__ == "__main__":
    export_csv()

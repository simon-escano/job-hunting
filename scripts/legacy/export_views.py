"""Pipeline Views Exporter (`export_views.py`)

Generates:
1. dist/pipeline.csv - Structured CSV export including salary ranges, relative dates, and contacts.
2. dist/pipeline.html - High-craft "Job Hunting" dashboard strictly compliant with design.md:
   - Sticky top control hierarchy (Header, Search/Filters, Download button, Table Header).
   - Aesthetic custom scrollbars (sleek 6px rounded pills, zero default primitives).
   - High-contrast, beautifully styled status dropdown in both dark mode and light mode.
   - Colored Target (Chartreuse) and Stretch (Lemon) filter buttons.
   - Interactive column resizing from both table headers and table body rows with localStorage persistence.
   - User-friendly Listing & Resume cell: primary "Apply ↗" button with domain subtext + tailored PDF resume chip below.
   - Distinct column dividing lines between every column.
   - Zero em dashes throughout the entire codebase and output.
"""

from __future__ import annotations

import csv
import re
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "pipeline.db"
DIST_DIR = ROOT_DIR / "dist"
CSV_PATH = DIST_DIR / "pipeline.csv"
HTML_PATH = DIST_DIR / "pipeline.html"

# Ensure dist directory exists
DIST_DIR.mkdir(parents=True, exist_ok=True)


def load_jobs(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Query all tracked jobs from pipeline.db ordered by match score and date."""
    if not db_path.exists():
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id, job_hash, company, role, url, source,
            seniority_tier, match_score, matched_skills,
            hiring_contact, cold_email, resume_path,
            COALESCE(cover_letter, '') AS cover_letter,
            COALESCE(cover_letter_path, '') AS cover_letter_path,
            COALESCE(salary, 'N/A') AS salary,
            COALESCE(date_posted, '3d ago') AS date_posted,
            status, created_at
        FROM jobs
        ORDER BY match_score DESC, created_at DESC
        """
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def to_file_uri(file_path: str) -> str:
    """Convert a local file path to a browser-clickable file:// URI."""
    if not file_path:
        return ""
    p = Path(file_path).resolve()
    return p.as_uri()


def get_base_domain(url: str) -> str:
    """Extract clean base domain from a URL (e.g. 'workatastartup.com')."""
    if not url:
        return "listing"
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain or "listing"


def export_csv(jobs: List[Dict[str, Any]], output_path: Path = CSV_PATH) -> Path:
    """
    Write all rows to dist/pipeline.csv with columns:
    [Match & Tier, Company & Role, Salary, Date Posted, Live Listing, Contact Lead, Tailored Resume, Cold Email Snippet, Status]
    """
    headers = [
        "Match & Tier",
        "Company & Role",
        "Salary",
        "Date Posted",
        "Live Listing",
        "Contact Lead",
        "Tailored Resume",
        "Cold Email Snippet",
        "Tailored Cover Letter",
        "Cover Letter PDF",
        "Status",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for job in jobs:
            match_score = job.get("match_score") or 0
            tier = job.get("seniority_tier") or "Target"
            match_and_tier = f"{tier} ({match_score}%)"
            company_role = f"{job.get('company', '')} - {job.get('role', '')}"
            salary = job.get("salary") or "N/A"
            if salary == "Undisclosed":
                salary = "N/A"
            date_posted = job.get("date_posted") or "3d ago"
            live_listing = job.get("url", "")
            hiring_lead = job.get("hiring_contact") or "engineering@company.com"
            resume_uri = to_file_uri(job.get("resume_path", ""))
            cold_email = job.get("cold_email", "")
            cover_letter = job.get("cover_letter", "")
            cover_letter_uri = to_file_uri(job.get("cover_letter_path", ""))
            status = job.get("status", "To Review")

            writer.writerow(
                [
                    match_and_tier,
                    company_role,
                    salary,
                    date_posted,
                    live_listing,
                    hiring_lead,
                    resume_uri,
                    cold_email,
                    cover_letter,
                    cover_letter_uri,
                    status,
                ]
            )

    return output_path



def infer_job_metadata(company: str, role: str, salary_str: str) -> tuple[list[str], str, int | None, int | None]:
    """Derive work setups, employment type, and annual USD salary bounds for filtering."""
    role_lower = role.lower()
    comp_lower = company.lower()

    # Work setups (open to remote candidate in Cebu, Philippines)
    setups = set()
    if any(k in role_lower for k in ['global', 'worldwide', '100% remote', 'remote / global']):
        setups.add('Worldwide')
        setups.add('APAC / Philippines')
    elif 'philippines' in role_lower or 'apac' in role_lower:
        setups.add('APAC / Philippines')
    else:
        setups.add('Worldwide')
        setups.add('APAC / Philippines')

    if any(k in comp_lower for k in ['lemon.io', 'micro1', 'invisible technologies']) or 'contract' in role_lower or 'b2b' in role_lower:
        setups.add('Contractor / B2B')

    # Employment type
    if any(k in role_lower for k in ['part-time', 'part time']):
        emp_type = 'Part-Time'
    elif any(k in comp_lower for k in ['lemon.io', 'micro1']) or any(k in role_lower for k in ['contractor', 'contract', 'b2b', 'specialist - ai trainer']):
        emp_type = 'Contract / B2B'
    else:
        emp_type = 'Full-Time'

    # Salary parsing to annual USD bounds
    min_usd, max_usd = None, None
    if salary_str and salary_str != 'N/A' and salary_str.lower() != 'undisclosed':
        nums = re.findall(r'\$([\d,]+)', salary_str)
        if nums:
            min_usd = int(nums[0].replace(',', ''))
            max_usd = int(nums[1].replace(',', '')) if len(nums) > 1 else min_usd

    return list(setups), emp_type, min_usd, max_usd

def export_html(jobs: List[Dict[str, Any]], output_path: Path = HTML_PATH) -> Path:
    """
    Generate the interactive 'Job Hunting' dashboard strictly adhering to design.md:
    - Zero vibecoding tropes (no emojis in headings, no gradients, no default Inter, no glassmorphism, zero em dashes).
    - Palette tokens: Light Canvas #FCFCFC, Dark Canvas #0E100D, Chartreuse #D2F898, Lemon #F6F930.
    - Sticky group: Header, Search & Filters, Download button, and Table Header remain pinned while scrolling.
    - Column dividing lines between header and table cells for enhanced clarity.
    - Resizing from both header and rows with persistent localStorage state.
    - User-friendly apply button with subtext + tailored PDF resume chip below.
    - Aesthetic custom scrollbars (6px pills, no default primitives).
    - Flawless dark mode status dropdown contrast.
    """
    total_count = len(jobs)
    target_count = sum(1 for j in jobs if j.get("seniority_tier") == "Target")
    stretch_count = sum(1 for j in jobs if j.get("seniority_tier") == "Stretch")

    jobs_data = []
    for j in jobs:
        sal = j.get("salary") or "N/A"
        if sal == "Undisclosed":
            sal = "N/A"
        cold_msg = j.get("cold_email", "")
        setups, emp_type, min_sal, max_sal = infer_job_metadata(
            j.get("company", ""),
            j.get("role", ""),
            sal,
        )
        jobs_data.append(
            {
                "id": j.get("id"),
                "job_hash": j.get("job_hash", ""),
                "company": j.get("company", ""),
                "role": j.get("role", ""),
                "url": j.get("url", ""),
                "base_domain": get_base_domain(j.get("url", "")),
                "source": j.get("source", "Direct"),
                "tier": j.get("seniority_tier", "Target"),
                "match_score": j.get("match_score") or 0,
                "matched_skills": j.get("matched_skills", ""),
                "hiring_contact": j.get("hiring_contact") or "engineering@company.com",
                "salary": sal,
                "min_salary_usd": min_sal,
                "max_salary_usd": max_sal,
                "work_setups": setups,
                "employment_type": emp_type,
                "date_posted": j.get("date_posted") or "3d ago",
                "cold_email": cold_msg,
                "cover_letter": j.get("cover_letter", ""),
                "resume_uri": to_file_uri(j.get("resume_path", "")),
                "cover_letter_uri": to_file_uri(j.get("cover_letter_path", "")),
                "status": j.get("status", "To Review"),
            }
        )

    jobs_json = json.dumps(jobs_data)

    html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="system">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Job Hunting</title>
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32' width='32' height='32'%3E%3Crect width='32' height='32' rx='7' fill='%230E100D'/%3E%3Cpath d='M10 10 L16 16 L10 22' stroke='%23D2F898' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3Cline x1='17' y1='22' x2='22' y2='22' stroke='%23F6F930' stroke-width='2.5' stroke-linecap='round'/%3E%3C/svg%3E">
  <style>
    /* -------------------------------------------------------------
       Design System Tokens (from design.md)
       ------------------------------------------------------------- */
    :root {{
      --bg-canvas: #FCFCFC;
      --bg-surface: #FFFFFF;
      --bg-surface-elevated: #F5F5F3;
      --bg-surface-subtle: #EFEFEA;

      --text-primary: #121212;
      --text-secondary: #2F2F2F;
      --text-muted: #6B7280;
      --text-faint: #9CA3AF;
      --text-inverse: #FCFCFC;

      --border-subtle: rgba(0, 0, 0, 0.08);
      --border-default: rgba(0, 0, 0, 0.14);
      --border-strong: #2F2F2F;

      --accent-lime: #D2F898;
      --accent-lime-fg: #142403;
      --accent-lemon: #F6F930;
      --accent-lemon-fg: #2E2F00;

      --tag-bg: rgba(0, 0, 0, 0.03);
      --tag-border: rgba(0, 0, 0, 0.08);
      --tag-text: #2F2F2F;

      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: "JetBrains Mono", "Geist Mono", SFMono-Regular, Menlo, Monaco, Consolas, monospace;

      color-scheme: light dark;
    }}

    @media (prefers-color-scheme: dark) {{
      :root[data-theme="system"] {{
        --bg-canvas: #0E100D;
        --bg-surface: #151813;
        --bg-surface-elevated: #1D211A;
        --bg-surface-subtle: #252A21;

        --text-primary: #F7F9F5;
        --text-secondary: #D4D9CE;
        --text-muted: #8E9684;
        --text-faint: #5C6353;
        --text-inverse: #0E100D;

        --border-subtle: rgba(255, 255, 255, 0.08);
        --border-default: rgba(255, 255, 255, 0.14);
        --border-strong: #3F4738;

        --accent-lime: #D2F898;
        --accent-lime-fg: #0E100D;
        --accent-lemon: #F6F930;
        --accent-lemon-fg: #0E100D;

        --tag-bg: rgba(255, 255, 255, 0.04);
        --tag-border: rgba(255, 255, 255, 0.08);
        --tag-text: #D4D9CE;
      }}
    }}

    :root[data-theme="dark"] {{
      --bg-canvas: #0E100D;
      --bg-surface: #151813;
      --bg-surface-elevated: #1D211A;
      --bg-surface-subtle: #252A21;

      --text-primary: #F7F9F5;
      --text-secondary: #D4D9CE;
      --text-muted: #8E9684;
      --text-faint: #5C6353;
      --text-inverse: #0E100D;

      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-default: rgba(255, 255, 255, 0.14);
      --border-strong: #3F4738;

      --accent-lime: #D2F898;
      --accent-lime-fg: #0E100D;
      --accent-lemon: #F6F930;
      --accent-lemon-fg: #0E100D;

      --tag-bg: rgba(255, 255, 255, 0.04);
      --tag-border: rgba(255, 255, 255, 0.08);
      --tag-text: #D4D9CE;
    }}

    :root[data-theme="light"] {{
      --bg-canvas: #FCFCFC;
      --bg-surface: #FFFFFF;
      --bg-surface-elevated: #F5F5F3;
      --bg-surface-subtle: #EFEFEA;

      --text-primary: #121212;
      --text-secondary: #2F2F2F;
      --text-muted: #6B7280;
      --text-faint: #9CA3AF;
      --text-inverse: #FCFCFC;

      --border-subtle: rgba(0, 0, 0, 0.08);
      --border-default: rgba(0, 0, 0, 0.14);
      --border-strong: #2F2F2F;

      --accent-lime: #D2F898;
      --accent-lime-fg: #142403;
      --accent-lemon: #F6F930;
      --accent-lemon-fg: #2E2F00;

      --tag-bg: rgba(0, 0, 0, 0.03);
      --tag-border: rgba(0, 0, 0, 0.08);
      --tag-text: #2F2F2F;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    /* -------------------------------------------------------------
       Aesthetic Custom Scrollbars
       ------------------------------------------------------------- */
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}

    ::-webkit-scrollbar-track {{
      background: transparent;
    }}

    ::-webkit-scrollbar-thumb {{
      background: var(--border-default);
      border-radius: 4px;
      transition: background 120ms ease;
    }}

    ::-webkit-scrollbar-thumb:hover {{
      background: var(--border-strong);
    }}

    * {{
      scrollbar-width: thin;
      scrollbar-color: var(--border-default) transparent;
    }}

    html, body {{
      background-color: var(--bg-canvas);
      color: var(--text-primary);
      font-family: var(--font-sans);
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      height: 100%;
    }}

    body {{
      padding: 0 24px 24px;
      display: flex;
      flex-direction: column;
    }}

    .container {{
      max-width: 1760px;
      width: 100%;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
    }}

    /* -------------------------------------------------------------
       Sticky Top Panel: Header, Search & Filters, Download CSV
       ------------------------------------------------------------- */
    .sticky-top-panel {{
      position: sticky;
      top: 0;
      z-index: 100;
      background-color: var(--bg-canvas);
      padding-top: 18px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-subtle);
      margin-bottom: 12px;
      flex-shrink: 0;
    }}

    header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-bottom: 12px;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    /* Keyframe Animations */
    @keyframes rowReveal {{
      0% {{
        opacity: 0;
        transform: translateY(6px);
      }}
      100% {{
        opacity: 1;
        transform: translateY(0);
      }}
    }}

    /* Global Smooth Theme Transitions */
    body, .sticky-top-panel, thead th, .seg-btn, .status-filter-btn, .export-csv-btn, .search-input, .table-container, .status-select-wrap, .email-container {{
      transition: background-color 220ms cubic-bezier(0.16, 1, 0.3, 1),
                  border-color 220ms cubic-bezier(0.16, 1, 0.3, 1),
                  color 220ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .brand-mark {{
      width: 28px;
      height: 28px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-default);
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1), border-color 200ms ease;
    }}

    .brand:hover .brand-mark {{
      transform: scale(1.06);
      border-color: var(--border-strong);
    }}

    h1 {{
      font-size: 18px;
      font-weight: 600;
      letter-spacing: -0.02em;
      color: var(--text-primary);
      transition: color 200ms ease;
    }}

    .theme-toggle-btn {{
      background: var(--bg-surface);
      border: 1px solid var(--border-default);
      color: var(--text-secondary);
      border-radius: 6px;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .theme-toggle-btn:hover {{
      background: var(--bg-surface-subtle);
      border-color: var(--border-strong);
      color: var(--text-primary);
      transform: rotate(18deg) scale(1.08);
    }}

    .theme-toggle-btn:active {{
      transform: scale(0.92);
    }}

    /* Toolbar Rows */
    .toolbar-container {{
      display: flex;
      flex-direction: column;
      gap: 9px;
    }}

    .toolbar-main {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .toolbar-left {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      flex: 1;
    }}

    .search-box {{
      position: relative;
      min-width: 280px;
      max-width: 440px;
      flex: 1;
    }}

    .search-input {{
      width: 100%;
      height: 32px;
      background: var(--bg-surface);
      border: 1px solid var(--border-default);
      border-radius: 6px;
      padding: 0 10px;
      font-family: var(--font-sans);
      font-size: 12.5px;
      color: var(--text-primary);
      outline: none;
      transition: border-color 200ms ease, box-shadow 200ms cubic-bezier(0.16, 1, 0.3, 1), background-color 200ms ease;
    }}

    .search-input:hover {{
      border-color: var(--border-strong);
    }}

    .search-input:focus {{
      border-color: var(--border-strong);
      box-shadow: 0 0 0 2px rgba(210, 248, 152, 0.4);
    }}

    /* Segmented Tier Control with Colors */
    .segmented-control {{
      display: inline-flex;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-default);
      border-radius: 6px;
      padding: 2px;
      gap: 2px;
    }}

    .seg-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 11.5px;
      font-weight: 500;
      padding: 3px 9px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}

    .seg-btn:hover {{
      color: var(--text-primary);
      transform: translateY(-1px);
    }}

    .seg-btn:active {{
      transform: translateY(0) scale(0.96);
    }}

    .seg-btn.active {{
      background: var(--bg-surface);
      color: var(--text-primary);
      font-weight: 600;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      transform: none;
    }}

    .tier-filter-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      display: inline-block;
      flex-shrink: 0;
      transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1), background-color 200ms ease;
    }}

    .seg-btn:hover .tier-filter-dot {{
      transform: scale(1.25);
    }}

    .seg-btn.active .tier-filter-dot {{
      transform: scale(1.15);
    }}

    .dot-target {{ background-color: var(--accent-lime); }}
    .dot-stretch {{ background-color: var(--accent-lemon); }}

    .seg-btn.seg-target.active {{
      background-color: var(--accent-lime);
      color: var(--accent-lime-fg);
      font-weight: 600;
      box-shadow: 0 2px 6px rgba(210, 248, 152, 0.35);
    }}

    .seg-btn.seg-target.active .dot-target {{
      background-color: var(--accent-lime-fg);
    }}

    .seg-btn.seg-stretch.active {{
      background-color: var(--accent-lemon);
      color: var(--accent-lemon-fg);
      font-weight: 600;
      box-shadow: 0 2px 6px rgba(246, 249, 48, 0.35);
    }}

    .seg-btn.seg-stretch.active .dot-stretch {{
      background-color: var(--accent-lemon-fg);
    }}

    /* Status Filter Bar with Unified Color Codes */
    .status-filter-bar {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }}

    .filter-label {{
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      margin-right: 2px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .status-filter-btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--bg-surface);
      border: 1px solid var(--border-default);
      color: var(--text-secondary);
      font-family: var(--font-sans);
      font-size: 11.5px;
      font-weight: 500;
      padding: 3px 9px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .status-filter-btn:hover {{
      background: var(--bg-surface-elevated);
      border-color: var(--border-strong);
      color: var(--text-primary);
      transform: translateY(-1px);
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }}

    .status-filter-btn:active {{
      transform: translateY(0) scale(0.96);
    }}

    .status-filter-btn.active {{
      background: var(--bg-surface-elevated);
      border-color: var(--border-strong);
      color: var(--text-primary);
      font-weight: 600;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}

    .status-filter-btn .status-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      flex-shrink: 0;
      display: inline-block;
      transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1), background-color 200ms ease;
    }}

    .status-filter-btn:hover .status-dot {{
      transform: scale(1.3);
    }}

    .status-filter-btn.active .status-dot {{
      transform: scale(1.15);
    }}

    /* Color Dot Codes on Filters */
    .dot-all {{ background-color: var(--text-muted); }}
    .dot-to-review {{ background-color: #9CA3AF; }}
    .dot-applied {{ background-color: #84CC16; }}
    .dot-interviewing {{ background-color: #F59E0B; }}
    .dot-offer {{ background-color: #10B981; }}
    .dot-rejected {{ background-color: #EF4444; }}

    .status-filter-btn[data-status="Applied"].active {{
      background-color: rgba(210, 248, 152, 0.22);
      border-color: rgba(210, 248, 152, 0.7);
      color: var(--text-primary);
    }}

    .status-filter-btn[data-status="Interviewing"].active {{
      background-color: rgba(246, 249, 48, 0.22);
      border-color: rgba(246, 249, 48, 0.7);
      color: var(--text-primary);
    }}

    .status-filter-btn[data-status="Offer"].active {{
      background-color: var(--accent-lime);
      color: var(--accent-lime-fg);
      border-color: transparent;
      box-shadow: 0 2px 6px rgba(210, 248, 152, 0.35);
    }}

    .status-filter-btn[data-status="Rejected"].active {{
      background-color: rgba(239, 68, 68, 0.16);
      border-color: rgba(239, 68, 68, 0.6);
      color: #EF4444;
    }}

    .filter-count {{
      font-family: var(--font-mono);
      font-size: 10.5px;
      opacity: 0.75;
      transition: opacity 180ms ease, transform 180ms ease;
    }}

    /* Download CSV Button with Icon */
    .export-csv-btn {{
      height: 32px;
      background: var(--bg-surface);
      border: 1px solid var(--border-default);
      border-radius: 6px;
      padding: 0 12px;
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 500;
      color: var(--text-primary);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
      white-space: nowrap;
    }}

    .export-csv-btn:hover {{
      background: var(--bg-surface-subtle);
      border-color: var(--border-strong);
      transform: translateY(-1.5px);
      box-shadow: 0 3px 6px rgba(0, 0, 0, 0.06);
    }}

    .export-csv-btn:active {{
      transform: translateY(0) scale(0.96);
      box-shadow: none;
    }}

    .btn-icon {{
      width: 14px;
      height: 14px;
      flex-shrink: 0;
      transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .export-csv-btn:hover .btn-icon {{
      transform: translateY(1.5px);
    }}

    /* -------------------------------------------------------------
       Data Table Container & Header with Column Dividing Lines
       ------------------------------------------------------------- */
    .table-container {{
      background: var(--bg-surface);
      border: 1px solid var(--border-default);
      border-radius: 8px;
      overflow: auto;
      flex: 1;
      min-height: 0;
      position: relative;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      min-width: 1220px;
      table-layout: fixed;
    }}

    thead th {{
      background: var(--bg-surface-elevated);
      color: var(--text-muted);
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 9px 10px;
      border-bottom: 1px solid var(--border-default);
      border-right: 1px solid var(--border-default);
      position: sticky;
      top: 0;
      z-index: 30;
      user-select: none;
      cursor: grab;
      box-shadow: 0 1px 0 var(--border-default);
      transition: background-color 180ms ease, color 180ms ease, opacity 180ms ease;
    }}

    thead th:last-child {{
      border-right: none;
    }}

    thead th.col-dragging {{
      opacity: 0.4;
      cursor: grabbing;
    }}

    thead th.drop-left {{
      border-left: 2px solid var(--accent-lime-fg);
    }}

    thead th.drop-right {{
      border-right: 2px solid var(--accent-lime-fg);
    }}

    thead th:hover {{
      background: var(--bg-surface-subtle);
      color: var(--text-primary);
    }}

    .th-content {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 4px;
      width: 100%;
    }}

    .col-title {{
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}

    .sort-arrow {{
      font-size: 10px;
      opacity: 0.3;
      flex-shrink: 0;
      transition: opacity 180ms ease, transform 200ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    thead th:hover .sort-arrow {{
      opacity: 0.75;
      transform: scale(1.1);
    }}

    thead th.sorted .sort-arrow {{
      opacity: 1;
      color: var(--text-primary);
      transform: scale(1.2);
    }}

    /* Column Resizer Handle (Header & Body Rows) */
    .col-resizer {{
      position: absolute;
      top: 0;
      right: -3px;
      width: 7px;
      height: 100%;
      cursor: col-resize;
      user-select: none;
      z-index: 20;
      transition: background-color 150ms ease, width 150ms ease;
    }}

    .col-resizer:hover,
    .col-resizer.resizing {{
      background-color: var(--accent-lime);
    }}

    tbody tr {{
      border-bottom: 1px solid var(--border-subtle);
      transition: background-color 150ms cubic-bezier(0.16, 1, 0.3, 1);
      animation: rowReveal 220ms cubic-bezier(0.16, 1, 0.3, 1) both;
    }}

    tbody tr:last-child {{
      border-bottom: none;
    }}

    tbody tr:hover {{
      background: var(--bg-surface-elevated);
    }}

    td {{
      padding: 10px 10px;
      font-size: 13px;
      vertical-align: top;
      overflow: hidden;
      word-break: break-word;
      border-right: 1px solid var(--border-subtle);
      position: relative;
      transition: background-color 150ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    td:last-child {{
      border-right: none;
    }}

    /* Inline Tier & Match Badge */
    .tier-badge-inline {{
      display: inline-flex;
      align-items: center;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      padding: 3px 7px;
      border-radius: 4px;
      white-space: nowrap;
      letter-spacing: -0.01em;
      transition: transform 180ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 180ms ease;
    }}

    .tier-badge-inline:hover {{
      transform: translateY(-1px) scale(1.02);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
    }}

    .tier-badge-inline.target {{
      background: var(--accent-lime);
      color: var(--accent-lime-fg);
    }}

    .tier-badge-inline.stretch {{
      background: var(--accent-lemon);
      color: var(--accent-lemon-fg);
    }}

    /* Company & Role */
    .company-name {{
      font-weight: 600;
      color: var(--text-primary);
      font-size: 13.5px;
    }}

    .role-title {{
      color: var(--text-secondary);
      font-size: 12.5px;
      margin-top: 2px;
    }}

    .skills-list {{
      display: flex;
      flex-wrap: wrap;
      gap: 3px;
      margin-top: 5px;
    }}

    .skill-tag {{
      font-family: var(--font-mono);
      font-size: 10.5px;
      background: var(--tag-bg);
      color: var(--tag-text);
      padding: 1px 5px;
      border-radius: 3px;
      border: 1px solid var(--tag-border);
      transition: background-color 150ms ease, border-color 150ms ease, transform 150ms ease;
    }}

    .skill-tag:hover {{
      border-color: var(--border-strong);
      transform: translateY(-1px);
    }}

    /* Salary Range */
    .salary-cell {{
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 500;
      color: var(--text-secondary);
      white-space: nowrap;
    }}

    .salary-cell.na {{
      color: var(--text-faint);
    }}

    .date-cell {{
      font-family: var(--font-mono);
      font-size: 11.5px;
      color: var(--text-muted);
      white-space: nowrap;
    }}

    /* -------------------------------------------------------------
       User-Friendly Listing & Resume Cell
       ------------------------------------------------------------- */
    .apply-resume-cell {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      width: 100%;
    }}

    .apply-btn {{
      display: flex;
      flex-direction: column;
      background-color: var(--accent-lime);
      color: var(--accent-lime-fg);
      border: 1px solid rgba(0, 0, 0, 0.14);
      border-radius: 5px;
      padding: 5px 9px;
      text-decoration: none;
      width: 100%;
      box-sizing: border-box;
      transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1),
                  box-shadow 200ms cubic-bezier(0.16, 1, 0.3, 1),
                  filter 200ms ease,
                  border-color 200ms ease;
    }}

    :root[data-theme="dark"] .apply-btn,
    :root[data-theme="system"] .apply-btn {{
      border-color: rgba(210, 248, 152, 0.4);
    }}

    .apply-btn:hover {{
      transform: translateY(-2px);
      filter: brightness(1.06);
      box-shadow: 0 3px 8px rgba(210, 248, 152, 0.4);
    }}

    .apply-btn:active {{
      transform: translateY(0) scale(0.97);
      filter: brightness(0.95);
      box-shadow: none;
    }}

    .apply-btn-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .apply-btn-label {{
      font-weight: 700;
      font-size: 12px;
      color: var(--accent-lime-fg);
      letter-spacing: -0.01em;
    }}

    .apply-btn-arrow {{
      font-size: 11px;
      font-weight: 700;
      color: var(--accent-lime-fg);
      transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .apply-btn:hover .apply-btn-arrow {{
      transform: translate(2.5px, -2.5px);
    }}

    .apply-btn-domain {{
      font-size: 10px;
      color: var(--accent-lime-fg);
      opacity: 0.85;
      font-family: var(--font-mono);
      font-weight: 500;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      margin-top: 1px;
    }}

    /* Tactile PDF Resume Attachment Button (Unrestricted Width) */
    .resume-attachment-btn {{
      display: flex;
      align-items: center;
      gap: 6px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-default);
      border-radius: 4px;
      padding: 4px 7px;
      font-size: 11px;
      font-family: var(--font-mono);
      color: var(--text-secondary);
      text-decoration: none;
      cursor: grab;
      user-select: none;
      width: 100%;
      max-width: none;
      box-sizing: border-box;
      transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1),
                  background 200ms ease,
                  border-color 200ms ease,
                  box-shadow 200ms ease,
                  color 200ms ease;
    }}

    .resume-attachment-btn:hover {{
      border-color: var(--border-strong);
      background: var(--bg-surface-subtle);
      color: var(--text-primary);
      transform: translateY(-1.5px);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
    }}

    .resume-attachment-btn:active {{
      cursor: grabbing;
      transform: translateY(0) scale(0.97);
      box-shadow: none;
    }}

    .pdf-tag {{
      background: #EF4444;
      color: #FFFFFF;
      font-size: 8.5px;
      font-weight: 700;
      border-radius: 2px;
      padding: 1px 3px;
      line-height: 1;
      letter-spacing: 0.02em;
      flex-shrink: 0;
      transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .pdf-tag.tag-cl {{
      background: #2563EB;
      color: #FFFFFF;
    }}

    .cover-letter-attachment-btn {{
      border-color: rgba(37, 99, 235, 0.22);
    }}

    :root[data-theme="dark"] .cover-letter-attachment-btn,
    :root[data-theme="system"] .cover-letter-attachment-btn {{
      border-color: rgba(96, 165, 250, 0.22);
    }}

    .cover-letter-attachment-btn:hover {{
      border-color: #2563EB;
      background: rgba(37, 99, 235, 0.05);
    }}

    .resume-attachment-btn:hover .pdf-tag {{
      transform: scale(1.08);
    }}

    .resume-filename {{
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      min-width: 0;
      flex: 1;
    }}

    .drag-handle {{
      font-size: 10px;
      opacity: 0.4;
      flex-shrink: 0;
      margin-left: 2px;
    }}

    /* Merged Contact Lead Header inside Outreach Box */
    .lead-header-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      margin-bottom: 5px;
      padding-bottom: 5px;
      border-bottom: 1px solid var(--border-subtle);
    }}

    .lead-email-wrap {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      min-width: 0;
      flex: 1;
    }}

    .lead-label {{
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .truncated-email {{
      display: inline-flex;
      align-items: center;
      max-width: 100%;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-primary);
      text-decoration: none;
      transition: color 180ms ease, transform 180ms ease;
    }}

    .truncated-email:hover {{
      text-decoration: underline;
      transform: translateX(1.5px);
    }}

    .truncated-link {{
      display: inline-flex;
      align-items: center;
      max-width: 100%;
      color: var(--text-primary);
      text-decoration: none;
      font-size: 11px;
      font-weight: 500;
      transition: color 180ms ease, transform 180ms ease;
      white-space: nowrap;
      flex-shrink: 0;
    }}

    .truncated-link:hover {{
      text-decoration: underline;
      transform: translateX(1.5px);
    }}

    .truncated-link.text-muted {{
      color: var(--text-muted);
    }}

    .link-label {{
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      min-width: 0;
    }}

    .link-arrow {{
      flex-shrink: 0;
      margin-left: 3px;
      font-size: 11px;
      transition: transform 180ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .truncated-link:hover .link-arrow {{
      transform: translate(2.5px, -2.5px);
    }}

    .email-label {{
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      min-width: 0;
    }}

    /* Cold Outreach Box */
    .email-container {{
      position: relative;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: 6px;
      padding: 7px 9px;
      max-width: 100%;
      transition: border-color 200ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 200ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .email-container:hover {{
      border-color: var(--border-default);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
    }}

    .email-content-wrap {{
      position: relative;
    }}

    .email-text {{
      font-family: var(--font-mono);
      font-size: 11px;
      line-height: 1.45;
      color: var(--text-secondary);
      word-break: break-word;
      max-height: 46px;
      overflow: hidden;
      transition: max-height 300ms cubic-bezier(0.16, 1, 0.3, 1), opacity 200ms ease;
    }}

    .email-text.expanded {{
      max-height: 400px;
    }}

    .expand-toggle {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 10.5px;
      font-weight: 500;
      cursor: pointer;
      padding: 2px 0;
      margin-top: 2px;
      display: inline-block;
      transition: color 180ms ease, transform 180ms ease;
    }}

    .expand-toggle:hover {{
      color: var(--text-primary);
      transform: translateX(2px);
    }}

    .email-actions {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 5px;
      margin-top: 5px;
      padding-top: 5px;
      border-top: 1px solid var(--border-subtle);
    }}

    .action-btn {{
      background: var(--bg-surface);
      border: 1px solid var(--border-default);
      color: var(--text-primary);
      font-family: var(--font-sans);
      font-size: 11px;
      font-weight: 500;
      padding: 3px 8px;
      border-radius: 4px;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: all 180ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .action-btn.icon-only {{
      width: 25px;
      height: 23px;
      padding: 0;
      justify-content: center;
      color: var(--text-secondary);
    }}

    .action-btn.icon-only:hover {{
      color: var(--text-primary);
    }}

    .action-icon {{
      width: 13px;
      height: 13px;
      flex-shrink: 0;
      transition: transform 180ms ease;
    }}

    .action-btn:hover .action-icon {{
      transform: scale(1.1);
    }}

    .action-arrow {{
      font-size: 10px;
      margin-left: 1px;
      transition: transform 180ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .action-btn:hover .action-arrow {{
      transform: translate(1.5px, -1.5px);
    }}

    .action-btn:hover {{
      background: var(--bg-surface-subtle);
      border-color: var(--border-strong);
      transform: translateY(-1px);
    }}

    .action-btn:active {{
      transform: translateY(0) scale(0.93);
    }}

    .action-btn.copied {{
      background: var(--accent-lime);
      color: var(--accent-lime-fg);
      border-color: transparent;
      transform: scale(1.08);
      box-shadow: 0 2px 6px rgba(210, 248, 152, 0.35);
    }}

    .action-btn.gmail-btn {{
      color: var(--text-secondary);
    }}

    .action-btn.gmail-btn:hover {{
      color: var(--text-primary);
    }}

    .gmail-icon {{
      color: #EA4335;
    }}

    :root[data-theme="dark"] .gmail-icon,
    :root[data-theme="system"] .gmail-icon {{
      color: #F87171;
    }}

    /* -------------------------------------------------------------
       Status Dropdown with High-Contrast Dark Mode Support
       ------------------------------------------------------------- */
    .status-select-wrap {{
      position: relative;
      display: inline-flex;
      align-items: center;
      background-color: var(--bg-surface-elevated);
      border: 1px solid var(--border-default);
      border-radius: 4px;
      padding: 2px 6px;
      gap: 5px;
      transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
      color: var(--text-primary);
    }}

    .status-select-wrap:hover {{
      border-color: var(--border-strong);
      transform: translateY(-1px);
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }}

    .status-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      flex-shrink: 0;
      display: inline-block;
      transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1), background-color 200ms ease;
    }}

    .status-select-wrap:hover .status-dot {{
      transform: scale(1.25);
    }}

    /* Color Dot Codes */
    .status-select-wrap[data-status="To Review"] .status-dot {{
      background-color: #9CA3AF;
    }}
    .status-select-wrap[data-status="Applied"] .status-dot {{
      background-color: #84CC16;
    }}
    .status-select-wrap[data-status="Interviewing"] .status-dot {{
      background-color: #F59E0B;
    }}
    .status-select-wrap[data-status="Offer"] .status-dot {{
      background-color: #10B981;
    }}
    .status-select-wrap[data-status="Rejected"] .status-dot {{
      background-color: #EF4444;
    }}

    .status-select {{
      appearance: none;
      -webkit-appearance: none;
      font-family: var(--font-sans);
      font-size: 11.5px;
      font-weight: 500;
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
      outline: none;
      padding-right: 14px;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8' viewBox='0 0 24 24' fill='none' stroke='%238E9684' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 2px center;
      color-scheme: light dark;
    }}

    .status-select option {{
      background-color: var(--bg-surface-elevated);
      color: var(--text-primary);
    }}

    /* Light Theme Tints */
    :root[data-theme="light"] .status-select-wrap[data-status="Applied"] {{
      background-color: rgba(210, 248, 152, 0.22);
      border-color: rgba(210, 248, 152, 0.6);
      color: #142403;
    }}

    :root[data-theme="light"] .status-select-wrap[data-status="Interviewing"] {{
      background-color: rgba(246, 249, 48, 0.22);
      border-color: rgba(246, 249, 48, 0.6);
      color: #2E2F00;
    }}

    :root[data-theme="light"] .status-select-wrap[data-status="Offer"] {{
      background-color: var(--accent-lime);
      border-color: transparent;
      color: var(--accent-lime-fg);
    }}

    :root[data-theme="light"] .status-select-wrap[data-status="Offer"] .status-select {{
      color: var(--accent-lime-fg);
      font-weight: 600;
    }}

    /* Dark Theme Tints */
    :root[data-theme="dark"] .status-select-wrap[data-status="Applied"],
    :root[data-theme="system"] .status-select-wrap[data-status="Applied"] {{
      background-color: rgba(210, 248, 152, 0.16);
      border-color: rgba(210, 248, 152, 0.45);
      color: #D2F898;
    }}

    :root[data-theme="dark"] .status-select-wrap[data-status="Interviewing"],
    :root[data-theme="system"] .status-select-wrap[data-status="Interviewing"] {{
      background-color: rgba(246, 249, 48, 0.16);
      border-color: rgba(246, 249, 48, 0.45);
      color: #F6F930;
    }}

    :root[data-theme="dark"] .status-select-wrap[data-status="Offer"],
    :root[data-theme="system"] .status-select-wrap[data-status="Offer"] {{
      background-color: #D2F898;
      border-color: transparent;
      color: #0E100D;
    }}

    :root[data-theme="dark"] .status-select-wrap[data-status="Offer"] .status-select,
    :root[data-theme="system"] .status-select-wrap[data-status="Offer"] .status-select {{
      color: #0E100D;
      font-weight: 600;
    }}

    :root[data-theme="dark"] .status-select-wrap[data-status="Rejected"],
    :root[data-theme="system"] .status-select-wrap[data-status="Rejected"] {{
      background-color: rgba(239, 68, 68, 0.14);
      border-color: rgba(239, 68, 68, 0.4);
      color: #F87171;
    }}

    :root[data-theme="dark"] .status-select option,
    :root[data-theme="system"] .status-select option {{
      background-color: #1D211A;
      color: #F7F9F5;
    }}

    :root[data-theme="light"] .status-select option {{
      background-color: #FFFFFF;
      color: #121212;
    }}

    .empty-row {{
      text-align: center;
      padding: 48px 16px;
      color: var(--text-muted);
      font-size: 13px;
      animation: rowReveal 240ms cubic-bezier(0.16, 1, 0.3, 1) both;
    }}

    /* Find Jobs Button */
    .find-jobs-btn {{
      height: 32px;
      background-color: var(--accent-lime);
      color: var(--accent-lime-fg);
      border: 1px solid rgba(0, 0, 0, 0.14);
      border-radius: 6px;
      padding: 0 12px;
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
      white-space: nowrap;
    }}

    .find-jobs-btn:hover {{
      transform: translateY(-1.5px);
      box-shadow: 0 3px 8px rgba(210, 248, 152, 0.4);
      filter: brightness(1.05);
    }}

    .find-jobs-btn:active {{
      transform: translateY(0) scale(0.96);
    }}

    .find-jobs-btn .btn-icon {{
      width: 14px;
      height: 14px;
      transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .find-jobs-btn:hover .btn-icon {{
      transform: rotate(45deg) scale(1.15);
    }}

    /* Modal Backdrop & Window */
    .modal-backdrop {{
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background-color: rgba(14, 16, 13, 0.7);
      backdrop-filter: blur(5px);
      -webkit-backdrop-filter: blur(5px);
      z-index: 1000;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      opacity: 0;
      visibility: hidden;
      transition: opacity 220ms cubic-bezier(0.16, 1, 0.3, 1), visibility 220ms ease;
    }}

    .modal-backdrop.open {{
      opacity: 1;
      visibility: visible;
    }}

    .modal-window {{
      background-color: var(--bg-surface);
      border: 1px solid var(--border-default);
      border-radius: 10px;
      max-width: 860px;
      width: 100%;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 20px 48px rgba(0, 0, 0, 0.35);
      transform: scale(0.95) translateY(8px);
      transition: transform 220ms cubic-bezier(0.16, 1, 0.3, 1);
      overflow: hidden;
    }}

    .modal-backdrop.open .modal-window {{
      transform: scale(1) translateY(0);
    }}

    .modal-header {{
      padding: 14px 20px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background-color: var(--bg-surface-elevated);
      flex-shrink: 0;
    }}

    .modal-title-wrap {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .modal-badge-icon {{
      width: 28px;
      height: 28px;
      background: var(--accent-lime);
      color: var(--accent-lime-fg);
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .modal-title {{
      font-size: 15px;
      font-weight: 600;
      color: var(--text-primary);
      letter-spacing: -0.01em;
    }}

    .modal-subtitle {{
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 1px;
    }}

    .modal-close-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 20px;
      line-height: 1;
      width: 28px;
      height: 28px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 150ms ease;
    }}

    .modal-close-btn:hover {{
      background: var(--bg-surface-subtle);
      color: var(--text-primary);
    }}

    .modal-body {{
      padding: 18px 20px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .form-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }}

    @media (max-width: 680px) {{
      .form-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .form-field {{
      display: flex;
      flex-direction: column;
      gap: 5px;
    }}

    .form-field.full-width {{
      grid-column: 1 / -1;
    }}

    .field-label {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-secondary);
    }}

    .field-select,
    .field-input,
    .field-textarea {{
      width: 100%;
      height: 32px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-default);
      border-radius: 6px;
      padding: 0 10px;
      font-family: var(--font-sans);
      font-size: 12px;
      color: var(--text-primary);
      outline: none;
      transition: border-color 150ms ease, box-shadow 150ms ease, background-color 150ms ease;
    }}

    .field-select:focus,
    .field-input:focus,
    .field-textarea:focus {{
      border-color: var(--border-strong);
      box-shadow: 0 0 0 2px rgba(210, 248, 152, 0.35);
      background-color: var(--bg-surface);
    }}

    .field-textarea {{
      height: 85px;
      padding: 8px 10px;
      font-family: var(--font-mono);
      font-size: 11px;
      line-height: 1.45;
      resize: vertical;
    }}

    .field-hint {{
      font-size: 10.5px;
      color: var(--text-muted);
      margin-top: 2px;
    }}

    .field-label-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }}

    .field-hint-inline {{
      font-size: 10.5px;
      color: var(--text-muted);
    }}

    /* Toggle Groups (Multi-Select Pills) */
    .toggle-group {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
    }}

    .toggle-btn {{
      height: 28px;
      padding: 0 11px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 500;
      font-family: var(--font-sans);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-default);
      color: var(--text-secondary);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 150ms cubic-bezier(0.16, 1, 0.3, 1);
      user-select: none;
      white-space: nowrap;
    }}

    .toggle-btn:hover {{
      border-color: var(--border-strong);
      color: var(--text-primary);
    }}

    .toggle-btn.selected {{
      background-color: var(--accent-lime);
      color: #0E100D;
      border-color: rgba(0, 0, 0, 0.16);
      font-weight: 600;
      box-shadow: 0 1px 4px rgba(210, 248, 152, 0.3);
    }}

    .toggle-btn.selected:hover {{
      filter: brightness(1.04);
    }}

    :root[data-theme="dark"] .toggle-btn.selected,
    :root[data-theme="system"] .toggle-btn.selected {{
      color: #0E100D;
    }}

    /* Salary Range Composite Controls */
    .salary-range-wrap {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }}

    .salary-range-inputs {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .salary-num-input {{
      width: 115px !important;
      font-family: var(--font-mono) !important;
      font-size: 11.5px !important;
    }}

    .salary-to-label {{
      font-size: 11px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: lowercase;
    }}

    .salary-select-currency {{
      width: 100px !important;
      font-size: 11.5px !important;
    }}

    .salary-select-period {{
      width: 120px !important;
      font-size: 11.5px !important;
    }}

    .salary-info-btn {{
      height: 32px;
      width: 32px;
      border-radius: 6px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-default);
      color: var(--text-muted);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 160ms ease;
      flex-shrink: 0;
    }}

    .salary-info-btn:hover,
    .salary-info-btn.active {{
      background: var(--bg-surface);
      border-color: var(--border-strong);
      color: var(--text-primary);
    }}

    .salary-info-btn.has-values {{
      border-color: var(--accent-lime);
      color: var(--text-primary);
      box-shadow: 0 0 0 1px rgba(210, 248, 152, 0.35);
    }}

    .salary-quick-hint {{
      font-size: 11px;
      color: var(--text-muted);
      font-family: var(--font-mono);
      min-height: 16px;
      margin-top: 3px;
    }}

    .salary-conversion-panel {{
      display: none;
      background: var(--bg-canvas);
      border: 1px solid var(--border-default);
      border-radius: 8px;
      padding: 12px;
      margin-top: 6px;
      animation: rowReveal 180ms ease both;
    }}

    .salary-conversion-panel.open {{
      display: block;
    }}

    .conv-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
      padding-bottom: 6px;
      border-bottom: 1px solid var(--border-subtle);
    }}

    .conv-title {{
      font-size: 11px;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .conv-rate {{
      font-size: 10px;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }}

    .conv-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
    }}

    @media (max-width: 680px) {{
      .conv-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .conv-card {{
      background: var(--bg-surface);
      border: 1px solid var(--border-default);
      border-radius: 6px;
      padding: 8px 10px;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}

    .conv-card.highlight {{
      border-color: var(--accent-lime);
      background: rgba(210, 248, 152, 0.06);
    }}

    .conv-card-title {{
      font-size: 10.5px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}

    .conv-val-main {{
      font-size: 13px;
      font-weight: 600;
      font-family: var(--font-mono);
      color: var(--text-primary);
    }}

    .conv-val-sub {{
      font-size: 10.5px;
      font-family: var(--font-mono);
      color: var(--text-secondary);
    }}

    /* Prompt Preview Box */
    .prompt-preview-wrap {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .prompt-preview-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .prompt-preview-label {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-secondary);
    }}

    .prompt-preview-sub {{
      font-size: 10.5px;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }}

    .prompt-preview-box {{
      width: 100%;
      height: 160px;
      background: var(--bg-canvas);
      border: 1px solid var(--border-default);
      border-radius: 6px;
      padding: 10px;
      font-family: var(--font-mono);
      font-size: 11px;
      line-height: 1.45;
      color: var(--text-secondary);
      white-space: pre-wrap;
      overflow-y: auto;
      user-select: text;
    }}

    /* Modal Footer */
    .modal-footer {{
      padding: 12px 20px;
      border-top: 1px solid var(--border-subtle);
      background-color: var(--bg-surface-elevated);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-shrink: 0;
    }}

    .modal-footer-hint {{
      font-size: 11px;
      color: var(--text-muted);
    }}

    .modal-footer-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .btn-modal-cancel {{
      background: var(--bg-surface);
      border: 1px solid var(--border-default);
      color: var(--text-secondary);
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 500;
      padding: 5px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 150ms ease;
    }}

    .btn-modal-cancel:hover {{
      background: var(--bg-surface-subtle);
      color: var(--text-primary);
      border-color: var(--border-strong);
    }}

    .btn-copy-prompt {{
      background-color: var(--accent-lime);
      color: var(--accent-lime-fg);
      border: 1px solid rgba(0, 0, 0, 0.12);
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 600;
      padding: 5px 14px;
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 180ms cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .btn-copy-prompt:hover {{
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(210, 248, 152, 0.4);
      filter: brightness(1.05);
    }}

    .btn-copy-prompt:active {{
      transform: translateY(0) scale(0.97);
    }}

    .btn-copy-prompt.copied {{
      background-color: var(--accent-lemon);
      color: var(--accent-lemon-fg);
      transform: scale(1.04);
    }}

    /* Filter Toolbar Additions */
    .filter-separator {{
      width: 1px;
      height: 16px;
      background-color: var(--border-default);
      margin: 0 4px;
    }}

    .filter-select-wrap {{
      position: relative;
      display: inline-flex;
      align-items: center;
    }}

    .filter-select {{
      height: 26px;
      background: var(--bg-surface);
      border: 1px solid var(--border-default);
      border-radius: 4px;
      font-family: var(--font-sans);
      font-size: 11px;
      font-weight: 500;
      color: var(--text-secondary);
      padding: 0 20px 0 8px;
      cursor: pointer;
      outline: none;
      appearance: none;
      -webkit-appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8' viewBox='0 0 24 24' fill='none' stroke='%238E9684' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 6px center;
      transition: all 150ms ease;
    }}

    .filter-select:hover {{
      border-color: var(--border-strong);
      color: var(--text-primary);
    }}

    :root[data-theme="dark"] .filter-select option,
    :root[data-theme="system"] .filter-select option {{
      background-color: #1D211A;
      color: #F7F9F5;
    }}

    :root[data-theme="light"] .filter-select option {{
      background-color: #FFFFFF;
      color: #121212;
    }}


    /* Advanced Table Filters Toolbar (Work Setup, Employment Type, Salary Range) */
    .table-advanced-filters {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      padding-top: 6px;
      border-top: 1px solid var(--border-subtle);
      position: relative;
    }}

    .table-filter-item {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}

    .table-toggle-group {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      flex-wrap: wrap;
    }}

    .table-toggle-btn {{
      height: 25px;
      padding: 0 9px;
      border-radius: 5px;
      font-size: 11px;
      font-weight: 500;
      font-family: var(--font-sans);
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-default);
      color: var(--text-secondary);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 150ms cubic-bezier(0.16, 1, 0.3, 1);
      user-select: none;
      white-space: nowrap;
    }}

    .table-toggle-btn:hover {{
      border-color: var(--border-strong);
      color: var(--text-primary);
      transform: translateY(-0.5px);
    }}

    .table-toggle-btn.selected {{
      background-color: var(--accent-lime);
      color: #0E100D;
      border-color: rgba(0, 0, 0, 0.16);
      font-weight: 600;
      box-shadow: 0 1px 3px rgba(210, 248, 152, 0.25);
    }}

    :root[data-theme="dark"] .table-toggle-btn.selected,
    :root[data-theme="system"] .table-toggle-btn.selected {{
      color: #0E100D;
    }}

    .table-salary-filter-item {{
      position: relative;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}

    .table-salary-range-wrap {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}

    .table-salary-inputs {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}

    .table-salary-input {{
      width: 78px !important;
      height: 26px !important;
      font-size: 11px !important;
      font-family: var(--font-mono) !important;
      padding: 0 6px !important;
      background: var(--bg-surface);
      border: 1px solid var(--border-default);
      border-radius: 4px;
      color: var(--text-primary);
      outline: none;
      transition: border-color 150ms ease, box-shadow 150ms ease;
    }}

    .table-salary-input:hover {{
      border-color: var(--border-strong);
    }}

    .table-salary-input:focus {{
      border-color: var(--border-strong);
      box-shadow: 0 0 0 2px rgba(210, 248, 152, 0.35);
    }}

    .table-salary-to {{
      font-size: 10.5px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: lowercase;
    }}

    .table-salary-select {{
      height: 26px !important;
      font-size: 11px !important;
      padding: 0 18px 0 6px !important;
      background: var(--bg-surface);
      border: 1px solid var(--border-default);
      border-radius: 4px;
      color: var(--text-secondary);
      font-family: var(--font-sans);
      font-weight: 500;
      cursor: pointer;
      outline: none;
      appearance: none;
      -webkit-appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8' viewBox='0 0 24 24' fill='none' stroke='%238E9684' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 5px center;
      transition: all 150ms ease;
    }}

    .table-salary-select:hover {{
      border-color: var(--border-strong);
      color: var(--text-primary);
    }}

    :root[data-theme="dark"] .table-salary-select option,
    :root[data-theme="system"] .table-salary-select option {{
      background-color: #1D211A;
      color: #F7F9F5;
    }}

    :root[data-theme="light"] .table-salary-select option {{
      background-color: #FFFFFF;
      color: #121212;
    }}

    .table-salary-info-btn {{
      height: 26px;
      width: 26px;
      border-radius: 4px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-default);
      color: var(--text-muted);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 150ms ease;
      flex-shrink: 0;
    }}

    .table-salary-info-btn:hover,
    .table-salary-info-btn.active {{
      background: var(--bg-surface);
      border-color: var(--border-strong);
      color: var(--text-primary);
    }}

    .table-salary-info-btn.has-values {{
      border-color: var(--accent-lime);
      color: var(--text-primary);
      box-shadow: 0 0 0 1px rgba(210, 248, 152, 0.4);
    }}

    .table-salary-popover {{
      position: absolute;
      top: calc(100% + 6px);
      left: 0;
      z-index: 100;
      min-width: 320px;
      max-width: 420px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
      border-color: var(--border-strong);
    }}

    .table-filters-reset-btn {{
      height: 25px;
      padding: 0 8px;
      border-radius: 4px;
      background: transparent;
      border: 1px dashed var(--border-default);
      color: var(--text-muted);
      font-size: 10.5px;
      font-family: var(--font-sans);
      font-weight: 500;
      cursor: pointer;
      display: none;
      align-items: center;
      transition: all 160ms ease;
    }}

    .table-filters-reset-btn:hover {{
      border-color: #EF4444;
      color: #EF4444;
      background: rgba(239, 68, 68, 0.08);
    }}

  </style>
</head>
<body>
  <div class="container">
    <!-- Sticky Top Panel: Header, Search, Filters, Download CSV -->
    <div class="sticky-top-panel">
      <!-- Header -->
      <header>
        <div class="brand">
          <div class="brand-mark" aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 32 32" fill="none">
              <path d="M10 10 L16 16 L10 22" stroke="var(--accent-lime)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="17" y1="22" x2="22" y2="22" stroke="var(--accent-lemon)" stroke-width="3" stroke-linecap="round"/>
            </svg>
          </div>
          <h1>Job Hunting</h1>
        </div>
        <button class="theme-toggle-btn" id="theme-toggle" aria-label="Toggle visual theme">
          <!-- Sun icon (for dark mode) -->
          <svg id="icon-sun" class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: none;">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
          </svg>
          <!-- Moon icon (for light mode) -->
          <svg id="icon-moon" class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
          </svg>
        </button>
      </header>

      <!-- Toolbar: Search, Tier, Download & Status Filter with Color Codes -->
      <div class="toolbar-container">
        <div class="toolbar-main">
          <div class="toolbar-left">
            <div class="search-box">
              <input
                type="text"
                id="search-input"
                class="search-input"
                placeholder="Search by company, role, skill, domain, or salary..."
                autocomplete="off"
              >
            </div>
            <div class="segmented-control tier-segmented-control" role="group" aria-label="Filter by tier">
              <button class="seg-btn active" data-filter="all">All ({total_count})</button>
              <button class="seg-btn seg-target" data-filter="Target">
                <span class="tier-filter-dot dot-target"></span>
                <span>Target ({target_count})</span>
              </button>
              <button class="seg-btn seg-stretch" data-filter="Stretch">
                <span class="tier-filter-dot dot-stretch"></span>
                <span>Stretch ({stretch_count})</span>
              </button>
            </div>

          </div>
          <div class="toolbar-right">
            <button class="find-jobs-btn" id="open-find-jobs-modal" onclick="openFindJobsModal()" aria-label="Find new jobs with automated pipeline prompt">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="11" cy="11" r="7"></circle>
                <line x1="21" y1="21" x2="16" y2="16"></line>
                <line x1="11" y1="8" x2="11" y2="14"></line>
                <line x1="8" y1="11" x2="14" y2="11"></line>
              </svg>
              <span>Find Jobs</span>
            </button>
            <button class="export-csv-btn" onclick="exportUpdatedCsv()" aria-label="Download updated CSV file">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              <span>Download CSV</span>
            </button>
          </div>
        </div>

        <!-- Status Filter Tabs with Dynamic Counts and Matching Color Dots -->
        <div class="status-filter-bar" id="status-filter-bar" role="group" aria-label="Filter by status">
          <span class="filter-label">Status:</span>
          <button class="status-filter-btn active" data-status="all">
            <span class="status-dot dot-all"></span>
            <span>All</span> <span class="filter-count" id="count-status-all">({total_count})</span>
          </button>
          <button class="status-filter-btn" data-status="To Review">
            <span class="status-dot dot-to-review"></span>
            <span>To Review</span> <span class="filter-count" id="count-status-to-review">(0)</span>
          </button>
          <button class="status-filter-btn" data-status="Applied">
            <span class="status-dot dot-applied"></span>
            <span>Applied</span> <span class="filter-count" id="count-status-applied">(0)</span>
          </button>
          <button class="status-filter-btn" data-status="Interviewing">
            <span class="status-dot dot-interviewing"></span>
            <span>Interviewing</span> <span class="filter-count" id="count-status-interviewing">(0)</span>
          </button>
          <button class="status-filter-btn" data-status="Offer">
            <span class="status-dot dot-offer"></span>
            <span>Offer</span> <span class="filter-count" id="count-status-offer">(0)</span>
          </button>
          <button class="status-filter-btn" data-status="Rejected">
            <span class="status-dot dot-rejected"></span>
            <span>Rejected</span> <span class="filter-count" id="count-status-rejected">(0)</span>
          </button>

          <div class="filter-separator" aria-hidden="true"></div>

          <!-- Target Board / Source Filter -->
          <span class="filter-label">Board:</span>
          <div class="filter-select-wrap">
            <select id="source-filter-select" class="filter-select" aria-label="Filter by target job board">
              <option value="all">All Portals</option>
              <option value="Himalayas">Himalayas</option>
              <option value="Wellfound">Wellfound</option>
              <option value="Y Combinator">Y Combinator</option>
              <option value="We Work Remotely">We Work Remotely</option>
            </select>
          </div>
        </div>

        <!-- Table Filters: Setup, Type, and Salary Range in Same Format as Modal -->
        <div class="table-advanced-filters" id="table-advanced-filters" role="region" aria-label="Table filters">
          <!-- Work Setup Toggle Group -->
          <div class="table-filter-item">
            <span class="filter-label">Setup:</span>
            <div class="toggle-group table-toggle-group" id="table-group-work-setup" data-group="table-work-setup">
              <button type="button" class="toggle-btn table-toggle-btn selected" data-val="Any">Any</button>
              <button type="button" class="toggle-btn table-toggle-btn" data-val="Worldwide">Remote (Worldwide)</button>
              <button type="button" class="toggle-btn table-toggle-btn" data-val="APAC / Philippines">Remote (APAC / Philippines)</button>
              <button type="button" class="toggle-btn table-toggle-btn" data-val="Contractor / B2B">Contractor / B2B / Deel</button>
            </div>
          </div>

          <div class="filter-separator" aria-hidden="true"></div>

          <!-- Employment Type Toggle Group -->
          <div class="table-filter-item">
            <span class="filter-label">Type:</span>
            <div class="toggle-group table-toggle-group" id="table-group-employment-type" data-group="table-employment-type">
              <button type="button" class="toggle-btn table-toggle-btn selected" data-val="Any">Any</button>
              <button type="button" class="toggle-btn table-toggle-btn" data-val="Full-Time">Full-Time</button>
              <button type="button" class="toggle-btn table-toggle-btn" data-val="Contract / B2B">Contract / B2B</button>
              <button type="button" class="toggle-btn table-toggle-btn" data-val="Part-Time">Part-Time</button>
            </div>
          </div>

          <div class="filter-separator" aria-hidden="true"></div>

          <!-- Salary Range Composite Filter -->
          <div class="table-salary-filter-item">
            <span class="filter-label">Salary:</span>
            <div class="salary-range-wrap table-salary-range-wrap">
              <div class="salary-range-inputs table-salary-inputs">
                <input
                  type="text"
                  id="table-filter-salary-min"
                  class="field-input salary-num-input table-salary-input"
                  placeholder="Min"
                  autocomplete="off"
                  aria-label="Table filter minimum salary"
                >
                <span class="salary-to-label table-salary-to">to</span>
                <input
                  type="text"
                  id="table-filter-salary-max"
                  class="field-input salary-num-input table-salary-input"
                  placeholder="Max"
                  autocomplete="off"
                  aria-label="Table filter maximum salary"
                >
              </div>

              <select id="table-filter-salary-currency" class="field-select salary-select-currency table-salary-select" aria-label="Table filter salary currency">
                <option value="USD" selected>USD ($)</option>
                <option value="PHP">PHP (₱)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
                <option value="AUD">AUD (A$)</option>
                <option value="CAD">CAD (C$)</option>
                <option value="SGD">SGD (S$)</option>
              </select>

              <select id="table-filter-salary-period" class="field-select salary-select-period table-salary-select" aria-label="Table filter salary frequency">
                <option value="yearly" selected>Yearly (/yr)</option>
                <option value="monthly">Monthly (/mo)</option>
                <option value="hourly">Hourly (/hr)</option>
              </select>

              <button
                type="button"
                id="table-salary-info-toggle"
                class="salary-info-btn table-salary-info-btn"
                onclick="toggleTableSalaryConversionPanel()"
                title="View currency and period conversions"
                aria-label="View currency and period conversions"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="16" x2="12" y2="12"></line>
                  <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
              </button>

              <button
                type="button"
                id="table-filters-reset-btn"
                class="table-filters-reset-btn"
                onclick="resetTableAdvancedFilters()"
                title="Reset all active table filters"
                aria-label="Reset all active table filters"
              >
                Reset
              </button>
            </div>

            <!-- Expandable Popover for Table Salary Conversions -->
            <div id="table-salary-conversion-panel" class="salary-conversion-panel table-salary-popover">
              <!-- Populated dynamically via JS -->
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Data Table Container with Sticky Header & Distinct Dividing Lines -->
    <div class="table-container">
      <table id="pipeline-table">
        <thead id="table-head">
          <!-- Populated dynamically with draggable/reorderable/resizable headers -->
        </thead>
        <tbody id="table-body">
          <!-- Populated dynamically -->
        </tbody>
      </table>
    </div>
  </div>


<!-- Find Jobs Modal -->
  <div class="modal-backdrop" id="find-jobs-modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <div class="modal-window">
      <div class="modal-header">
        <div class="modal-title-wrap">
          <div class="modal-badge-icon" aria-hidden="true">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="7"></circle>
              <line x1="21" y1="21" x2="16" y2="16"></line>
            </svg>
          </div>
          <div>
            <div class="modal-title" id="modal-title">Find Remote Jobs Pipeline</div>
            <div class="modal-subtitle">Configure search parameters and generate an automated /browser agent prompt.</div>
          </div>
        </div>
        <button class="modal-close-btn" onclick="closeFindJobsModal()" aria-label="Close dialog">×</button>
      </div>

      <div class="modal-body">
        <!-- 1. Salary Range Input to Input with Currency & Period Dropdowns + Info Conversion Button -->
        <div class="form-field full-width">
          <div class="field-label-row">
            <label class="field-label" for="param-salary-min">Salary Range</label>
            <span class="field-hint-inline">Leave blank for Any compensation</span>
          </div>
          <div class="salary-range-wrap">
            <div class="salary-range-inputs">
              <input
                type="text"
                id="param-salary-min"
                class="field-input salary-num-input"
                placeholder="Min (e.g. 70000)"
                autocomplete="off"
              >
              <span class="salary-to-label">to</span>
              <input
                type="text"
                id="param-salary-max"
                class="field-input salary-num-input"
                placeholder="Max (e.g. 120000)"
                autocomplete="off"
              >
            </div>

            <select id="param-salary-currency" class="field-select salary-select-currency" aria-label="Salary currency">
              <option value="USD" selected>USD ($)</option>
              <option value="PHP">PHP (₱)</option>
              <option value="EUR">EUR (€)</option>
              <option value="GBP">GBP (£)</option>
              <option value="AUD">AUD (A$)</option>
              <option value="CAD">CAD (C$)</option>
              <option value="SGD">SGD (S$)</option>
            </select>

            <select id="param-salary-period" class="field-select salary-select-period" aria-label="Salary frequency">
              <option value="yearly" selected>Yearly (/yr)</option>
              <option value="monthly">Monthly (/mo)</option>
              <option value="hourly">Hourly (/hr)</option>
            </select>

            <button
              type="button"
              id="salary-info-toggle"
              class="salary-info-btn"
              onclick="toggleSalaryConversionPanel()"
              title="View currency and period conversions"
              aria-label="View currency and period conversions"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
            </button>
          </div>

          <!-- Quick conversion inline hint -->
          <div id="salary-quick-hint" class="salary-quick-hint"></div>

          <!-- Expandable detailed conversions panel -->
          <div id="salary-conversion-panel" class="salary-conversion-panel">
            <!-- Populated dynamically via JS -->
          </div>
        </div>

        <!-- 2. Work Setup Toggle Group (Multi-Select with Any Exclusive) -->
        <div class="form-field full-width">
          <div class="field-label-row">
            <span class="field-label">Work Setup</span>
            <span class="field-hint-inline">Multi-select ('Any' clears others)</span>
          </div>
          <div class="toggle-group" id="group-work-setup" data-group="work-setup">
            <button type="button" class="toggle-btn selected" data-val="Any">Any</button>
            <button type="button" class="toggle-btn" data-val="Worldwide">Remote (Worldwide)</button>
            <button type="button" class="toggle-btn" data-val="APAC / Philippines">Remote (APAC / Philippines)</button>
            <button type="button" class="toggle-btn" data-val="Contractor / B2B">Contractor / B2B / Deel</button>
          </div>
        </div>

        <!-- 3. Seniority Level Toggle Group (Multi-Select with Any Exclusive) -->
        <div class="form-field full-width">
          <div class="field-label-row">
            <span class="field-label">Seniority Level</span>
            <span class="field-hint-inline">Multi-select ('Any' clears others)</span>
          </div>
          <div class="toggle-group" id="group-seniority" data-group="seniority">
            <button type="button" class="toggle-btn selected" data-val="Any">Any</button>
            <button type="button" class="toggle-btn" data-val="Target Tier (Junior / Entry 0-2 YOE)">Target (Junior / Entry 0-2 YOE)</button>
            <button type="button" class="toggle-btn" data-val="Stretch Tier (Software Engineer 2-3 YOE)">Stretch (SWE 2-3 YOE)</button>
            <button type="button" class="toggle-btn" data-val="Senior (3+ YOE)">Senior (3+ YOE)</button>
          </div>
        </div>

        <!-- 4. Employment Type Toggle Group (Multi-Select with Any Exclusive) -->
        <div class="form-field full-width">
          <div class="field-label-row">
            <span class="field-label">Employment Type</span>
            <span class="field-hint-inline">Multi-select ('Any' clears others)</span>
          </div>
          <div class="toggle-group" id="group-employment-type" data-group="employment-type">
            <button type="button" class="toggle-btn selected" data-val="Any">Any</button>
            <button type="button" class="toggle-btn" data-val="Full-Time">Full-Time</button>
            <button type="button" class="toggle-btn" data-val="Contract / B2B">Contract / B2B</button>
            <button type="button" class="toggle-btn" data-val="Part-Time">Part-Time</button>
          </div>
        </div>

        <!-- 5. Target Titles & Leads Count Grid -->
        <div class="form-grid">
          <div class="form-field">
            <label class="field-label" for="param-roles">Role Profiles / Target Titles</label>
            <input
              type="text"
              id="param-roles"
              class="field-input"
              value="Backend Engineer, Full Stack Engineer, Systems Engineer, Junior SWE, Web Developer"
              placeholder="e.g. Backend, Full Stack, Systems, Junior SWE"
            >
          </div>

          <div class="form-field">
            <label class="field-label" for="param-count">Target Fresh Leads Count</label>
            <select id="param-count" class="field-select">
              <option value="25" selected>25 Leads (Recommended)</option>
              <option value="15">15 Leads (Quick Run)</option>
              <option value="35">35 Leads</option>
              <option value="50">50 Leads (Deep Search)</option>
            </select>
          </div>
        </div>

        <!-- 6. Job Sites Textarea -->
        <div class="form-field full-width">
          <div class="field-label-row">
            <label class="field-label" for="param-sites">Job-Seeking Sites & Portals (Scrollable / Editable)</label>
            <span class="field-hint-inline">One URL per line</span>
          </div>
          <textarea id="param-sites" class="field-textarea" placeholder="Enter portal URLs, one per line...">https://himalayas.app/jobs?remote_location=Anywhere
https://wellfound.com/jobs
https://www.workatastartup.com/companies
https://weworkremotely.com/categories/remote-back-end-programming-jobs
https://remoteok.com/remote-dev-jobs
https://jobspresso.co/remote-software-jobs/
https://boards.greenhouse.io
https://jobs.lever.co
https://jobs.ashbyhq.com</textarea>
        </div>

        <!-- Generated Prompt Live Preview -->
        <div class="prompt-preview-wrap">
          <div class="prompt-preview-header">
            <span class="prompt-preview-label">Generated Agent Automation Prompt</span>
            <span class="prompt-preview-sub">Starts with /browser</span>
          </div>
          <pre class="prompt-preview-box" id="prompt-preview-box"></pre>
        </div>
      </div>

      <div class="modal-footer">
        <div class="modal-footer-hint">
          <span>Tip: Click Copy Prompt, then paste into Antigravity chat to trigger the search.</span>
        </div>
        <div class="modal-footer-actions">
          <button class="btn-modal-cancel" onclick="closeFindJobsModal()">Close</button>
          <button class="btn-copy-prompt" id="copy-prompt-btn" onclick="copyGeneratedPrompt()">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            <span>Copy Prompt</span>
          </button>
        </div>
      </div>
    </div>
  </div>

  <script>
    const initialJobs = {jobs_json};

    // Load persisted status overrides from localStorage
    const STATUS_STORAGE_KEY = 'job_hunting_status_overrides';
    const statusOverrides = JSON.parse(localStorage.getItem(STATUS_STORAGE_KEY) || '{{}}');

    // Merge status overrides into jobs array
    const jobs = initialJobs.map(j => {{
      if (statusOverrides[j.id]) {{
        j.status = statusOverrides[j.id];
      }}
      return j;
    }});

    // Column Definitions (7 Clean Columns: Merged Contact & Outreach, Cover Letter PDF in Listing & Docs)
    const COLUMNS = {{
      tier: {{ id: 'tier', title: 'Tier & Match', defaultWidth: 125, sortable: true }},
      company: {{ id: 'company', title: 'Company & Role', defaultWidth: 260, sortable: true }},
      salary: {{ id: 'salary', title: 'Salary', defaultWidth: 140, sortable: true }},
      date: {{ id: 'date', title: 'Posted', defaultWidth: 95, sortable: true }},
      listing: {{ id: 'listing', title: 'Listing & Docs', defaultWidth: 215, sortable: false }},
      outreach: {{ id: 'outreach', title: 'Contact & Outreach', defaultWidth: 460, sortable: false }},
      status: {{ id: 'status', title: 'Status', defaultWidth: 140, sortable: true }}
    }};

    const DEFAULT_COL_ORDER = ['tier', 'company', 'salary', 'date', 'listing', 'outreach', 'status'];

    // Load persisted column order and widths from localStorage
    const COL_ORDER_KEY = 'job_hunting_col_order';
    const COL_WIDTHS_KEY = 'job_hunting_col_widths';

    let colOrder = JSON.parse(localStorage.getItem(COL_ORDER_KEY) || 'null');
    if (!Array.isArray(colOrder) || colOrder.length !== DEFAULT_COL_ORDER.length || !colOrder.every(c => COLUMNS[c]) || colOrder.includes('contact') || colOrder.includes('cover_letter')) {{
      colOrder = [...DEFAULT_COL_ORDER];
      localStorage.setItem(COL_ORDER_KEY, JSON.stringify(colOrder));
    }}

    let colWidths = JSON.parse(localStorage.getItem(COL_WIDTHS_KEY) || 'null');
    if (!colWidths || typeof colWidths !== 'object' || !colWidths['outreach'] || colWidths['contact'] || colWidths['cover_letter']) {{
      colWidths = {{}};
      DEFAULT_COL_ORDER.forEach(c => {{
        colWidths[c] = COLUMNS[c].defaultWidth;
      }});
      localStorage.setItem(COL_WIDTHS_KEY, JSON.stringify(colWidths));
    }}
    if (!colWidths['listing'] || colWidths['listing'] < 200) {{
      colWidths['listing'] = 215;
    }}
    if (!colWidths['outreach'] || colWidths['outreach'] < 380) {{
      colWidths['outreach'] = 460;
    }}

    let activeTierFilter = 'all';
    let activeStatusFilter = 'all';
    let activeSalaryFilter = 'all';
    let activeSourceFilter = 'all';
    let searchQuery = '';
    let sortColumn = 'match_score';
    let sortDirection = 'desc'; // 'asc' or 'desc'

    // Theme Management with Icons
    const themeToggle = document.getElementById('theme-toggle');
    const iconSun = document.getElementById('icon-sun');
    const iconMoon = document.getElementById('icon-moon');

    function applyTheme(theme) {{
      document.documentElement.setAttribute('data-theme', theme);
      const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      iconSun.style.display = isDark ? 'block' : 'none';
      iconMoon.style.display = isDark ? 'none' : 'block';
      localStorage.setItem('pipeline-theme', theme);
    }}

    const savedTheme = localStorage.getItem('pipeline-theme') || 'system';
    applyTheme(savedTheme);

    themeToggle.addEventListener('click', () => {{
      const current = document.documentElement.getAttribute('data-theme');
      const isDark = current === 'dark' || (current === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      applyTheme(isDark ? 'light' : 'dark');
    }});

    // Parse numeric salary for sorting
    function parseSalaryValue(str) {{
      if (!str || str === 'N/A' || str.toLowerCase() === 'undisclosed') return -1;
      const m = str.match(/\\$\\s*([\\d,]+)/);
      if (m) {{
        return parseInt(m[1].replace(/,/g, ''), 10);
      }}
      return 0;
    }}

    // Parse relative date for sorting
    function parseDateValue(str) {{
      if (!str) return 999;
      const m = str.match(/(\\d+)\\s*([dwmy])/);
      if (m) {{
        const num = parseInt(m[1], 10);
        const unit = m[2];
        if (unit === 'd') return num;
        if (unit === 'w') return num * 7;
        if (unit === 'm') return num * 30;
        if (unit === 'y') return num * 365;
      }}
      return 999;
    }}

    // Update Status Filter Counts Dynamically
    function updateStatusCounts() {{
      const counts = {{
        all: jobs.length,
        'To Review': 0,
        'Applied': 0,
        'Interviewing': 0,
        'Offer': 0,
        'Rejected': 0
      }};

      jobs.forEach(j => {{
        if (counts[j.status] !== undefined) {{
          counts[j.status]++;
        }}
      }});

      document.getElementById('count-status-all').textContent = `(${{counts.all}})`;
      document.getElementById('count-status-to-review').textContent = `(${{counts['To Review']}})`;
      document.getElementById('count-status-applied').textContent = `(${{counts['Applied']}})`;
      document.getElementById('count-status-interviewing').textContent = `(${{counts['Interviewing']}})`;
      document.getElementById('count-status-offer').textContent = `(${{counts['Offer']}})`;
      document.getElementById('count-status-rejected').textContent = `(${{counts['Rejected']}})`;
    }}

    // Header Rendering with Drag & Drop Reordering and Resizing
    const thead = document.getElementById('table-head');
    let draggedCol = null;

    function renderHeader() {{
      thead.innerHTML = '<tr>' + colOrder.map(colId => {{
        const col = COLUMNS[colId];
        const width = colWidths[colId] || col.defaultWidth;
        const isSorted = sortColumn === colId || (colId === 'tier' && sortColumn === 'match_score');
        const arrowChar = (isSorted && sortDirection === 'asc') ? '▲' : '▼';
        const sortedClass = isSorted ? 'sorted' : '';

        return `
          <th
            class="col-header ${{sortedClass}}"
            data-col="${{colId}}"
            draggable="true"
            style="width: ${{width}}px;"
          >
            <div class="th-content">
              <span class="col-title">${{col.title}}</span>
              ${{col.sortable ? `<span class="sort-arrow" id="sort-${{colId}}">${{arrowChar}}</span>` : ''}}
            </div>
            <div class="col-resizer" data-col="${{colId}}"></div>
          </th>
        `;
      }}).join('') + '</tr>';

      attachHeaderEvents();
    }}

    function attachHeaderEvents() {{
      const headers = thead.querySelectorAll('th.col-header');

      headers.forEach(th => {{
        const colId = th.getAttribute('data-col');
        const col = COLUMNS[colId];

        // Click to sort (if not clicking on a resizer)
        th.addEventListener('click', (e) => {{
          if (e.target.classList.contains('col-resizer')) return;
          if (!col.sortable) return;

          if (colId === 'tier') {{
            if (sortColumn === 'match_score') {{
              sortDirection = sortDirection === 'desc' ? 'asc' : 'desc';
            }} else {{
              sortColumn = 'match_score';
              sortDirection = 'desc';
            }}
          }} else if (sortColumn === colId) {{
            sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
          }} else {{
            sortColumn = colId;
            sortDirection = colId === 'salary' || colId === 'match_score' ? 'desc' : 'asc';
          }}
          renderHeader();
          renderTable();
        }});

        // Column Drag and Drop (Reordering)
        th.addEventListener('dragstart', (e) => {{
          if (e.target.classList.contains('col-resizer')) {{
            e.preventDefault();
            return;
          }}
          draggedCol = colId;
          th.classList.add('col-dragging');
          e.dataTransfer.effectAllowed = 'move';
          e.dataTransfer.setData('text/plain', colId);
        }});

        th.addEventListener('dragend', () => {{
          th.classList.remove('col-dragging');
          headers.forEach(h => h.classList.remove('drop-left', 'drop-right'));
        }});

        th.addEventListener('dragover', (e) => {{
          e.preventDefault();
          if (!draggedCol || draggedCol === colId) return;

          const rect = th.getBoundingClientRect();
          const midpoint = rect.left + rect.width / 2;
          headers.forEach(h => h.classList.remove('drop-left', 'drop-right'));

          if (e.clientX < midpoint) {{
            th.classList.add('drop-left');
          }} else {{
            th.classList.add('drop-right');
          }}
        }});

        th.addEventListener('dragleave', () => {{
          th.classList.remove('drop-left', 'drop-right');
        }});

        th.addEventListener('drop', (e) => {{
          e.preventDefault();
          th.classList.remove('drop-left', 'drop-right');
          if (!draggedCol || draggedCol === colId) return;

          const rect = th.getBoundingClientRect();
          const insertBefore = e.clientX < (rect.left + rect.width / 2);

          const fromIdx = colOrder.indexOf(draggedCol);
          colOrder.splice(fromIdx, 1);

          let toIdx = colOrder.indexOf(colId);
          if (!insertBefore) toIdx++;
          colOrder.splice(toIdx, 0, draggedCol);

          draggedCol = null;
          localStorage.setItem(COL_ORDER_KEY, JSON.stringify(colOrder));
          renderHeader();
          renderTable();
        }});
      }});
    }}

    // Global Column Resizing Handler (Supports Resizing from Headers and Any Row)
    const pipelineTable = document.getElementById('pipeline-table');
    pipelineTable.addEventListener('mousedown', (e) => {{
      const resizer = e.target.closest('.col-resizer');
      if (!resizer) return;

      e.stopPropagation();
      e.preventDefault();
      const targetCol = resizer.getAttribute('data-col');
      const th = thead.querySelector(`th[data-col="${{targetCol}}"]`);
      if (!th) return;

      const startX = e.pageX;
      const startWidth = th.offsetWidth;
      resizer.classList.add('resizing');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';

      // Highlight resizers in this column
      document.querySelectorAll(`.col-resizer[data-col="${{targetCol}}"]`).forEach(r => r.classList.add('resizing'));

      function onMouseMove(eMove) {{
        const diff = eMove.pageX - startX;
        const newWidth = Math.max(75, startWidth + diff);
        th.style.width = newWidth + 'px';
        colWidths[targetCol] = newWidth;

        // Update all cells in this column immediately for real-time smoothness
        document.querySelectorAll(`td[data-col="${{targetCol}}"]`).forEach(td => {{
          td.style.width = newWidth + 'px';
          td.style.maxWidth = newWidth + 'px';
        }});
      }}

      function onMouseUp() {{
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        document.querySelectorAll('.col-resizer').forEach(r => r.classList.remove('resizing'));
        localStorage.setItem(COL_WIDTHS_KEY, JSON.stringify(colWidths));
        renderTable();
      }}

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    }});

    // Table Rendering

    // Currency Reference Rates & Period Utilities
    const CURRENCY_RATES = {{
      USD: 1.0,
      PHP: 58.5,
      EUR: 0.92,
      GBP: 0.77,
      AUD: 1.51,
      CAD: 1.36,
      SGD: 1.31
    }};

    const CURRENCY_SYMBOLS = {{
      USD: '$',
      PHP: '₱',
      EUR: '€',
      GBP: '£',
      AUD: 'A$',
      CAD: 'C$',
      SGD: 'S$'
    }};

    function toAnnualUsdValue(val, currency, period) {{
      if (val === null || isNaN(val)) return null;
      const rate = CURRENCY_RATES[currency] || 1.0;
      let annualLocal = val;
      if (period === 'monthly') annualLocal = val * 12;
      if (period === 'hourly') annualLocal = val * 2080;
      return annualLocal / rate;
    }}

    const tbody = document.getElementById('table-body');

    function renderTable() {{
      // Filter
      let filtered = jobs.filter(j => {{
        const matchesTier = activeTierFilter === 'all' || j.tier === activeTierFilter;
        const matchesStatus = activeStatusFilter === 'all' || j.status === activeStatusFilter;

        // Work Setup filter (Any is mutually exclusive)
        const selectedSetups = getSelectedToggleValues('table-group-work-setup');
        let matchesSetup = true;
        if (!selectedSetups.includes('Any') && selectedSetups.length > 0) {{
          matchesSetup = selectedSetups.some(s => j.work_setups && j.work_setups.includes(s));
        }}

        // Employment Type filter (Any is mutually exclusive)
        const selectedEmpTypes = getSelectedToggleValues('table-group-employment-type');
        let matchesEmpType = true;
        if (!selectedEmpTypes.includes('Any') && selectedEmpTypes.length > 0) {{
          matchesEmpType = selectedEmpTypes.includes(j.employment_type);
        }}

        // Salary filter (Input-to-Input range or segmented presets)
        const tMinEl = document.getElementById('table-filter-salary-min');
        const tMaxEl = document.getElementById('table-filter-salary-max');
        const tCurrEl = document.getElementById('table-filter-salary-currency');
        const tPeriodEl = document.getElementById('table-filter-salary-period');

        const tMinStr = tMinEl ? tMinEl.value.trim() : '';
        const tMaxStr = tMaxEl ? tMaxEl.value.trim() : '';
        const tCurr = tCurrEl ? tCurrEl.value : 'USD';
        const tPeriod = tPeriodEl ? tPeriodEl.value : 'yearly';

        const tMinUsd = toAnnualUsdValue(parseSalaryNum(tMinStr), tCurr, tPeriod);
        const tMaxUsd = toAnnualUsdValue(parseSalaryNum(tMaxStr), tCurr, tPeriod);

        let matchesSalary = true;
        if (tMinUsd !== null || tMaxUsd !== null) {{
          if (j.min_salary_usd === null && j.max_salary_usd === null) {{
            matchesSalary = false;
          }} else {{
            const jMin = j.min_salary_usd !== null ? j.min_salary_usd : j.max_salary_usd;
            const jMax = j.max_salary_usd !== null ? j.max_salary_usd : j.min_salary_usd;
            const minPass = (tMinUsd === null || jMax >= tMinUsd);
            const maxPass = (tMaxUsd === null || jMin <= tMaxUsd);
            matchesSalary = minPass && maxPass;
          }}
        }}

        let matchesSource = true;
        if (activeSourceFilter !== 'all') {{
          matchesSource = j.source && j.source.toLowerCase().includes(activeSourceFilter.toLowerCase());
        }}

        const q = searchQuery.toLowerCase();
        const matchesSearch = !q ||
          j.company.toLowerCase().includes(q) ||
          j.role.toLowerCase().includes(q) ||
          j.matched_skills.toLowerCase().includes(q) ||
          j.hiring_contact.toLowerCase().includes(q) ||
          j.base_domain.toLowerCase().includes(q) ||
          j.salary.toLowerCase().includes(q) ||
          (j.cover_letter && j.cover_letter.toLowerCase().includes(q));

        return matchesTier && matchesStatus && matchesSalary && matchesSource && matchesSearch && matchesSetup && matchesEmpType;
      }});

      // Update reset button visibility
      const resetBtn = document.getElementById('table-filters-reset-btn');
      if (resetBtn) {{
        const tMinEl = document.getElementById('table-filter-salary-min');
        const tMaxEl = document.getElementById('table-filter-salary-max');
        const hasCustomSalary = (tMinEl && tMinEl.value.trim() !== '') || (tMaxEl && tMaxEl.value.trim() !== '');
        const selectedSetups = getSelectedToggleValues('table-group-work-setup');
        const selectedEmpTypes = getSelectedToggleValues('table-group-employment-type');
        const hasCustomSetup = (!selectedSetups.includes('Any') && selectedSetups.length > 0);
        const hasCustomEmp = (!selectedEmpTypes.includes('Any') && selectedEmpTypes.length > 0);

        resetBtn.style.display = (hasCustomSalary || hasCustomSetup || hasCustomEmp) ? 'inline-flex' : 'none';
      }}

      // Sort
      filtered.sort((a, b) => {{
        let valA, valB;
        if (sortColumn === 'match_score') {{
          valA = a.match_score;
          valB = b.match_score;
        }} else if (sortColumn === 'tier') {{
          valA = a.tier;
          valB = b.tier;
        }} else if (sortColumn === 'company') {{
          valA = a.company.toLowerCase();
          valB = b.company.toLowerCase();
        }} else if (sortColumn === 'salary') {{
          valA = parseSalaryValue(a.salary);
          valB = parseSalaryValue(b.salary);
        }} else if (sortColumn === 'date') {{
          valA = parseDateValue(a.date_posted);
          valB = parseDateValue(b.date_posted);
        }} else if (sortColumn === 'status') {{
          valA = a.status.toLowerCase();
          valB = b.status.toLowerCase();
        }} else {{
          valA = a[sortColumn];
          valB = b[sortColumn];
        }}

        if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
        if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
        return 0;
      }});

      if (filtered.length === 0) {{
        tbody.innerHTML = `<tr><td colspan="${{colOrder.length}}" class="empty-row">No application leads match the selected criteria.</td></tr>`;
        return;
      }}

      tbody.innerHTML = filtered.map((j, idx) => {{
        const cells = colOrder.map(colId => {{
          return renderCell(colId, j);
        }}).join('');
        const delay = Math.min(idx * 14, 180);
        return `<tr style="animation-delay: ${{delay}}ms;">${{cells}}</tr>`;
      }}).join('');
    }}

    function renderCell(colId, j) {{
      const width = colWidths[colId] || COLUMNS[colId].defaultWidth;
      const style = `width: ${{width}}px; max-width: ${{width}}px;`;

      if (colId === 'tier') {{
        const tierClass = j.tier.toLowerCase() === 'target' ? 'target' : 'stretch';
        return `
          <td data-col="tier" style="${{style}}">
            <span class="tier-badge-inline ${{tierClass}}">${{j.tier}} (${{j.match_score}}%)</span>
            <div class="col-resizer" data-col="tier"></div>
          </td>
        `;
      }}

      if (colId === 'company') {{
        const skills = j.matched_skills ? j.matched_skills.split(',').map(s => s.trim()).filter(Boolean) : [];
        const skillsHtml = skills.map(s => `<span class="skill-tag">${{escapeHtml(s)}}</span>`).join('');
        return `
          <td data-col="company" style="${{style}}">
            <div class="company-name">${{escapeHtml(j.company)}}</div>
            <div class="role-title">${{escapeHtml(j.role)}}</div>
            ${{skillsHtml ? `<div class="skills-list">${{skillsHtml}}</div>` : ''}}
            <div class="col-resizer" data-col="company"></div>
          </td>
        `;
      }}

      if (colId === 'salary') {{
        const isNA = !j.salary || j.salary === 'N/A' || j.salary.toLowerCase() === 'undisclosed';
        return `
          <td data-col="salary" style="${{style}}">
            <div class="salary-cell ${{isNA ? 'na' : ''}}">
              ${{escapeHtml(j.salary)}}
            </div>
            <div class="col-resizer" data-col="salary"></div>
          </td>
        `;
      }}

      if (colId === 'date') {{
        return `
          <td data-col="date" style="${{style}}">
            <div class="date-cell">${{escapeHtml(j.date_posted)}}</div>
            <div class="col-resizer" data-col="date"></div>
          </td>
        `;
      }}

      if (colId === 'listing') {{
        const resumeFilename = `${{j.company.replace(/[^a-zA-Z0-9]/g, '_')}}_Resume.pdf`;
        const coverLetterFilename = `${{j.company.replace(/[^a-zA-Z0-9]/g, '_')}}_Cover_Letter.pdf`;
        return `
          <td data-col="listing" style="${{style}}">
            <div class="apply-resume-cell">
              <a
                href="${{escapeHtml(j.url)}}"
                target="_blank"
                rel="noopener noreferrer"
                class="apply-btn"
                title="Apply on ${{escapeHtml(j.base_domain)}} (opens job listing)"
              >
                <div class="apply-btn-row">
                  <span class="apply-btn-label">Apply</span>
                  <span class="apply-btn-arrow">↗</span>
                </div>
                <div class="apply-btn-domain" title="${{escapeHtml(j.url)}}">
                  ${{escapeHtml(j.base_domain)}}
                </div>
              </a>
              ${{j.resume_uri ? `
                <a
                  href="${{j.resume_uri}}"
                  target="_blank"
                  rel="noopener noreferrer"
                  draggable="true"
                  ondragstart="dragResume(event, '${{j.resume_uri}}')"
                  class="resume-attachment-btn"
                  title="Open Resume PDF or drag to a new browser tab"
                >
                  <span class="pdf-tag">PDF</span>
                  <span class="resume-filename">${{escapeHtml(resumeFilename)}}</span>
                  <span class="drag-handle" aria-hidden="true">⋮⋮</span>
                </a>
              ` : ''}}
              ${{j.cover_letter_uri ? `
                <a
                  href="${{j.cover_letter_uri}}"
                  target="_blank"
                  rel="noopener noreferrer"
                  draggable="true"
                  ondragstart="dragResume(event, '${{j.cover_letter_uri}}')"
                  class="resume-attachment-btn cover-letter-attachment-btn"
                  title="Open Tailored Cover Letter PDF or drag to a new browser tab"
                >
                  <span class="pdf-tag tag-cl">PDF</span>
                  <span class="resume-filename">${{escapeHtml(coverLetterFilename)}}</span>
                  <span class="drag-handle" aria-hidden="true">⋮⋮</span>
                </a>
              ` : ''}}
            </div>
            <div class="col-resizer" data-col="listing"></div>
          </td>
        `;
      }}

      if (colId === 'outreach') {{
        const emailSubject = `Application: ${{j.role}} - Simon Escaño`;
        const emailRecipient = j.hiring_contact && j.hiring_contact.includes('@') ? j.hiring_contact : '';
        const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${{encodeURIComponent(emailRecipient)}}&su=${{encodeURIComponent(emailSubject)}}&body=${{encodeURIComponent(j.cold_email)}}`;
        const linkedInSearchUrl = `https://www.linkedin.com/search/results/people/?keywords=${{encodeURIComponent(j.company + ' Engineering Manager')}}`;

        return `
          <td data-col="outreach" style="${{style}}">
            <div class="email-container">
              <div class="lead-header-row">
                <div class="lead-email-wrap">
                  <span class="lead-label">To:</span>
                  <a href="mailto:${{escapeHtml(j.hiring_contact)}}" class="truncated-email" title="Email ${{escapeHtml(j.hiring_contact)}}">
                    <span class="email-label">${{escapeHtml(j.hiring_contact)}}</span>
                  </a>
                </div>
                <a href="${{linkedInSearchUrl}}" target="_blank" rel="noopener noreferrer" class="truncated-link text-muted" title="Search ${{escapeHtml(j.company)}} Engineering Manager on LinkedIn">
                  <span class="link-label">LinkedIn</span>
                  <span class="link-arrow">↗</span>
                </a>
              </div>
              <div class="email-content-wrap">
                <div class="email-text" id="email-${{j.id}}">${{escapeHtml(j.cold_email)}}</div>
                <button class="expand-toggle" onclick="toggleEmailExpand(${{j.id}}, this)">
                  Expand
                </button>
              </div>
              <div class="email-actions">
                <button class="action-btn icon-only copy-btn" onclick="copyEmail(${{j.id}}, this)" title="Copy outreach message" aria-label="Copy outreach message">
                  <svg class="action-icon icon-copy" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                  <svg class="action-icon icon-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display: none;">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </button>
                <a href="${{gmailUrl}}" target="_blank" rel="noopener noreferrer" class="action-btn gmail-btn" title="Open pre-filled cold outreach draft in Gmail" aria-label="Open pre-filled cold outreach draft in Gmail">
                  <svg class="action-icon gmail-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                    <polyline points="22,6 12,13 2,6"></polyline>
                  </svg>
                  <span>Gmail</span>
                  <span class="action-arrow">↗</span>
                </a>
              </div>
            </div>
            <div class="col-resizer" data-col="outreach"></div>
          </td>
        `;
      }}

      if (colId === 'status') {{
        return `
          <td data-col="status" style="${{style}}">
            <div class="status-select-wrap" data-status="${{escapeHtml(j.status)}}" id="wrap-status-${{j.id}}">
              <span class="status-dot"></span>
              <select class="status-select" data-status="${{escapeHtml(j.status)}}" onchange="updateJobStatus(${{j.id}}, this.value, this)" aria-label="Application status">
                <option value="To Review" ${{j.status === 'To Review' ? 'selected' : ''}}>To Review</option>
                <option value="Applied" ${{j.status === 'Applied' ? 'selected' : ''}}>Applied</option>
                <option value="Interviewing" ${{j.status === 'Interviewing' ? 'selected' : ''}}>Interviewing</option>
                <option value="Offer" ${{j.status === 'Offer' ? 'selected' : ''}}>Offer</option>
                <option value="Rejected" ${{j.status === 'Rejected' ? 'selected' : ''}}>Rejected</option>
              </select>
            </div>
            <div class="col-resizer" data-col="status"></div>
          </td>
        `;
      }}

      return `<td style="${{style}}"></td>`;
    }}

    function escapeHtml(str) {{
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }}

    // Drag Resume Handler to browser tabs
    window.dragResume = function(e, uri) {{
      e.dataTransfer.setData('text/uri-list', uri);
      e.dataTransfer.setData('text/plain', uri);
      e.dataTransfer.effectAllowed = 'copyMove';
    }};

    // Expand/Collapse Outreach Note
    window.toggleEmailExpand = function(id, btn) {{
      const textEl = document.getElementById('email-' + id);
      if (!textEl) return;
      const isExpanded = textEl.classList.toggle('expanded');
      btn.textContent = isExpanded ? 'Collapse' : 'Expand';
    }};



    // Update Status Handler with Persistence & Live Count Refresh
    window.updateJobStatus = function(id, newStatus, selectEl) {{
      const job = jobs.find(j => j.id === id);
      if (job) {{
        job.status = newStatus;
        selectEl.setAttribute('data-status', newStatus);

        const wrap = document.getElementById('wrap-status-' + id);
        if (wrap) wrap.setAttribute('data-status', newStatus);

        // Save to localStorage
        statusOverrides[id] = newStatus;
        localStorage.setItem(STATUS_STORAGE_KEY, JSON.stringify(statusOverrides));

        updateStatusCounts();
        if (activeStatusFilter !== 'all') {{
          renderTable();
        }}
      }}
    }};

    // Tactile Copy Handler (Icon-Only Clipboard / Checkmark Toggle)
    window.copyEmail = function(id, btn) {{
      const el = document.getElementById('email-' + id);
      if (!el) return;
      const text = el.textContent || '';
      const iconCopy = btn.querySelector('.icon-copy');
      const iconCheck = btn.querySelector('.icon-check');

      navigator.clipboard.writeText(text).then(() => {{
        btn.classList.add('copied');
        btn.setAttribute('title', 'Copied!');
        if (iconCopy) iconCopy.style.display = 'none';
        if (iconCheck) iconCheck.style.display = 'block';
        setTimeout(() => {{
          btn.classList.remove('copied');
          btn.setAttribute('title', 'Copy outreach message');
          if (iconCopy) iconCopy.style.display = 'block';
          if (iconCheck) iconCheck.style.display = 'none';
        }}, 1800);
      }}).catch(() => {{
        const range = document.createRange();
        range.selectNodeContents(el);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        btn.setAttribute('title', 'Press Ctrl+C to copy');
      }});
    }};

    // Download Updated CSV from in-browser state
    window.exportUpdatedCsv = function() {{
      const headers = [
        'Match & Tier',
        'Company & Role',
        'Salary',
        'Date Posted',
        'Live Listing',
        'Contact Lead',
        'Tailored Resume',
        'Cold Email Snippet',
        'Tailored Cover Letter',
        'Cover Letter PDF',
        'Status'
      ];

      function escapeCsvField(val) {{
        if (val === null || val === undefined) return '""';
        let str = String(val).replace(/"/g, '""');
        return `"${{str}}"`;
      }}

      const csvRows = [headers.join(',')];

      jobs.forEach(j => {{
        const row = [
          escapeCsvField(`${{j.tier}} (${{j.match_score}}%)`),
          escapeCsvField(`${{j.company}} - ${{j.role}}`),
          escapeCsvField(j.salary),
          escapeCsvField(j.date_posted),
          escapeCsvField(j.url),
          escapeCsvField(j.hiring_contact),
          escapeCsvField(j.resume_uri),
          escapeCsvField(j.cold_email),
          escapeCsvField(j.cover_letter),
          escapeCsvField(j.cover_letter_uri),
          escapeCsvField(j.status)
        ];
        csvRows.push(row.join(','));
      }});

      const csvString = csvRows.join('\\r\\n');
      const blob = new Blob([csvString], {{ type: 'text/csv;charset=utf-8;' }});
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', 'pipeline_updated.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }};

    // Search input listener
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', (e) => {{
      searchQuery = e.target.value.trim();
      renderTable();
    }});

    // Tier filter segmented control listeners
    document.querySelectorAll('.segmented-control .seg-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.segmented-control .seg-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeTierFilter = btn.getAttribute('data-filter');
        renderTable();
      }});
    }});

    // Status filter listeners
    document.querySelectorAll('.status-filter-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.status-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeStatusFilter = btn.getAttribute('data-status');
        renderTable();
      }});
    }});

    // Initialize View
    updateStatusCounts();
    renderHeader();
    renderTable();

    // Table Filter Toggle Groups
    setupToggleGroup('table-group-work-setup', () => {{
      renderTable();
    }});

    setupToggleGroup('table-group-employment-type', () => {{
      renderTable();
    }});

    // Table Salary Range Inputs & Dropdowns
    ['table-filter-salary-min', 'table-filter-salary-max'].forEach(id => {{
      const el = document.getElementById(id);
      if (el) {{
        el.addEventListener('input', () => {{
          updateTableSalaryConversionsUI();
          renderTable();
        }});
      }}
    }});

    ['table-filter-salary-currency', 'table-filter-salary-period'].forEach(id => {{
      const el = document.getElementById(id);
      if (el) {{
        el.addEventListener('change', () => {{
          updateTableSalaryConversionsUI();
          renderTable();
        }});
      }}
    }});

    // Close Table Salary Popover on Click Outside
    document.addEventListener('click', (e) => {{
      const panel = document.getElementById('table-salary-conversion-panel');
      const btn = document.getElementById('table-salary-info-toggle');
      if (panel && panel.classList.contains('open')) {{
        if (!panel.contains(e.target) && !btn.contains(e.target)) {{
          panel.classList.remove('open');
          if (btn) btn.classList.remove('active');
        }}
      }}
    }});

    // Source filter listener
    const sourceSelect = document.getElementById('source-filter-select');
    if (sourceSelect) {{
      sourceSelect.addEventListener('change', (e) => {{
        activeSourceFilter = e.target.value;
        renderTable();
      }});
    }}

    // Modal & Prompt State Management
    const FIND_JOBS_STORAGE_KEY = 'job_hunting_find_jobs_params';

    window.openFindJobsModal = function() {{
      const modalEl = document.getElementById('find-jobs-modal');
      if (!modalEl) return;
      modalEl.classList.add('open');
      document.body.style.overflow = 'hidden';
      updatePromptPreview();
      updateSalaryConversionsUI();
    }};

    window.closeFindJobsModal = function() {{
      const modalEl = document.getElementById('find-jobs-modal');
      if (!modalEl) return;
      modalEl.classList.remove('open');
      document.body.style.overflow = '';
      const convPanel = document.getElementById('salary-conversion-panel');
      if (convPanel) convPanel.classList.remove('open');
      const infoBtn = document.getElementById('salary-info-toggle');
      if (infoBtn) infoBtn.classList.remove('active');
    }};

    // Close on backdrop click or Escape
    document.addEventListener('click', (e) => {{
      const modalEl = document.getElementById('find-jobs-modal');
      if (modalEl && e.target === modalEl) {{
        closeFindJobsModal();
      }}
    }});

    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') {{
        const modalEl = document.getElementById('find-jobs-modal');
        if (modalEl && modalEl.classList.contains('open')) {{
          closeFindJobsModal();
        }}
      }}
    }});

    // Toggle Group Management (Multi-select with 'Any' mutual exclusivity)
    function setupToggleGroup(groupId, onChange) {{
      const group = document.getElementById(groupId);
      if (!group) return;

      group.addEventListener('click', (e) => {{
        const btn = e.target.closest('.toggle-btn');
        if (!btn) return;

        const val = btn.getAttribute('data-val');
        const allBtns = Array.from(group.querySelectorAll('.toggle-btn'));
        const anyBtn = allBtns.find(b => b.getAttribute('data-val') === 'Any');

        if (val === 'Any') {{
          allBtns.forEach(b => b.classList.remove('selected'));
          btn.classList.add('selected');
        }} else {{
          if (anyBtn) anyBtn.classList.remove('selected');
          btn.classList.toggle('selected');

          const specificSelected = allBtns.filter(b => b !== anyBtn && b.classList.contains('selected'));
          if (specificSelected.length === 0 && anyBtn) {{
            anyBtn.classList.add('selected');
          }}
        }}

        if (typeof onChange === 'function') {{
          onChange(getSelectedToggleValues(groupId));
        }} else {{
          saveFindJobsState();
        }}
      }});
    }}

    function getSelectedToggleValues(groupId) {{
      const group = document.getElementById(groupId);
      if (!group) return ['Any'];
      const selected = Array.from(group.querySelectorAll('.toggle-btn.selected')).map(b => b.getAttribute('data-val'));
      return selected.length > 0 ? selected : ['Any'];
    }}

    function setSelectedToggleValues(groupId, values) {{
      const group = document.getElementById(groupId);
      if (!group) return;
      const allBtns = Array.from(group.querySelectorAll('.toggle-btn'));
      const vals = Array.isArray(values) && values.length > 0 ? values : ['Any'];

      allBtns.forEach(b => {{
        const v = b.getAttribute('data-val');
        if (vals.includes(v)) {{
          b.classList.add('selected');
        }} else {{
          b.classList.remove('selected');
        }}
      }});

      const hasSelected = allBtns.some(b => b.classList.contains('selected'));
      if (!hasSelected) {{
        const anyBtn = allBtns.find(b => b.getAttribute('data-val') === 'Any');
        if (anyBtn) anyBtn.classList.add('selected');
      }}
    }}

    // Salary Parsing & Conversions
    function parseSalaryNum(val) {{
      if (!val) return null;
      const cleaned = String(val).replace(/,/g, '').trim();
      const n = parseFloat(cleaned);
      return isNaN(n) ? null : n;
    }}

    function formatRangeText(valA, valB, symbol, suffix) {{
      if (valA !== null && valB !== null) {{
        if (valA === valB) {{
          return `${{symbol}}${{Math.round(valA).toLocaleString('en-US')}} ${{suffix}}`;
        }}
        return `${{symbol}}${{Math.round(valA).toLocaleString('en-US')}} to ${{symbol}}${{Math.round(valB).toLocaleString('en-US')}} ${{suffix}}`;
      }}
      if (valA !== null) {{
        return `${{symbol}}${{Math.round(valA).toLocaleString('en-US')}}+ ${{suffix}}`;
      }}
      if (valB !== null) {{
        return `Up to ${{symbol}}${{Math.round(valB).toLocaleString('en-US')}} ${{suffix}}`;
      }}
      return '';
    }}

    function computeSalaryConversions(minVal, maxVal, currency, period) {{
      const rate = CURRENCY_RATES[currency] || 1.0;

      function toAnnualUsd(val) {{
        if (val === null) return null;
        let annualLocal = val;
        if (period === 'monthly') annualLocal = val * 12;
        if (period === 'hourly') annualLocal = val * 2080;
        return annualLocal / rate;
      }}

      const minUsd = toAnnualUsd(minVal);
      const maxUsd = toAnnualUsd(maxVal);

      if (minUsd === null && maxUsd === null) return null;

      return {{
        usd: {{
          annual: formatRangeText(minUsd, maxUsd, '$', '/yr'),
          monthly: formatRangeText(minUsd ? minUsd / 12 : null, maxUsd ? maxUsd / 12 : null, '$', '/mo'),
          hourly: formatRangeText(minUsd ? minUsd / 2080 : null, maxUsd ? maxUsd / 2080 : null, '$', '/hr')
        }},
        php: {{
          annual: formatRangeText(minUsd ? minUsd * 58.5 : null, maxUsd ? maxUsd * 58.5 : null, '₱', '/yr'),
          monthly: formatRangeText(minUsd ? (minUsd * 58.5) / 12 : null, maxUsd ? (maxUsd * 58.5) / 12 : null, '₱', '/mo'),
          hourly: formatRangeText(minUsd ? (minUsd * 58.5) / 2080 : null, maxUsd ? (maxUsd * 58.5) / 2080 : null, '₱', '/hr')
        }},
        eur: {{
          annual: formatRangeText(minUsd ? minUsd * 0.92 : null, maxUsd ? maxUsd * 0.92 : null, '€', '/yr')
        }},
        gbp: {{
          annual: formatRangeText(minUsd ? minUsd * 0.77 : null, maxUsd ? maxUsd * 0.77 : null, '£', '/yr')
        }},
        aud: {{
          annual: formatRangeText(minUsd ? minUsd * 1.51 : null, maxUsd ? maxUsd * 1.51 : null, 'A$', '/yr')
        }}
      }};
    }}


    // Table Salary Conversion Panel & Reset Handlers
    window.toggleTableSalaryConversionPanel = function() {{
      const panel = document.getElementById('table-salary-conversion-panel');
      const btn = document.getElementById('table-salary-info-toggle');
      if (!panel || !btn) return;
      const isOpen = panel.classList.toggle('open');
      btn.classList.toggle('active', isOpen);
      if (isOpen) updateTableSalaryConversionsUI();
    }};

    function updateTableSalaryConversionsUI() {{
      const minEl = document.getElementById('table-filter-salary-min');
      const maxEl = document.getElementById('table-filter-salary-max');
      const currEl = document.getElementById('table-filter-salary-currency');
      const periodEl = document.getElementById('table-filter-salary-period');
      const btn = document.getElementById('table-salary-info-toggle');
      const panel = document.getElementById('table-salary-conversion-panel');
      if (!minEl || !maxEl || !currEl || !periodEl || !panel) return;

      const minVal = parseSalaryNum(minEl.value);
      const maxVal = parseSalaryNum(maxEl.value);
      const curr = currEl.value;
      const period = periodEl.value;

      const hasValues = (minVal !== null || maxVal !== null);
      if (btn) {{
        btn.classList.toggle('has-values', hasValues);
      }}

      if (!panel.classList.contains('open')) return;

      if (!hasValues) {{
        panel.innerHTML = `
          <div class="conv-header">
            <span class="conv-title">Salary Filter Equivalents</span>
            <span class="conv-rate">1 USD ≈ ₱58.50 PHP</span>
          </div>
          <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-sans); line-height: 1.4;">
            Enter a Min or Max salary to see real-time FX conversions across USD, PHP, EUR, and GBP.
          </div>
        `;
        return;
      }}

      const conv = computeSalaryConversions(minVal, maxVal, curr, period);
      if (!conv) return;

      panel.innerHTML = `
        <div class="conv-header">
          <span class="conv-title">Active Salary Filter Equivalents</span>
          <span class="conv-rate">1 USD ≈ ₱58.50 PHP</span>
        </div>
        <div class="conv-grid">
          <div class="conv-card highlight">
            <span class="conv-card-title">USD Annual</span>
            <span class="conv-val-main">${{conv.usd.annual}}</span>
            <span class="conv-val-sub">${{conv.usd.monthly}} | ${{conv.usd.hourly}}</span>
          </div>
          <div class="conv-card">
            <span class="conv-card-title">PHP (Philippine Peso)</span>
            <span class="conv-val-main">${{conv.php.annual}}</span>
            <span class="conv-val-sub">${{conv.php.monthly}}</span>
          </div>
          <div class="conv-card">
            <span class="conv-card-title">EUR & GBP</span>
            <span class="conv-val-main">${{conv.eur.annual}}</span>
            <span class="conv-val-sub">${{conv.gbp.annual}}</span>
          </div>
        </div>
      `;
    }}

    window.resetTableAdvancedFilters = function() {{
      const minEl = document.getElementById('table-filter-salary-min');
      const maxEl = document.getElementById('table-filter-salary-max');
      const currEl = document.getElementById('table-filter-salary-currency');
      const periodEl = document.getElementById('table-filter-salary-period');
      const panel = document.getElementById('table-salary-conversion-panel');
      const infoBtn = document.getElementById('table-salary-info-toggle');

      if (minEl) minEl.value = '';
      if (maxEl) maxEl.value = '';
      if (currEl) currEl.value = 'USD';
      if (periodEl) periodEl.value = 'yearly';
      if (panel) panel.classList.remove('open');
      if (infoBtn) {{
        infoBtn.classList.remove('active');
        infoBtn.classList.remove('has-values');
      }}

      setSelectedToggleValues('table-group-work-setup', ['Any']);
      setSelectedToggleValues('table-group-employment-type', ['Any']);

      renderTable();
    }};

    window.toggleSalaryConversionPanel = function() {{
      const panel = document.getElementById('salary-conversion-panel');
      const btn = document.getElementById('salary-info-toggle');
      if (!panel || !btn) return;
      const isOpen = panel.classList.toggle('open');
      btn.classList.toggle('active', isOpen);
      if (isOpen) updateSalaryConversionsUI();
    }};

    function updateSalaryConversionsUI() {{
      const p = getParamValues();
      const minVal = parseSalaryNum(p.salaryMin);
      const maxVal = parseSalaryNum(p.salaryMax);
      const btn = document.getElementById('salary-info-toggle');
      const hint = document.getElementById('salary-quick-hint');
      const panel = document.getElementById('salary-conversion-panel');

      const hasValues = (minVal !== null || maxVal !== null);
      if (btn) {{
        btn.classList.toggle('has-values', hasValues);
      }}

      if (!hasValues) {{
        if (hint) hint.textContent = '';
        if (panel) {{
          panel.innerHTML = `
            <div class="conv-header">
              <span class="conv-title">Currency & Period Conversion Calculator</span>
              <span class="conv-rate">Reference FX: 1 USD ≈ ₱58.50 PHP</span>
            </div>
            <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-sans);">
              Enter a Min or Max salary above to see live equivalent conversions across PHP, USD, EUR, GBP, and AUD.
            </div>
          `;
        }}
        return;
      }}

      const convs = computeSalaryConversions(minVal, maxVal, p.salaryCurrency, p.salaryPeriod);
      if (!convs) return;

      if (hint) {{
        hint.textContent = `≈ ${{convs.php.monthly}} (PHP) | ${{convs.usd.annual}} | ${{convs.usd.hourly}}`;
      }}

      if (panel) {{
        panel.innerHTML = `
          <div class="conv-header">
            <span class="conv-title">Live FX & Frequency Breakdown</span>
            <span class="conv-rate">FX: 1 USD ≈ ₱58.50 PHP | 1 GBP ≈ $1.30 USD</span>
          </div>
          <div class="conv-grid">
            <div class="conv-card highlight">
              <div class="conv-card-title">Philippine Peso (Local Take-Home)</div>
              <div class="conv-val-main">${{convs.php.monthly}}</div>
              <div class="conv-val-sub">${{convs.php.annual}}</div>
              <div class="conv-val-sub">${{convs.php.hourly}}</div>
            </div>
            <div class="conv-card">
              <div class="conv-card-title">US Dollar Benchmark</div>
              <div class="conv-val-main">${{convs.usd.annual}}</div>
              <div class="conv-val-sub">${{convs.usd.monthly}}</div>
              <div class="conv-val-sub">${{convs.usd.hourly}}</div>
            </div>
            <div class="conv-card">
              <div class="conv-card-title">International Currencies</div>
              <div class="conv-val-sub">EUR: ${{convs.eur.annual}}</div>
              <div class="conv-val-sub">GBP: ${{convs.gbp.annual}}</div>
              <div class="conv-val-sub">AUD: ${{convs.aud.annual}}</div>
            </div>
          </div>
        `;
      }}
    }}

    function getParamValues() {{
      const getVal = (id, fallback) => {{
        const el = document.getElementById(id);
        return el ? el.value : fallback;
      }};
      return {{
        salaryMin: getVal('param-salary-min', '').trim(),
        salaryMax: getVal('param-salary-max', '').trim(),
        salaryCurrency: getVal('param-salary-currency', 'USD'),
        salaryPeriod: getVal('param-salary-period', 'yearly'),
        workSetups: getSelectedToggleValues('group-work-setup'),
        seniorities: getSelectedToggleValues('group-seniority'),
        empTypes: getSelectedToggleValues('group-employment-type'),
        roles: getVal('param-roles', 'Backend Engineer, Full Stack Engineer, Systems Engineer, Junior SWE, Web Developer').trim(),
        count: getVal('param-count', '25'),
        sites: getVal('param-sites', '').trim()
      }};
    }}

    function generatePromptText() {{
      const p = getParamValues();
      const siteLines = p.sites ? p.sites.split(String.fromCharCode(10)).map(s => s.trim()).filter(Boolean) : [];
      const defaultSites = [
        '  - https://himalayas.app/jobs?remote_location=Anywhere',
        '  - https://wellfound.com/jobs',
        '  - https://www.workatastartup.com/companies',
        '  - https://weworkremotely.com/categories/remote-back-end-programming-jobs'
      ].join(String.fromCharCode(10));
      const sitesFormatted = siteLines.length > 0
        ? siteLines.map(s => `  - ${{s}}`).join(String.fromCharCode(10))
        : defaultSites;

      // Format Salary Range
      let salaryDesc = 'Any Compensation (Default)';
      const minN = parseSalaryNum(p.salaryMin);
      const maxN = parseSalaryNum(p.salaryMax);
      const sym = CURRENCY_SYMBOLS[p.salaryCurrency] || '$';
      if (minN !== null || maxN !== null) {{
        const rangeText = formatRangeText(minN, maxN, sym, `${{p.salaryCurrency}}/${{p.salaryPeriod}}`);
        const conv = computeSalaryConversions(minN, maxN, p.salaryCurrency, p.salaryPeriod);
        if (conv) {{
          salaryDesc = `${{rangeText}} (approx. ${{conv.php.monthly}} | ${{conv.usd.annual}})`;
        }} else {{
          salaryDesc = rangeText;
        }}
      }}

      // Format Work Setup
      const workSetupDesc = p.workSetups.includes('Any') || p.workSetups.length === 0
        ? 'Any Remote Work Setup (Default)'
        : p.workSetups.join(', ');

      // Format Seniority
      const seniorityDesc = p.seniorities.includes('Any') || p.seniorities.length === 0
        ? 'Any Seniority Level (Default)'
        : p.seniorities.join(', ');

      // Format Employment Type
      const empTypeDesc = p.empTypes.includes('Any') || p.empTypes.length === 0
        ? 'Any Employment Type (Default)'
        : p.empTypes.join(', ');

      return `/browser Find newly posted remote software engineering positions and pipe them through engine.py:

SEARCH PARAMETERS:
- Target Portals:
${{sitesFormatted}}
- Role Profiles: ${{p.roles || 'Backend, Full Stack, Systems, Junior Software Engineer, Web Developer'}}
- Seniority Calibration: ${{seniorityDesc}} (Target: Junior/Entry 0-2 YOE; Stretch: SWE 2-3 YOE with strong portfolio alignment)
- Work Setup: ${{workSetupDesc}} (Strictly confirm eligibility for remote candidate in Cebu, Philippines: Worldwide, Global, Anywhere, APAC, Contractor, B2B, Deel. Reject US Citizen, Green Card, US-only, W-2 only, or no visa sponsorship)
- Employment Type: ${{empTypeDesc}}
- Compensation / Target Salary: ${{salaryDesc}}
- Target Fresh Leads: ${{p.count}} verified positions

CANDIDATE QUALIFICATIONS & REPERTOIRE (data.json):
- Name: Simon Escaño (Cebu, Philippines)
- Education: Cebu Institute of Technology - University (CIT-U), BS Computer Science Cum Laude (GWA 4.59 / 5.0)
- Stack: Rust, Axum, Python, FastAPI, Django, TypeScript, React 19, Next.js, PostgreSQL, Supabase, Redis, Docker
- Verified Projects: Trellis (Rust/Axum graph routing), PixCell (FastAPI/YOLOv8 diagnostics), Gitlore (TypeScript/Cloudflare Workers AST), TekNotes (Django/PostgreSQL/Redis), STEMIFlow (FastAPI emergency triage), AutoPBI (C#/.NET automation), Lupus Lens (React 19 optical inspection), Fasaar (Java networking)
- Portfolio: https://simon-escano.pages.dev | GitHub: https://github.com/simon-escano

PIPELINE AUTOMATION TASKS:
1. Search the target portals for active listings matching the criteria, ignoring paywalled aggregators (flexjobs.com, theladders.com, ziprecruiter.com, jooble.org, etc.).
2. For each verified job listing, extract:
   - Company, Role, Live URL, Source, Description, Salary range (or N/A), Relative date posted (e.g. "2d ago"), and Hiring Contact email (e.g. Engineering Manager, Founder, or Recruiter).
3. Call engine.process_job() to:
   - Verify Cebu legal remote eligibility and calibrate seniority tier (Target vs Stretch)
   - Deduplicate against pipeline.db (drop duplicates automatically)
   - Compute match score and match skills against candidate portfolio
   - Compile a tailored 1-page ATS LaTeX resume into ./resumes/{{company}}_{{role}}.pdf via tectonic
   - Compile a tailored 1-page ATS LaTeX cover letter into ./resumes/{{company}}_{{role}}_cover_letter.pdf via tectonic
   - Draft an authentic peer-to-peer cold outreach message with zero em dashes
   - Ingest record into pipeline.db
4. Execute "python export_views.py" to regenerate dist/pipeline.csv and dist/pipeline.html with the new rows.
5. Provide a clean summary table of newly added positions vs skipped duplicates, and output the absolute path to dist/pipeline.html.`;
    }}

    function updatePromptPreview() {{
      const previewBox = document.getElementById('prompt-preview-box');
      if (!previewBox) return;
      previewBox.textContent = generatePromptText();
    }}

    function saveFindJobsState() {{
      const p = getParamValues();
      localStorage.setItem(FIND_JOBS_STORAGE_KEY, JSON.stringify(p));
      updatePromptPreview();
      updateSalaryConversionsUI();
    }}

    function loadFindJobsState() {{
      try {{
        const saved = JSON.parse(localStorage.getItem(FIND_JOBS_STORAGE_KEY) || 'null');
        if (saved) {{
          const setVal = (id, val) => {{
            const el = document.getElementById(id);
            if (el && val !== undefined && val !== null) el.value = val;
          }};
          setVal('param-salary-min', saved.salaryMin);
          setVal('param-salary-max', saved.salaryMax);
          setVal('param-salary-currency', saved.salaryCurrency || 'USD');
          setVal('param-salary-period', saved.salaryPeriod || 'yearly');

          setSelectedToggleValues('group-work-setup', saved.workSetups);
          setSelectedToggleValues('group-seniority', saved.seniorities);
          setSelectedToggleValues('group-employment-type', saved.empTypes);

          setVal('param-roles', saved.roles);
          setVal('param-count', saved.count);
          setVal('param-sites', saved.sites);
        }}
      }} catch (err) {{
        console.error('Failed to load find jobs params:', err);
      }}
      updatePromptPreview();
      updateSalaryConversionsUI();
    }}

    // Setup Toggle Groups
    setupToggleGroup('group-work-setup');
    setupToggleGroup('group-seniority');
    setupToggleGroup('group-employment-type');

    // Attach form input listeners
    ['param-salary-min', 'param-salary-max', 'param-salary-currency', 'param-salary-period', 'param-roles', 'param-count', 'param-sites'].forEach(id => {{
      const el = document.getElementById(id);
      if (el) {{
        el.addEventListener('input', saveFindJobsState);
        el.addEventListener('change', saveFindJobsState);
      }}
    }});

    window.copyGeneratedPrompt = function() {{
      const promptText = generatePromptText();
      const btn = document.getElementById('copy-prompt-btn');

      navigator.clipboard.writeText(promptText).then(() => {{
        if (btn) {{
          btn.classList.add('copied');
          btn.innerHTML = `
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span>Copied Prompt!</span>
          `;
          setTimeout(() => {{
            btn.classList.remove('copied');
            btn.innerHTML = `
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>Copy Prompt</span>
            `;
          }}, 2000);
        }}
      }}).catch(() => {{
        const previewBox = document.getElementById('prompt-preview-box');
        if (previewBox) {{
          const range = document.createRange();
          range.selectNodeContents(previewBox);
          const sel = window.getSelection();
          sel.removeAllRanges();
          sel.addRange(range);
          if (btn) btn.querySelector('span').textContent = 'Press Ctrl+C';
        }}
      }});
    }};

    // Load initial modal state
    loadFindJobsState();

    </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path


if __name__ == "__main__":
    jobs = load_jobs()
    csv_file = export_csv(jobs)
    html_file = export_html(jobs)
    print(f"Exported {len(jobs)} leads:")
    print(f"  CSV:  {csv_file}")
    print(f"  HTML: {html_file}")

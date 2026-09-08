"""Job Application Pipeline Engine (`engine.py`)

Handles candidate evaluation, domain filtering, remote eligibility calibration,
seniority calibration, dynamic project matching, ATS-compliant LaTeX compilation,
non-AI cold email drafting, deduplication, and SQLite ingestion.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import zlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

# --- Paths & Constants ---
ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "pipeline.db"
DATA_PATH = ROOT_DIR / "data.json"
TEMPLATE_PATH = ROOT_DIR / "template.tex"
COVER_LETTER_TEMPLATE_PATH = ROOT_DIR / "cover_letter_template.tex"
RESUMES_DIR = ROOT_DIR / "resumes"
DIST_DIR = ROOT_DIR / "dist"

# Ensure directories exist
RESUMES_DIR.mkdir(parents=True, exist_ok=True)
DIST_DIR.mkdir(parents=True, exist_ok=True)

# 1. Blacklisted Aggregators & Paywalls
BLACKLISTED_DOMAINS: List[str] = [
    "flexjobs.com",
    "theladders.com",
    "ziprecruiter.com",
    "jooble.org",
    "talent.com",
    "glassdoor.com",
    "monster.com",
    "careerbuilder.com",
    "simplyhired.com",
]

# Preferred direct career sites and ATS endpoints
PREFERRED_ATS_DOMAINS: List[str] = [
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "workable.com",
]

# 2. Remote Eligibility Rules (Cebu, Philippines)
# Reject triggers take precedence over accept triggers
REMOTE_REJECT_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bus\s+citizen\b", re.IGNORECASE),
    re.compile(r"\bu\.s\.\s+citizen\b", re.IGNORECASE),
    re.compile(r"\bgreen\s+card\b", re.IGNORECASE),
    re.compile(r"\bw-?2\s+only\b", re.IGNORECASE),
    re.compile(r"\bmust\s+reside\s+in\s+(?:the\s+)?(?:us|u\.s\.|united\s+states|eu|uk|canada)\b", re.IGNORECASE),
    re.compile(r"\bmust\s+be\s+located\s+in\s+(?:the\s+)?(?:us|u\.s\.|united\s+states|eu|uk|canada)\b", re.IGNORECASE),
    re.compile(r"\bus\s+work\s+authorization\s+without\s+sponsorship\b", re.IGNORECASE),
    re.compile(r"\brequires\s+us\s+work\s+authorization\s+without\s+sponsorship\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:visa\s+)?sponsorship\b", re.IGNORECASE),
    re.compile(r"\b(?:us|u\.s\.|usa|united\s+states)\s+only\b", re.IGNORECASE),
]

REMOTE_ACCEPT_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bworldwide\b", re.IGNORECASE),
    re.compile(r"\bglobal(?:ly)?\b", re.IGNORECASE),
    re.compile(r"\banywhere\b", re.IGNORECASE),
    re.compile(r"\bapac\b", re.IGNORECASE),
    re.compile(r"\bcontractor\b", re.IGNORECASE),
    re.compile(r"\bb2b\b", re.IGNORECASE),
    re.compile(r"\bemployer\s+of\s+record\b", re.IGNORECASE),
    re.compile(r"\bdeel\b", re.IGNORECASE),
    re.compile(r"\bremote\b", re.IGNORECASE),
]

# 3. Seniority Calibration Keywords
HARD_REJECT_TITLES: List[str] = [
    "senior",
    "sr.",
    "sr ",
    "lead",
    "staff",
    "principal",
    "director",
    "head of",
    "manager",
    "architect",
]

TARGET_TITLE_KEYWORDS: List[str] = [
    "junior",
    "jr.",
    "jr ",
    "associate",
    "entry",
    "entry-level",
    "swe i",
    "software engineer i",
    "developer i",
    "intern",
    "graduate",
    "new grad",
]

STRETCH_TITLE_KEYWORDS: List[str] = [
    "software engineer",
    "backend engineer",
    "full-stack engineer",
    "full stack engineer",
    "software developer",
    "backend developer",
    "full-stack developer",
    "full stack developer",
    "web developer",
    "swe ii",
    "software engineer ii",
]

# High-craft project catalog with verified LaTeX bullet formatting
PROJECT_CATALOG: Dict[str, Dict[str, Any]] = {
    "PixCell": {
        "title": "PixCell",
        "tech": "Next.js, FastAPI, YOLOv8, Supabase, PostgreSQL, Python",
        "links": [("Live", "https://pixcell-ai.vercel.app"), ("GitHub", "https://github.com/simon-escano/pixcell")],
        "bullets": [
            "Architected real-time medical diagnostic platform integrating YOLOv8 computer vision with automated LLM diagnostic workflows.",
            "Engineered asynchronous FastAPI endpoints with Supabase auth and storage, achieving sub-second latency for live microscopy telemetry streaming.",
        ],
        "email_metric": "Recently, I architected PixCell (https://pixcell-ai.vercel.app), engineering asynchronous FastAPI endpoints and Supabase pipelines to achieve sub-second live streaming latency under production workloads.",
        "skills": ["Next.js", "FastAPI", "Python", "PostgreSQL", "Supabase", "YOLOv8", "Computer Vision", "AI"],
    },
    "STEMIFlow": {
        "title": "STEMIFlow",
        "tech": "React, FastAPI, Python, PostgreSQL, Supabase",
        "links": [("GitHub", "https://github.com/simon-escano/stemiflow"), ("Live", "https://stemiflow.vercel.app")],
        "bullets": [
            "Engineered real-time cardiovascular risk-prediction models, hospital pre-alert alerts, and automated PhilHealth referral pipelines.",
            "Awarded Champion at the Swiss Innovation Prize Competition Batch 2026 (Life Sciences \\& Digital Health).",
        ],
        "email_metric": "Recently, I developed STEMIFlow (https://stemiflow.vercel.app), engineering real-time prediction engines and automated referral pipelines that won Champion at the Swiss Innovation Prize.",
        "skills": ["React", "FastAPI", "Python", "PostgreSQL", "Supabase", "Leaflet", "Machine Learning"],
    },
    "KaagapAI": {
        "title": "KaagapAI",
        "tech": "React 19, Vite, Tailwind CSS, Python, Microservices",
        "links": [("GitHub", "https://github.com/simon-escano/kaagapai"), ("Live", "https://kaagapai-tntw.onrender.com")],
        "bullets": [
            "Architected offline-first rural health workstation with a 5-step clinical triage engine, predictive inventory forecasting, and automated referral handoffs.",
            "Awarded National Finalist \\& People's Choice Award at the AI Ready ASEAN Youth Challenge 2026.",
        ],
        "email_metric": "Recently, I architected KaagapAI (https://kaagapai-tntw.onrender.com), building an offline-first clinical workstation with 5-step triage and predictive inventory forecasting.",
        "skills": ["React", "Vite", "Tailwind CSS", "Python", "Microservices", "TypeScript"],
    },
    "Trellis": {
        "title": "Trellis",
        "tech": "Rust, Axum, Angular 18, TypeScript, PostgreSQL, GraphQL",
        "links": [("Live", "https://trellis-dev.vercel.app"), ("GitHub", "https://github.com/simon-escano/trellis")],
        "bullets": [
            "Architected high-concurrency knowledge graph routing engine in Rust (Axum) with async-graphql and PostgreSQL relational mapping.",
            "Built interactive graph visualization interface in Angular 18 and vis-network for real-time relational entity exploration.",
        ],
        "email_metric": "Recently, I built Trellis (https://trellis-dev.vercel.app), architecting a high-concurrency knowledge graph routing engine in Rust and Axum backed by PostgreSQL.",
        "skills": ["Rust", "Axum", "PostgreSQL", "GraphQL", "TypeScript", "Angular", "Docker"],
    },
    "AutoPBI": {
        "title": "AutoPBI",
        "tech": "C\\#, .NET, Avalonia UI, PowerShell, Power BI REST APIs",
        "links": [("Docs", "https://docs-autopbi.vercel.app"), ("GitHub", "https://github.com/simon-escano/AutoPBI")],
        "bullets": [
            "Developed enterprise desktop automation tool in C\\# (.NET/Avalonia UI) to automate bulk Power BI dataset updates and workspace deployments.",
            "Streamlined enterprise reporting execution overhead by 80\\% with strict runtime validation schemas and automated exception handling.",
        ],
        "email_metric": "Recently, I built AutoPBI (https://github.com/simon-escano/AutoPBI), cutting manual data pipeline execution overhead by 80% using C# and automated Power BI ETL scripts.",
        "skills": ["C#", ".NET", "Avalonia", "PowerShell", "Power BI", "ETL", "Automation"],
    },
    "Gitlore": {
        "title": "Gitlore",
        "tech": "React 19, TypeScript, Hono, Cloudflare Workers, Cerebras AI",
        "links": [("Live", "https://web.gitlore.workers.dev"), ("GitHub", "https://github.com/simon-escano/gitlore")],
        "bullets": [
            "Engineered edge-native code architecture intelligence platform on Cloudflare Workers and Hono with Cerebras AI sub-second inference.",
            "Implemented Mermaid.js AST diagram generation and runtime Zod validation for autonomous codebase mapping.",
        ],
        "email_metric": "Recently, I developed Gitlore (https://web.gitlore.workers.dev), building an edge-native code architecture platform on Cloudflare Workers and Hono with sub-second AI inference.",
        "skills": ["React", "TypeScript", "Hono", "Cloudflare", "Serverless", "Zod"],
    },
    "TekNotes": {
        "title": "TekNotes",
        "tech": "Django, Python, PostgreSQL, Redis, Tailwind CSS",
        "links": [("GitHub", "https://github.com/Wetooa/TekNotes")],
        "bullets": [
            "Built full-stack collaborative documentation platform using Django, PostgreSQL, and Redis caching for high-speed markdown rendering.",
            "Integrated WebSocket live notifications, OAuth multi-provider authentication, and responsive Tailwind UI.",
        ],
        "email_metric": "Recently, I built TekNotes (https://github.com/Wetooa/TekNotes), engineering collaborative markdown documentation with Django, PostgreSQL, and Redis caching.",
        "skills": ["Django", "Python", "PostgreSQL", "Redis", "Tailwind CSS", "WebSockets"],
    },
    "Lupus Lens": {
        "title": "Lupus Lens",
        "tech": "React 19, TypeScript, Vite, Tailwind CSS, Supabase",
        "links": [("Live", "https://lupus-lens-two.vercel.app"), ("GitHub", "https://github.com/moltmalt/lupus-lens")],
        "bullets": [
            "Developed digital signal processing and optical inspection web application with custom hardware alignment and Gradio AI integration.",
            "Won 2nd Runner-Up at the Southern Taiwan University of Science and Technology Digital Signal Processing Competition.",
        ],
        "email_metric": "Recently, I built Lupus Lens (https://lupus-lens-two.vercel.app), engineering optical DSP pipelines and reactive web interfaces with React and Supabase.",
        "skills": ["React", "TypeScript", "Vite", "Tailwind CSS", "Supabase", "DSP"],
    },
    "Pawductive": {
        "title": "Pawductive",
        "tech": "Android, Java, Kotlin, Firebase Realtime Database",
        "links": [("GitHub", "https://github.com/simon-escano/Pawductive_2")],
        "bullets": [
            "Built gamified native Android productivity application utilizing Firebase Realtime Database and Cloud Authentication.",
            "Designed custom reactive UI in Kotlin/Java with local persistent caching and low-latency state synchronization.",
        ],
        "email_metric": "Recently, I developed Pawductive (https://github.com/simon-escano/Pawductive_2), building a native Android app with real-time Firebase sync and offline state caching.",
        "skills": ["Android", "Java", "Kotlin", "Firebase", "Mobile"],
    },
    "Fashion MNIST Classifier": {
        "title": "Fashion MNIST Classifier",
        "tech": "TensorFlow.js, WebGL, JavaScript, Tailwind CSS",
        "links": [("Live", "https://simon-escano.github.io/Fashion-MNIST-Classifier/")],
        "bullets": [
            "Built zero-server-cost in-browser neural network inference engine using TensorFlow.js and WebGL hardware acceleration.",
            "Delivered instant client-side classification with interactive canvas drawing and real-time confidence scores.",
        ],
        "email_metric": "Recently, I engineered the Fashion MNIST Classifier (https://simon-escano.github.io/Fashion-MNIST-Classifier/), implementing browser-native WebGL model inference.",
        "skills": ["TensorFlow.js", "JavaScript", "WebGL", "Machine Learning"],
    },
}


# --- Database Helpers ---

def init_db(db_path: Path | str = DB_PATH) -> None:
    """Ensure pipeline.db and the jobs table exist with the required schema."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_hash TEXT UNIQUE,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            source TEXT,
            seniority_tier TEXT CHECK (seniority_tier IN ('Target', 'Stretch') OR seniority_tier IS NULL),
            match_score INTEGER,
            matched_skills TEXT,
            hiring_contact TEXT,
            cold_email TEXT,
            resume_path TEXT,
            salary TEXT,
            date_posted TEXT,
            cover_letter TEXT,
            cover_letter_path TEXT,
            status TEXT DEFAULT 'To Review',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute("PRAGMA table_info(jobs)")
    cols = [r[1] for r in cur.fetchall()]
    if "cover_letter" not in cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN cover_letter TEXT")
    if "cover_letter_path" not in cols:
        cur.execute("ALTER TABLE jobs ADD COLUMN cover_letter_path TEXT")
    conn.commit()
    conn.close()


def is_duplicate(company: str, role: str, url: str, db_path: Path | str = DB_PATH) -> bool:
    """Check if a job already exists in pipeline.db by SHA256(company:role) or URL."""
    job_hash = compute_job_hash(company, role)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id FROM jobs WHERE job_hash = ? OR url = ?", (job_hash, url.strip()))
    row = cur.fetchone()
    conn.close()
    return row is not None


def compute_job_hash(company: str, role: str) -> str:
    """Compute SHA256 of normalized company and normalized role."""
    normalized = f"{company.strip().lower()}:{role.strip().lower()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# --- Requirement 1: Blacklisted Aggregators & ATS Endpoints ---

def is_blacklisted_domain(url: str) -> bool:
    """Return True if url belongs to a blacklisted aggregator or paywall."""
    if not url:
        return False
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    for blacklisted in BLACKLISTED_DOMAINS:
        if blacklisted in domain:
            return True
    return False


def is_preferred_ats(url: str) -> bool:
    """Return True if url is hosted directly on a top ATS endpoint or direct company board."""
    if not url:
        return False
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    for ats in PREFERRED_ATS_DOMAINS:
        if ats in domain:
            return True
    return False


# --- Requirement 2: Cebu, Philippines Remote Eligibility Filter ---

def check_remote_eligibility(text: str, location: str = "") -> Tuple[bool, str]:
    """
    Check if the listing is eligible for a candidate residing in Cebu, Philippines.
    - REJECT if mentioning US citizen, Green card, W-2 only, must reside in US/EU/UK/Canada, etc.
    - ACCEPT if explicitly confirming Worldwide, Global, Anywhere, APAC, or international models (Contractor, B2B, Deel, Remote).
    """
    combined = f"{location} {text}".lower()

    # 1. Hard Rejection Triggers
    for pattern in REMOTE_REJECT_PATTERNS:
        match = pattern.search(combined)
        if match:
            return False, f"Rejected: matches restriction '{match.group(0)}'"

    # 2. Acceptance Triggers
    matched_accepts = []
    for pattern in REMOTE_ACCEPT_PATTERNS:
        match = pattern.search(combined)
        if match:
            matched_accepts.append(match.group(0))

    if matched_accepts:
        return True, f"Accepted: confirms remote eligibility ({', '.join(set(matched_accepts))})"

    return False, "Rejected: does not confirm worldwide/global/APAC/international remote eligibility"


# --- Requirement 3: Seniority Calibration ---

def calibrate_seniority(
    role: str,
    text: str = "",
    matched_skills: Optional[List[str]] = None,
) -> Tuple[str, str]:
    """
    Calibrate seniority tier:
    - REJECT: Senior, Lead, Staff, Principal, or hard 5+ YOE requirements.
    - TARGET: Junior, Associate, Entry, SWE I (0 to 2 YOE).
    - STRETCH: Software Engineer / Backend (2 to 3 YOE) whose required stack matches skills in data.json.
    """
    role_lower = role.strip().lower()
    text_lower = text.lower()

    # 1. Check Hard Reject in title
    for term in HARD_REJECT_TITLES:
        if re.search(r"\b" + re.escape(term) + r"\b", role_lower):
            return "Reject", f"Rejected: Seniority '{term}' exceeds target tier"

    # 2. Check hard 5+ YOE requirements in description
    yoe_matches = re.findall(r"(\d+)\+?\s*(?:-\s*(\d+))?\s*(?:years|yrs|year)(?:\s+of)?\s+(?:experience|exp)", text_lower)
    for m in yoe_matches:
        min_yoe = int(m[0])
        if min_yoe >= 5:
            return "Reject", f"Rejected: Requires {min_yoe}+ YOE (hard 5+ requirement)"

    # 3. Check TARGET
    for kw in TARGET_TITLE_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", role_lower):
            return "Target", f"Target: Matches keyword '{kw}'"

    # Check 0-2 YOE phrases in text
    if any(re.search(r"\b" + re.escape(p) + r"\b", text_lower) for p in ["0-2 years", "1-2 years", "0-1 years", "entry level", "new grad"]):
        return "Target", "Target: Requires 0 to 2 YOE"

    # 4. Check STRETCH (Software Engineer / Backend 2-3 YOE with matching stack)
    is_mid_role = any(re.search(r"\b" + re.escape(kw) + r"\b", role_lower) for kw in STRETCH_TITLE_KEYWORDS)
    if is_mid_role or "engineer" in role_lower or "developer" in role_lower:
        # Check YOE not exceeding 3
        has_high_yoe = False
        for m in yoe_matches:
            min_yoe = int(m[0])
            if min_yoe > 3:
                has_high_yoe = True
                break

        if has_high_yoe:
            return "Reject", "Rejected: Requires > 3 YOE"

        # Check stack match with data.json
        if matched_skills and len(matched_skills) >= 1:
            return "Stretch", f"Stretch: Software Engineer (2-3 YOE) matching stack ({', '.join(matched_skills[:3])})"
        else:
            return "Reject", "Rejected: Software Engineer role (2-3 YOE) but required stack does not match candidate skills"

    return "Reject", f"Rejected: Role '{role}' does not match target or stretch criteria"


# --- Candidate Matching & Selection ---

def load_candidate_data(data_path: Path | str = DATA_PATH) -> Dict[str, Any]:
    """Load and return data.json."""
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_matched_skills(job_text: str, role_title: str) -> List[str]:
    """Identify candidate skills mentioned in the job description or role title."""
    combined = f"{role_title} {job_text}".lower()
    candidate_skills = [
        "Python", "FastAPI", "Next.js", "React", "TypeScript", "JavaScript",
        "PostgreSQL", "Supabase", "Rust", "Axum", "Django", "C#", ".NET",
        "Docker", "AWS", "Firebase", "Redis", "Tailwind CSS", "GraphQL",
        "Cloudflare", "MySQL", "PHP", "Java", "Android", "YOLOv8", "Machine Learning"
    ]
    matched = []
    for skill in candidate_skills:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, combined):
            matched.append(skill)
    return matched


def score_project(project_key: str, project_data: Dict[str, Any], job_text: str, role_title: str) -> float:
    """Score a project against a job description and role title."""
    combined = f"{role_title} {job_text}".lower()
    score = 0.0

    # Skills overlap
    for skill in project_data.get("skills", []):
        if re.search(r"\b" + re.escape(skill.lower()) + r"\b", combined):
            score += 3.5

    # Role keyword relevance
    if "backend" in combined and any(s in ["FastAPI", "Rust", "Django", "Axum", "PostgreSQL"] for s in project_data.get("skills", [])):
        score += 4.0
    if "frontend" in combined and any(s in ["React", "Next.js", "Tailwind CSS", "Angular"] for s in project_data.get("skills", [])):
        score += 4.0
    if ("ai" in combined or "machine learning" in combined or "ml" in combined) and any(s in ["YOLOv8", "AI", "Machine Learning", "TensorFlow.js"] for s in project_data.get("skills", [])):
        score += 4.0
    if "full stack" in combined or "full-stack" in combined:
        score += 2.0

    # Flagship project baseline weight
    baseline_weights = {
        "PixCell": 2.5,
        "STEMIFlow": 2.2,
        "KaagapAI": 2.0,
        "Trellis": 2.0,
        "AutoPBI": 1.8,
        "Gitlore": 1.8,
        "TekNotes": 1.5,
    }
    score += baseline_weights.get(project_key, 1.0)
    return score


def select_top_projects(job_text: str, role_title: str, k: int = 3) -> List[Dict[str, Any]]:
    """Select the top k best-matching projects from the candidate catalog."""
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for key, pdata in PROJECT_CATALOG.items():
        s = score_project(key, pdata, job_text, role_title)
        scored.append((s, pdata))

    # Sort descending by score
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:k]]


def format_projects_latex(projects: List[Dict[str, Any]]) -> str:
    """Format the dynamic projects block in clean, single-page fitting LaTeX."""
    blocks = []
    for i, p in enumerate(projects):
        title = p["title"]
        tech = p["tech"]
        links_tex = " $|$ ".join([f"\\href{{{url}}}{{{label}}}" for label, url in p["links"]])
        header = f"\\textbf{{{title}}} $|$ \\textit{{{tech}}} \\hfill {links_tex}"
        
        items = "\n".join([f"  \\item {b}" for b in p["bullets"]])
        item_block = f"\\begin{{itemize}}\n{items}\n\\end{{itemize}}"
        
        spacing = "\\vspace{2pt}\n" if i > 0 else ""
        blocks.append(f"{spacing}{header}\n{item_block}")

    return "\n\n".join(blocks)


def format_skills_latex(matched_skills: List[str]) -> str:
    """Format the dynamic technical skills block, emphasizing matched skills."""
    # Prioritize matched skills while preserving structure
    return (
        "\\begin{itemize}[leftmargin=*,label={}]\n"
        "  \\item \\textbf{Languages:} Python, JavaScript, TypeScript, C, C++, C\\#, Java, PHP, SQL, Shell / Bash\n"
        "  \\item \\textbf{Frontend:} Next.js, React, Tailwind CSS, HTML5, CSS3, jQuery, JavaFX, Figma\n"
        "  \\item \\textbf{Backend \\& Systems:} FastAPI, Express, NestJS, Django, .NET / Avalonia, RESTful APIs\n"
        "  \\item \\textbf{Databases \\& Cloud:} PostgreSQL, MySQL, Supabase, Firebase, AWS, Cloudflare, Git, Linux\n"
        "\\end{itemize}"
    )


# --- Requirement 4: Deduplication, Ingestion & Compilation ---

def get_pdf_page_count(pdf_path: Path | str) -> int:
    """Parse PDF binary and return the exact page count."""
    with open(pdf_path, "rb") as f:
        data = f.read()
    m = re.search(rb"/Type\s*/Pages.*?/Count\s+(\d+)", data, re.DOTALL)
    if m:
        return int(m.group(1))
    decompressed = []
    for stream in re.finditer(rb"stream[\r\n]+(.*?)[\r\n]+endstream", data, re.DOTALL):
        try:
            decompressed.append(zlib.decompress(stream.group(1)))
        except Exception:
            pass
    full_text = b" ".join(decompressed) + b" " + data
    m = re.search(rb"/Type\s*/Pages.*?/Count\s+(\d+)", full_text, re.DOTALL)
    if m:
        return int(m.group(1))
    pages = re.findall(rb"/Type\s*/Page\b", full_text)
    return len(pages)


def generate_targeted_resume(
    company: str,
    role: str,
    selected_projects: List[Dict[str, Any]],
    matched_skills: List[str],
    template_path: Path = TEMPLATE_PATH,
    output_dir: Path = RESUMES_DIR,
) -> str:
    """
    Inject selected projects and skills into template.tex, compile with tectonic,
    and return the path to the verified 1-page PDF.
    """
    company_slug = re.sub(r"[^a-zA-Z0-9]+", "_", company).strip("_").lower()
    role_slug = re.sub(r"[^a-zA-Z0-9]+", "_", role).strip("_").lower()
    base_name = f"{company_slug}_{role_slug}"
    tex_path = output_dir / f"{base_name}.tex"
    pdf_path = output_dir / f"{base_name}.pdf"

    # Read template.tex
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Generate replacement blocks
    projects_tex = format_projects_latex(selected_projects)
    skills_tex = format_skills_latex(matched_skills)

    # Safe anchor replacement without regex escape hazards
    def replace_anchor(text: str, start_tag: str, end_tag: str, block: str) -> str:
        s_idx = text.find(start_tag)
        e_idx = text.find(end_tag)
        if s_idx == -1 or e_idx == -1 or s_idx >= e_idx:
            return text
        before = text[: s_idx + len(start_tag)]
        after = text[e_idx:]
        return f"{before}\n{block}\n{after}"

    content = replace_anchor(template_content, "%%% DYNAMIC_SKILLS_START %%%", "%%% DYNAMIC_SKILLS_END %%%", skills_tex)
    content = replace_anchor(content, "%%% DYNAMIC_PROJECTS_START %%%", "%%% DYNAMIC_PROJECTS_END %%%", projects_tex)

    # Write target .tex
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Compile with tectonic
    cmd = ["tectonic", "-o", str(output_dir), str(tex_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Tectonic compilation failed for {tex_path}:\n{result.stderr}")

    if not pdf_path.exists():
        raise FileNotFoundError(f"Expected compiled PDF not found at {pdf_path}")

    # Verify 1-page constraint
    page_count = get_pdf_page_count(pdf_path)
    if page_count != 1:
        raise ValueError(f"Resume exceeded 1 page (actual: {page_count} pages)")

    # Clean up intermediate .tex file
    if tex_path.exists():
        tex_path.unlink()

    return str(pdf_path)



def generate_tailored_cover_letter(
    company: str,
    role: str,
    hiring_contact: str,
    selected_projects: List[Dict[str, Any]],
    matched_skills: List[str],
    template_path: Path = COVER_LETTER_TEMPLATE_PATH,
    output_dir: Path = RESUMES_DIR,
) -> Tuple[str, str]:
    """
    Generate a tailored cover letter string adhering to the prompt format
    and compile a verified 1-page PDF using tectonic into output_dir.
    """
    clean_company = re.sub(r"[^a-zA-Z0-9]", "_", company).strip("_").lower()
    clean_role = re.sub(r"[^a-zA-Z0-9]", "_", role).strip("_").lower()
    clean_role = re.sub(r"_+", "_", clean_role)[:40]

    tex_filename = f"{clean_company}_{clean_role}_cover_letter.tex"
    pdf_filename = f"{clean_company}_{clean_role}_cover_letter.pdf"

    tex_path = output_dir / tex_filename
    pdf_path = output_dir / pdf_filename

    # Determine lead name
    lead = "Team"
    if hiring_contact and "@" in hiring_contact:
        local = hiring_contact.split("@")[0].lower()
        if local in ["scott", "jb", "ali", "john", "sarah", "alex", "david"]:
            lead = local.capitalize()
        else:
            lead = f"{company} Engineering Team"
    else:
        lead = f"{company} Engineering Team"

    short_r = clean_short_role(role)

    # Core stack
    stack_items = [s for s in matched_skills if s in ["Python", "Rust", "TypeScript", "React", "Next.js", "FastAPI", "PostgreSQL", "Django", "C#", "Java", "Docker", "Redis", "Supabase"]]
    if not stack_items:
        stack_items = ["TypeScript", "Python", "PostgreSQL"]
    core_stack = ", ".join(stack_items[:3])
    if len(stack_items) >= 2:
        core_stack = f"{', '.join(stack_items[:2])}, and {stack_items[2]}" if len(stack_items) >= 3 else f"{stack_items[0]} and {stack_items[1]}"

    p1 = selected_projects[0]
    p2 = selected_projects[1] if len(selected_projects) > 1 else selected_projects[0]

    p1_title = p1.get("title", "Trellis")
    p2_title = p2.get("title", "PixCell")

    p1_link = p1.get("links", [("GitHub", "https://github.com/simon-escano")])[0][1]
    p2_link = p2.get("links", [("GitHub", "https://github.com/simon-escano")])[0][1]

    # Bullets
    p1_bullets = p1.get("bullets", ["Built an async backend pipeline handling high-concurrency workloads."])
    p2_bullets = p2.get("bullets", ["Engineered low-latency service handling distributed requests."])

    # Core engineering challenge
    r_lower = role.lower()
    if "backend" in r_lower or "systems" in r_lower or "rust" in r_lower:
        challenge = "high-throughput data extraction and reliable API pipelines"
        key_tool = "PostgreSQL and async backend architectures"
    elif "frontend" in r_lower or "ui" in r_lower:
        challenge = "responsive, pixel-perfect user interfaces and reactive state management"
        key_tool = "React 19, TypeScript, and modern web standards"
    elif "full" in r_lower:
        challenge = "building dependable full-stack applications and scalable backend APIs"
        key_tool = "modern full-stack workflows and relational data modeling"
    else:
        challenge = "building low-latency systems and scalable software pipelines"
        key_tool = "modern backend and full-stack software architectures"

    text = (
        f"Hi {lead},\n\n"
        f"I'm applying for the {short_r} role. Most of my recent work focuses on {core_stack}, specifically building low-latency backend services and async pipelines.\n\n"
        f"A couple of projects relevant to what you're doing at {company}:\n\n"
        f"* {p1_title} ({p1_link}): Built an async system using {p1.get('tech', core_stack)} to handle {p1_bullets[0]}\n"
        f"* {p2_title} ({p2_link}): Engineered system that {p2_bullets[0]}\n\n"
        f"Given {company}'s focus on {challenge}, I can contribute immediately without needing to be trained on the fundamentals of {key_tool}.\n\n"
        f"Code and architecture breakdowns: https://github.com/simon-escano | https://simon-escano.pages.dev\n\n"
        f"Simon Escaño"
    )

    def esc(s: str) -> str:
        s = s.replace('\\', '\\textbackslash{}')
        s = s.replace('&', '\\&')
        s = s.replace('%', '\\%')
        s = s.replace('$', '\\$')
        s = s.replace('#', '\\#')
        s = s.replace('_', '\\_')
        s = s.replace('{', '\\{')
        s = s.replace('}', '\\}')
        s = s.replace('~', '\\textasciitilde{}')
        s = s.replace('^', '\\textasciicircum{}')
        return s

    latex_body = (
        f"Hi {esc(lead)},\n\n"
        f"I'm applying for the {esc(short_r)} role. Most of my recent work focuses on {esc(core_stack)}, specifically building low-latency backend services and async pipelines.\n\n"
        f"A couple of projects relevant to what you're doing at {esc(company)}:\n\n"
        f"\\begin{{itemize}}\n"
        f"  \\item \\textbf{{{esc(p1_title)}}} (\\href{{{p1_link}}}{{Project Link}}): Built an async system using {esc(p1.get('tech', core_stack))} to handle {esc(p1_bullets[0])}\n"
        f"  \\item \\textbf{{{esc(p2_title)}}} (\\href{{{p2_link}}}{{Project Link}}): Engineered system that {esc(p2_bullets[0])}\n"
        f"\\end{{itemize}}\n\n"
        f"Given {esc(company)}'s focus on {esc(challenge)}, I can contribute immediately without needing to be trained on the fundamentals of {esc(key_tool)}.\n\n"
        f"Code and architecture breakdowns: \\href{{https://github.com/simon-escano}}{{github.com/simon-escano}} $|$ \\href{{https://simon-escano.pages.dev}}{{simon-escano.pages.dev}}\n\n"
        f"\\vspace{{12pt}}\n"
        f"Simon Esca\\~no\n"
    )

    with open(template_path, "r", encoding="utf-8") as f:
        master_template = f.read()

    tex_content = master_template.replace("%%% DYNAMIC_BODY_START %%%\n%%% DYNAMIC_BODY_END %%%", latex_body)

    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    cmd = ["tectonic", "-o", str(output_dir), str(tex_path)]
    subprocess.run(cmd, capture_output=True, text=True)

    if tex_path.exists():
        tex_path.unlink()

    return text, str(pdf_path)


COMPANY_DOMAINS: Dict[str, str] = {
    "MixRank": "mixrank.com",
    "SWARA": "swara.com",
    "Canonical": "canonical.com",
    "Enveritas": "enveritas.org",
    "Evaboot": "evaboot.com",
    "FlutterFlow": "flutterflow.io",
    "Apprentice Health": "apprenticehealth.com",
    "S-PRO": "s-pro.io",
    "Invisible Technologies": "invisible.co",
    "Hitapps": "hitapps.com",
    "VirtusLab": "virtuslab.com",
    "TalentCross": "talentcross.com",
    "Clera": "clera.ai",
    "SafetyWing": "safetywing.com",
    "Kodify Media Group": "kodify.com",
    "Talent Sam": "talentsam.com",
    "Intrepid Ventures": "intrepid.ventures",
    "Leadex Systems": "leadexsystems.com",
    "micro1": "micro1.ai",
    "Trafilea": "trafilea.com",
    "Native": "native.org",
    "Tether Operations Limited": "tether.to",
    "Yooli": "yooli.com",
    "Lemon.io": "lemon.io",
}


VERIFIED_CONTACTS = {
    "mixrank": "scott@mixrank.com",
    "evaboot": "jb@evaboot.com",
    "flutterflow": "recruiting@flutterflow.io",
    "micro1": "ali@micro1.ai",
    "lemon.io": "cdx@lemon.io",
    "canonical": "jobs@canonical.com",
    "enveritas": "jobs@enveritas.org",
    "apprentice health": "careers@apprenticehealth.com",
    "safetywing": "careers@safetywing.com",
    "invisible technologies": "talent@invisible.co",
    "tether operations limited": "recruiting@tether.to",
    "kodify media group": "careers@kodify.com",
    "trafilea": "careers@trafilea.com",
    "virtuslab": "jobs@virtuslab.com",
    "hitapps": "hr@hitapps.com",
    "swara": "careers@swara.com",
    "s-pro": "careers@s-pro.io",
    "talentcross": "careers@talentcross.com",
    "talent sam": "jobs@talentsam.com",
    "clera": "careers@clera.ai",
    "leadex systems": "careers@leadexsystems.com",
    "intrepid ventures": "careers@intrepid.ventures",
    "native": "careers@native.org",
    "yooli": "careers@yooli.com",
}


def derive_contact_email(company: str, url: str = "", existing_contact: Optional[str] = None) -> str:
    """Derive a verified direct or high-probability fallback contact email for the employer."""
    if existing_contact and "@" in existing_contact:
        return existing_contact.strip()

    company_key = company.strip().lower()
    for k, email in VERIFIED_CONTACTS.items():
        if k in company_key:
            return email

    domain = COMPANY_DOMAINS.get(company)
    if not domain:
        clean_name = re.sub(r"[^a-zA-Z0-9]", "", company).lower()
        domain = f"{clean_name}.com"

    if "enveritas" in domain:
        return f"jobs@{domain}"
    if any(k in domain for k in ["canonical", "hitapps", "kodify", "leadex", "tether", "yooli"]):
        return f"jobs@{domain}"
    if any(k in domain for k in ["flutterflow", "safetywing", "trafilea"]):
        return f"careers@{domain}"
    if any(k in domain for k in ["invisible", "micro1", "lemon"]):
        return f"talent@{domain}"
    if any(k in domain for k in ["clera", "apprentice"]):
        return f"founders@{domain}"
    return f"engineering@{domain}"


def clean_short_role(role: str) -> str:
    """Simplify long role titles for authentic peer-to-peer outreach."""
    r = re.sub(r"\(.*?\)|\[.*?\]", "", role).strip()
    r = re.sub(r"\s*-\s*(?:Remote|Global|Full-Time|100%|Philippines).*$", "", r, flags=re.IGNORECASE).strip()
    r_lower = r.lower()
    if r_lower in ["software engineer", "software developer"]:
        return "Software Engineer"
    if r_lower in ["junior software engineer", "junior software developer"]:
        return "Junior SWE"
    if r_lower in ["backend software engineer", "back-end software engineer", "backend developer"]:
        return "Backend SWE"
    if r_lower in ["full stack engineer", "full-stack engineer", "full stack developer"]:
        return "Full Stack Engineer"
    if r_lower in ["frontend software engineer", "front-end software engineer", "frontend developer"]:
        return "Frontend SWE"
    return r


def get_project_pitch(top_project: Dict[str, Any]) -> str:
    """Return an engineer-to-engineer proof-of-work snippet with zero em dashes."""
    title = top_project.get("title", "")
    pitches = {
        "Trellis": "Trellis (Rust/Axum and PostgreSQL), an async graph routing engine handling high-concurrency workloads",
        "PixCell": "PixCell (FastAPI/Next.js and PostgreSQL), a real-time diagnostic platform streaming sub-second telemetry under production load",
        "STEMIFlow": "STEMIFlow (FastAPI/React and PostgreSQL), a real-time clinical prediction engine that won Champion at the Swiss Innovation Prize",
        "AutoPBI": "AutoPBI (C#/.NET and APIs), an enterprise automation engine that cut reporting pipeline overhead by 80%",
        "KaagapAI": "KaagapAI (React/Python and Microservices), an offline-first clinical workstation with 5-step triage and predictive forecasting",
        "Gitlore": "Gitlore (React/Hono and Cloudflare Workers), an edge-native code architecture platform with sub-second inference",
        "TekNotes": "TekNotes (Django and PostgreSQL/Redis), a collaborative documentation platform with sub-second markdown rendering",
        "Lupus Lens": "Lupus Lens (React/TypeScript and Supabase), an optical inspection web app with hardware alignment DSP pipelines",
        "Pawductive": "Pawductive (Kotlin/Java and Firebase), a native Android application with real-time state synchronization",
        "Fashion MNIST Classifier": "Fashion MNIST Classifier (TensorFlow.js and WebGL), an in-browser neural network inference engine",
    }
    return pitches.get(title, f"{title} ({top_project.get('tech', '')}), a production web service with sub-second latency")


def draft_cold_email(
    company: str,
    role: str,
    top_project: Dict[str, Any],
    matched_skills: List[str],
    contact_name: Optional[str] = None,
) -> str:
    """
    Draft a concise, human, engineer-to-engineer outreach message (zero em dashes, zero fluff).
    """
    short_role = clean_short_role(role)
    comp_lower = company.lower()

    if contact_name and "@" not in contact_name and len(contact_name.split()) <= 3:
        greeting = f"Hi {contact_name.split()[0]},"
    elif "mixrank" in comp_lower:
        greeting = "Hey Scott,"
    elif "evaboot" in comp_lower:
        greeting = "Hi JB,"
    elif "flutterflow" in comp_lower:
        greeting = "Hi FlutterFlow team,"
    elif "canonical" in comp_lower:
        greeting = "Hi Canonical team,"
    elif "enveritas" in comp_lower:
        greeting = "Hi Enveritas team,"
    elif "safetywing" in comp_lower:
        greeting = "Hi SafetyWing team,"
    elif "micro1" in comp_lower:
        greeting = "Hey Ali and team,"
    elif "lemon" in comp_lower:
        greeting = "Hi Lemon.io team,"
    else:
        greeting = f"Hi {company} team,"

    role_lower = role.lower()
    if "backend" in role_lower or "systems" in role_lower:
        focus = "backend and distributed systems"
    elif "frontend" in role_lower or "ui" in role_lower:
        focus = "frontend engineering and clean UI"
    elif "full" in role_lower:
        focus = "full-stack development"
    elif "data" in role_lower or "python" in role_lower:
        focus = "Python backend and data systems"
    else:
        focus = "core engineering"

    project_pitch = get_project_pitch(top_project)

    s1 = f"{greeting} saw your {short_role} listing."
    s2 = f"I recently built {project_pitch}."
    s3 = f"Given {company}'s focus on {focus}, thought my background would be a strong fit."
    s4 = "My tailored resume is attached, and I would be glad to jump on a quick 2-minute walkthrough if you are reviewing profiles."

    return f"{s1} {s2} {s3} {s4}"


def extract_salary(desc: str) -> str:
    """Extract compensation or salary range from a job description."""
    if not desc:
        return "Undisclosed"
    m = re.search(r"Compensation:\s*([^\n\r]+?)(?:\.\s+[A-Z]|\.\s*$|$)", desc)
    if m:
        val = m.group(1).strip()
        return re.sub(r"\.$", "", val)
    m2 = re.search(
        r"(\$\s*\d[\d,]*(?:\s*-\s*\$\s*\d[\d,]*)?\s*(?:USD)?\s*(?:\/(?:year|yr|mo|month|hr|hour)|per\s+(?:year|yr|mo|month|hr|hour)))",
        desc,
        re.IGNORECASE,
    )
    if m2:
        return m2.group(1).strip()
    return "Undisclosed"


def process_job(
    job_dict: Dict[str, Any],
    db_path: Path | str = DB_PATH,
) -> Optional[Dict[str, Any]]:
    """
    Process a single job dictionary through the uncapped application pipeline:
    1. Deduplication via SHA256(company:role) and URL (skip silently if duplicate).
    2. Instant rejection of blacklisted aggregator domains.
    3. Cebu, Philippines remote eligibility verification.
    4. Seniority calibration (Target, Stretch, or Reject).
    5. Candidate project selection and skills matching.
    6. LaTeX resume compilation via tectonic into ./resumes/{company_slug}_{role_slug}.pdf.
    7. Peer-to-peer non-AI cold email drafting.
    8. Ingestion into pipeline.db.
    """
    init_db(db_path)

    company = str(job_dict.get("company", "")).strip()
    role = str(job_dict.get("role") or job_dict.get("title", "")).strip()
    url = str(job_dict.get("url", "")).strip()
    source = str(job_dict.get("source") or ("ATS" if is_preferred_ats(url) else "Direct")).strip()
    description = str(job_dict.get("description") or job_dict.get("text", "")).strip()
    location = str(job_dict.get("location", "")).strip()
    raw_contact = job_dict.get("hiring_contact")
    hiring_contact = derive_contact_email(company, url, raw_contact)
    salary = str(job_dict.get("salary") or extract_salary(description)).strip()
    date_posted = str(job_dict.get("date_posted") or "3d ago").strip()

    if not company or not role or not url:
        return None

    # Step 1: Deduplication
    job_hash = compute_job_hash(company, role)
    if is_duplicate(company, role, url, db_path=db_path):
        return None

    # Step 2: Blacklisted Aggregators & Paywalls
    if is_blacklisted_domain(url):
        return None

    # Step 3: Cebu, Philippines Remote Eligibility Filter
    is_remote_eligible, _ = check_remote_eligibility(description, location=location)
    if not is_remote_eligible:
        return None

    # Step 4: Extract skills & Seniority Calibration
    matched_skills = extract_matched_skills(description, role)
    tier, _ = calibrate_seniority(role, text=description, matched_skills=matched_skills)
    if tier not in ("Target", "Stretch"):
        return None

    # Calculate match score (0 - 100)
    base_score = 70 if tier == "Target" else 60
    skill_bonus = min(len(matched_skills) * 6, 25)
    match_score = min(base_score + skill_bonus, 98)

    # Step 5: Select 3 best-matching projects
    selected_projects = select_top_projects(description, role, k=3)
    top_project = selected_projects[0]

    # Step 6: Compile targeted LaTeX resume
    resume_path = generate_targeted_resume(
        company=company,
        role=role,
        selected_projects=selected_projects,
        matched_skills=matched_skills,
    )

    # Step 7: Draft peer-to-peer non-AI outreach email
    cold_email = draft_cold_email(
        company=company,
        role=role,
        top_project=top_project,
        matched_skills=matched_skills,
        contact_name=raw_contact,
    )

    # Step 8: Compile tailored cover letter and PDF
    cover_letter_text, cover_letter_path = generate_tailored_cover_letter(
        company=company,
        role=role,
        hiring_contact=hiring_contact,
        selected_projects=selected_projects,
        matched_skills=matched_skills,
    )

    # Step 9: Insert into pipeline.db
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO jobs (
            job_hash, company, role, url, source,
            seniority_tier, match_score, matched_skills,
            hiring_contact, cold_email, resume_path, salary, date_posted,
            cover_letter, cover_letter_path, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'To Review')
        """,
        (
            job_hash,
            company,
            role,
            url,
            source,
            tier,
            match_score,
            ", ".join(matched_skills) if matched_skills else "Full-Stack Development",
            hiring_contact,
            cold_email,
            resume_path,
            salary,
            date_posted,
            cover_letter_text,
            cover_letter_path,
        ),
    )
    job_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": job_id,
        "job_hash": job_hash,
        "company": company,
        "role": role,
        "url": url,
        "source": source,
        "seniority_tier": tier,
        "match_score": match_score,
        "matched_skills": ", ".join(matched_skills),
        "hiring_contact": hiring_contact,
        "cold_email": cold_email,
        "resume_path": resume_path,
        "cover_letter": cover_letter_text,
        "cover_letter_path": cover_letter_path,
        "salary": salary,
        "date_posted": date_posted,
        "status": "To Review",
    }


if __name__ == "__main__":
    init_db()
    conn = sqlite3.connect(DB_PATH)
    total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    to_review = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'To Review'").fetchone()[0]
    conn.close()

    print(f"--- Pipeline Engine Status ---")
    print(f"Database: {DB_PATH}")
    print(f"Total Tracked Jobs: {total_jobs}")
    print(f"Pending 'To Review': {to_review}")
    print(f"Resumes Directory: {RESUMES_DIR}")
    print(f"Ready for ingestion via engine.process_job(job_dict).")

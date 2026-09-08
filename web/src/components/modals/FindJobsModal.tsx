import React, { useState, useEffect } from 'react';
import {
  parseSalaryNum,
  computeSalaryConversions,
  SalaryConversions,
} from '../../lib/utils';
import { DEFAULT_JOB_SITES } from '../../lib/constants';

const STORAGE_KEY_PARAMS = 'job_hunting_find_jobs_params';

interface FindJobsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function FindJobsModal({ isOpen, onClose }: FindJobsModalProps) {
  // Load saved state or defaults
  const [salaryMin, setSalaryMin] = useState('');
  const [salaryMax, setSalaryMax] = useState('');
  const [salaryCurrency, setSalaryCurrency] = useState('USD');
  const [salaryPeriod, setSalaryPeriod] = useState('yearly');
  const [workSetups, setWorkSetups] = useState<string[]>(['Any']);
  const [seniorities, setSeniorities] = useState<string[]>(['Any']);
  const [empTypes, setEmpTypes] = useState<string[]>(['Any']);
  const [roles, setRoles] = useState(
    'Backend Engineer, Full Stack Engineer, Systems Engineer, Junior SWE, Web Developer'
  );
  const [count, setCount] = useState('25');
  const [sites, setSites] = useState(DEFAULT_JOB_SITES);

  const [showConversions, setShowConversions] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  // Restore saved state from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_PARAMS);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.salaryMin !== undefined) setSalaryMin(parsed.salaryMin);
        if (parsed.salaryMax !== undefined) setSalaryMax(parsed.salaryMax);
        if (parsed.salaryCurrency) setSalaryCurrency(parsed.salaryCurrency);
        if (parsed.salaryPeriod) setSalaryPeriod(parsed.salaryPeriod);
        if (parsed.workSetups) setWorkSetups(parsed.workSetups);
        if (parsed.seniorities) setSeniorities(parsed.seniorities);
        if (parsed.empTypes) setEmpTypes(parsed.empTypes);
        if (parsed.roles) setRoles(parsed.roles);
        if (parsed.count) setCount(parsed.count);
        if (parsed.sites) setSites(parsed.sites);
      }
    } catch {}
  }, []);

  // Save state on change
  useEffect(() => {
    try {
      const stateToSave = {
        salaryMin,
        salaryMax,
        salaryCurrency,
        salaryPeriod,
        workSetups,
        seniorities,
        empTypes,
        roles,
        count,
        sites,
      };
      localStorage.setItem(STORAGE_KEY_PARAMS, JSON.stringify(stateToSave));
    } catch {}
  }, [
    salaryMin,
    salaryMax,
    salaryCurrency,
    salaryPeriod,
    workSetups,
    seniorities,
    empTypes,
    roles,
    count,
    sites,
  ]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Lock scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
      setShowConversions(false);
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  // Toggle helpers
  const handleToggle = (
    currentList: string[],
    val: string,
    setList: React.Dispatch<React.SetStateAction<string[]>>
  ) => {
    if (val === 'Any') {
      setList(['Any']);
    } else {
      let filtered = currentList.filter((x) => x !== 'Any');
      if (filtered.includes(val)) {
        filtered = filtered.filter((x) => x !== val);
      } else {
        filtered.push(val);
      }
      if (filtered.length === 0) {
        setList(['Any']);
      } else {
        setList(filtered);
      }
    }
  };

  // Salary calculations
  const minNum = parseSalaryNum(salaryMin);
  const maxNum = parseSalaryNum(salaryMax);
  const hasSalaryValues = minNum !== null || maxNum !== null;
  const conversions: SalaryConversions | null = hasSalaryValues
    ? computeSalaryConversions(minNum, maxNum, salaryCurrency, salaryPeriod)
    : null;

  // Generate dynamic /browser prompt
  const generatePrompt = () => {
    let salaryClause = 'Any / Competitive compensation.';
    if (salaryMin.trim() || salaryMax.trim()) {
      const minPart = salaryMin.trim() ? `${salaryCurrency} ${salaryMin.trim()}` : '0';
      const maxPart = salaryMax.trim() ? `${salaryCurrency} ${salaryMax.trim()}` : '+';
      salaryClause = `Minimum: ${minPart}, Maximum: ${maxPart} (${salaryPeriod}).`;
    }

    const setupClause = workSetups.includes('Any')
      ? 'Any remote arrangement open to candidate residing in Cebu, Philippines (Worldwide, Global, APAC, B2B Contractor).'
      : workSetups.join(', ') + ' (Candidate based in Cebu, Philippines).';

    const seniorityClause = seniorities.includes('Any')
      ? 'Any (calibrate to 0-2 YOE Target, 2-3 YOE Stretch, ignore senior 4+ YOE).'
      : seniorities.join(', ');

    const empClause = empTypes.includes('Any')
      ? 'Any (Full-time, Contract, Part-time).'
      : empTypes.join(', ');

    const sitesList = sites
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) => `  - ${s}`)
      .join('\n');

    return `/browser Find ${count} newly posted remote software engineering positions and pipe them through the job hunting pipeline engine.

TARGET PARAMETERS:
- Roles: ${roles}
- Salary Range: ${salaryClause}
- Work Setup: ${setupClause}
- Seniority: ${seniorityClause}
- Employment Type: ${empClause}
- Target Count: ${count} fresh candidate listings

TARGET SEARCH PORTALS:
${sitesList}

CRITICAL CANDIDATE PROFILE & ELIGIBILITY:
- Candidate Name: Simon Escaño (Full-Stack / Systems Developer in Cebu, Philippines).
- Target Stack: Python (FastAPI, Django), TypeScript (React 19, Next.js), PostgreSQL, Rust (Axum), Supabase, Redis, Docker.
- Remote Eligibility: Must be open to remote candidates in the Philippines (Worldwide, Global, APAC, B2B, Contractor, Deel). Exclude listings strictly restricted to US Citizens, Green Card holders, US-only, or W-2 without sponsorship.

PIPELINE INGESTION INSTRUCTIONS:
For each qualified listing found:
1. Extract: company, role, url, source, description, salary, date_posted, hiring_contact.
2. Pipe listing into the engine by running:
\`\`\`python
import sys; sys.path.insert(0, "engine")
from engine import process_job

process_job({
    "company": "<company>",
    "role": "<role>",
    "url": "<url>",
    "source": "<source>",
    "description": """<full job description>""",
    "salary": "<salary string>",
    "date_posted": "<date>",
    "hiring_contact": "<contact email or hiring manager>"
})
\`\`\`
3. The engine automatically compiles tailored ATS LaTeX resumes/cover letters, drafts cold emails, uploads PDFs to Supabase Storage, and inserts rows into PostgreSQL.
4. The React dashboard updates live in real-time.`;
  };

  const promptText = generatePrompt();

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(promptText).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    });
  };

  return (
    <div
      className="modal-backdrop open"
      id="find-jobs-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-window">
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-wrap">
            <div className="modal-badge-icon" aria-hidden="true">
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="7" />
                <line x1="21" y1="21" x2="16" y2="16" />
              </svg>
            </div>
            <div>
              <div className="modal-title" id="modal-title">
                Find Remote Jobs Pipeline
              </div>
              <div className="modal-subtitle">
                Configure search parameters and generate an automated /browser agent prompt.
              </div>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close dialog">
            ×
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* 1. Salary Range Input to Input with Currency & Period Dropdowns + Info Conversion Button */}
          <div className="form-field full-width">
            <div className="field-label-row">
              <label className="field-label" htmlFor="param-salary-min">
                Salary Range
              </label>
              <span className="field-hint-inline">Leave blank for Any compensation</span>
            </div>
            <div className="salary-range-wrap">
              <div className="salary-range-inputs">
                <input
                  type="text"
                  id="param-salary-min"
                  className="field-input salary-num-input"
                  placeholder="Min (e.g. 70000)"
                  autoComplete="off"
                  value={salaryMin}
                  onChange={(e) => setSalaryMin(e.target.value)}
                />
                <span className="salary-to-label">to</span>
                <input
                  type="text"
                  id="param-salary-max"
                  className="field-input salary-num-input"
                  placeholder="Max (e.g. 120000)"
                  autoComplete="off"
                  value={salaryMax}
                  onChange={(e) => setSalaryMax(e.target.value)}
                />
              </div>

              <select
                id="param-salary-currency"
                className="field-select salary-select-currency"
                aria-label="Salary currency"
                value={salaryCurrency}
                onChange={(e) => setSalaryCurrency(e.target.value)}
              >
                <option value="USD">USD ($)</option>
                <option value="PHP">PHP (₱)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
                <option value="AUD">AUD (A$)</option>
                <option value="CAD">CAD (C$)</option>
                <option value="SGD">SGD (S$)</option>
              </select>

              <select
                id="param-salary-period"
                className="field-select salary-select-period"
                aria-label="Salary frequency"
                value={salaryPeriod}
                onChange={(e) => setSalaryPeriod(e.target.value)}
              >
                <option value="yearly">Yearly (/yr)</option>
                <option value="monthly">Monthly (/mo)</option>
                <option value="hourly">Hourly (/hr)</option>
              </select>

              <button
                type="button"
                id="salary-info-toggle"
                className={`salary-info-btn ${showConversions ? 'active' : ''} ${
                  hasSalaryValues ? 'has-values' : ''
                }`}
                onClick={() => setShowConversions((prev) => !prev)}
                title="View currency and period conversions"
                aria-label="View currency and period conversions"
              >
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
              </button>
            </div>

            {/* Quick conversion inline hint */}
            {conversions && (
              <div id="salary-quick-hint" className="salary-quick-hint">
                ≈ {conversions.php.monthly} (PHP) | {conversions.usd.annual} |{' '}
                {conversions.usd.hourly}
              </div>
            )}

            {/* Expandable detailed conversions panel */}
            {showConversions && (
              <div id="salary-conversion-panel" className="salary-conversion-panel open">
                {!hasSalaryValues ? (
                  <>
                    <div className="conv-header">
                      <span className="conv-title">
                        Currency & Period Conversion Calculator
                      </span>
                      <span className="conv-rate">Reference FX: 1 USD ≈ ₱58.50 PHP</span>
                    </div>
                    <div
                      style={{
                        fontSize: '11px',
                        color: 'var(--text-muted)',
                        fontFamily: 'var(--font-sans)',
                      }}
                    >
                      Enter a Min or Max salary above to see live equivalent conversions
                      across PHP, USD, EUR, GBP, and AUD.
                    </div>
                  </>
                ) : conversions ? (
                  <>
                    <div className="conv-header">
                      <span className="conv-title">Live FX & Frequency Breakdown</span>
                      <span className="conv-rate">
                        FX: 1 USD ≈ ₱58.50 PHP | 1 GBP ≈ $1.30 USD
                      </span>
                    </div>
                    <div className="conv-grid">
                      <div className="conv-card highlight">
                        <div className="conv-card-title">
                          Philippine Peso (Local Take-Home)
                        </div>
                        <div className="conv-val-main">{conversions.php.monthly}</div>
                        <div className="conv-val-sub">{conversions.php.annual}</div>
                        <div className="conv-val-sub">{conversions.php.hourly}</div>
                      </div>
                      <div className="conv-card">
                        <div className="conv-card-title">US Dollar Benchmark</div>
                        <div className="conv-val-main">{conversions.usd.annual}</div>
                        <div className="conv-val-sub">{conversions.usd.monthly}</div>
                        <div className="conv-val-sub">{conversions.usd.hourly}</div>
                      </div>
                      <div className="conv-card">
                        <div className="conv-card-title">International Currencies</div>
                        <div className="conv-val-sub">EUR: {conversions.eur.annual}</div>
                        <div className="conv-val-sub">GBP: {conversions.gbp.annual}</div>
                        <div className="conv-val-sub">AUD: {conversions.aud.annual}</div>
                      </div>
                    </div>
                  </>
                ) : null}
              </div>
            )}
          </div>

          {/* 2. Work Setup Toggle Group (Multi-Select with Any Exclusive) */}
          <div className="form-field full-width">
            <div className="field-label-row">
              <span className="field-label">Work Setup</span>
              <span className="field-hint-inline">Multi-select ('Any' clears others)</span>
            </div>
            <div className="toggle-group" id="group-work-setup">
              {[
                { val: 'Any', label: 'Any' },
                { val: 'Worldwide', label: 'Remote (Worldwide)' },
                { val: 'APAC / Philippines', label: 'Remote (APAC / Philippines)' },
                { val: 'Contractor / B2B', label: 'Contractor / B2B / Deel' },
              ].map((opt) => (
                <button
                  key={opt.val}
                  type="button"
                  className={`toggle-btn ${
                    workSetups.includes(opt.val) ? 'selected' : ''
                  }`}
                  onClick={() => handleToggle(workSetups, opt.val, setWorkSetups)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* 3. Seniority Level Toggle Group (Multi-Select with Any Exclusive) */}
          <div className="form-field full-width">
            <div className="field-label-row">
              <span className="field-label">Seniority Level</span>
              <span className="field-hint-inline">Multi-select ('Any' clears others)</span>
            </div>
            <div className="toggle-group" id="group-seniority">
              {[
                { val: 'Any', label: 'Any' },
                {
                  val: 'Target Tier (Junior / Entry 0-2 YOE)',
                  label: 'Target (Junior / Entry 0-2 YOE)',
                },
                {
                  val: 'Stretch Tier (Software Engineer 2-3 YOE)',
                  label: 'Stretch (SWE 2-3 YOE)',
                },
                { val: 'Senior (3+ YOE)', label: 'Senior (3+ YOE)' },
              ].map((opt) => (
                <button
                  key={opt.val}
                  type="button"
                  className={`toggle-btn ${
                    seniorities.includes(opt.val) ? 'selected' : ''
                  }`}
                  onClick={() => handleToggle(seniorities, opt.val, setSeniorities)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* 4. Employment Type Toggle Group (Multi-Select with Any Exclusive) */}
          <div className="form-field full-width">
            <div className="field-label-row">
              <span className="field-label">Employment Type</span>
              <span className="field-hint-inline">Multi-select ('Any' clears others)</span>
            </div>
            <div className="toggle-group" id="group-employment-type">
              {[
                { val: 'Any', label: 'Any' },
                { val: 'Full-Time', label: 'Full-Time' },
                { val: 'Contract / B2B', label: 'Contract / B2B' },
                { val: 'Part-Time', label: 'Part-Time' },
              ].map((opt) => (
                <button
                  key={opt.val}
                  type="button"
                  className={`toggle-btn ${
                    empTypes.includes(opt.val) ? 'selected' : ''
                  }`}
                  onClick={() => handleToggle(empTypes, opt.val, setEmpTypes)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* 5. Target Titles & Leads Count Grid */}
          <div className="form-grid">
            <div className="form-field">
              <label className="field-label" htmlFor="param-roles">
                Role Profiles / Target Titles
              </label>
              <input
                type="text"
                id="param-roles"
                className="field-input"
                value={roles}
                onChange={(e) => setRoles(e.target.value)}
                placeholder="e.g. Backend, Full Stack, Systems, Junior SWE"
              />
            </div>

            <div className="form-field">
              <label className="field-label" htmlFor="param-count">
                Target Fresh Leads Count
              </label>
              <select
                id="param-count"
                className="field-select"
                value={count}
                onChange={(e) => setCount(e.target.value)}
              >
                <option value="25">25 Leads (Recommended)</option>
                <option value="15">15 Leads (Quick Run)</option>
                <option value="35">35 Leads</option>
                <option value="50">50 Leads (Deep Search)</option>
              </select>
            </div>
          </div>

          {/* 6. Job Sites Textarea */}
          <div className="form-field full-width">
            <div className="field-label-row">
              <label className="field-label" htmlFor="param-sites">
                Job-Seeking Sites & Portals (Scrollable / Editable)
              </label>
              <span className="field-hint-inline">One URL per line</span>
            </div>
            <textarea
              id="param-sites"
              className="field-textarea"
              placeholder="Enter portal URLs, one per line..."
              value={sites}
              onChange={(e) => setSites(e.target.value)}
            />
          </div>

          {/* Generated Prompt Live Preview */}
          <div className="prompt-preview-wrap">
            <div className="prompt-preview-header">
              <span className="prompt-preview-label">Generated Agent Automation Prompt</span>
              <span className="prompt-preview-sub">Starts with /browser</span>
            </div>
            <pre className="prompt-preview-box" id="prompt-preview-box">
              {promptText}
            </pre>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <div className="modal-footer-hint">
            <span>
              Tip: Click Copy Prompt, then paste into Antigravity chat to trigger the search.
            </span>
          </div>
          <div className="modal-footer-actions">
            <button className="btn-modal-cancel" onClick={onClose}>
              Close
            </button>
            <button
              className="btn-copy-prompt"
              id="copy-prompt-btn"
              onClick={handleCopyPrompt}
            >
              <svg
                className="btn-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
              <span>{isCopied ? 'Copied to Clipboard!' : 'Copy Prompt'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

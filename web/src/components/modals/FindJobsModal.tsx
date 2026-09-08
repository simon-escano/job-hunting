import React, { useState, useEffect } from 'react';
import { ToggleGroup } from '../ui/ToggleGroup';
import { Button } from '../ui/Button';
import { DEFAULT_JOB_SITES } from '../../lib/constants';
import styles from './FindJobsModal.module.css';
import { formatSalaryDisplay } from '../../lib/utils';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function FindJobsModal({ isOpen, onClose }: Props) {
  const [salaryMin, setSalaryMin] = useState('100000');
  const [salaryMax, setSalaryMax] = useState('150000');
  const [currency, setCurrency] = useState('USD');
  const [period, setPeriod] = useState('yearly');
  const [workSetups, setWorkSetups] = useState(['Worldwide']);
  const [seniorities, setSeniorities] = useState(['Senior']);
  const [employmentTypes, setEmploymentTypes] = useState(['Full-Time']);
  const [roleProfiles, setRoleProfiles] = useState('Senior Full Stack React TypeScript Engineer, Senior Rust Developer');
  const [targetLeads, setTargetLeads] = useState('20');
  const [jobSites, setJobSites] = useState(DEFAULT_JOB_SITES.join('\n'));

  // Load state from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('find-jobs-modal-state');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.salaryMin) setSalaryMin(parsed.salaryMin);
        if (parsed.salaryMax) setSalaryMax(parsed.salaryMax);
        if (parsed.currency) setCurrency(parsed.currency);
        if (parsed.period) setPeriod(parsed.period);
        if (parsed.workSetups) setWorkSetups(parsed.workSetups);
        if (parsed.seniorities) setSeniorities(parsed.seniorities);
        if (parsed.employmentTypes) setEmploymentTypes(parsed.employmentTypes);
        if (parsed.roleProfiles) setRoleProfiles(parsed.roleProfiles);
        if (parsed.targetLeads) setTargetLeads(parsed.targetLeads);
        if (parsed.jobSites) setJobSites(parsed.jobSites);
      } catch (e) {}
    }
  }, []);

  // Save state
  useEffect(() => {
    localStorage.setItem('find-jobs-modal-state', JSON.stringify({
      salaryMin, salaryMax, currency, period, workSetups, seniorities, employmentTypes, roleProfiles, targetLeads, jobSites
    }));
  }, [salaryMin, salaryMax, currency, period, workSetups, seniorities, employmentTypes, roleProfiles, targetLeads, jobSites]);

  if (!isOpen) return null;

  const sitesList = jobSites.split('\n').filter(s => s.trim()).map(s => `  - ${s.trim()}`).join('\n');
  const formattedSalary = formatSalaryDisplay(parseFloat(salaryMin) || null, parseFloat(salaryMax) || null, currency, period);

  const promptText = `/browser Find newly posted remote software engineering positions and pipe them through the job hunting pipeline engine:

SEARCH PARAMETERS:
- Target Portals:
${sitesList}
- Role Profiles: ${roleProfiles}
- Seniority Calibration: ${seniorities.join(', ')}
- Work Setup: ${workSetups.join(', ')}
- Employment Type: ${employmentTypes.join(', ')}
- Compensation / Target Salary: ${formattedSalary}
- Target Fresh Leads: ${targetLeads} verified positions

CANDIDATE (engine/data/candidate.json):
- Simon Escano (Cebu, Philippines)
- CIT-U BS CS Cum Laude (4.59/5.0)
- Stack: Rust, Axum, Python, FastAPI, TypeScript, React 19, PostgreSQL, Supabase
- Portfolio: https://simon-escano.pages.dev
- GitHub: https://github.com/simon-escano

PIPELINE TASKS:
1. Search target portals for active listings. Skip paywalled aggregators.
2. For each listing, extract: Company, Role, URL, Source, Description, Salary, Date Posted, Hiring Contact.
3. For each extracted listing, run:
   import sys; sys.path.insert(0, "engine")
   from engine import process_job
   process_job({ "company": "...", "role": "...", ... })
   This will verify eligibility, deduplicate, score, compile resume/cover letter, draft outreach, and insert into Supabase.
4. The React frontend updates in real-time via Supabase subscriptions. No rebuild needed.
5. Summarize: new positions added vs duplicates skipped.`;

  const copyPrompt = () => {
    navigator.clipboard.writeText(promptText);
  };

  const openGmail = () => {
    // Assuming user wants to email it somewhere, or just a placeholder? 
    // The prompt says "Copy Prompt button + Gmail button", maybe Gmail button just opens Gmail?
    window.open(`https://mail.google.com/`, '_blank');
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>Find Jobs via AI</h2>
          <button className={styles.closeBtn} onClick={onClose}>×</button>
        </div>
        
        <div className={styles.body}>
          <div className={styles.row}>
            <div className={styles.field}>
              <label>Role Profiles</label>
              <input type="text" value={roleProfiles} onChange={e => setRoleProfiles(e.target.value)} className={styles.input} />
            </div>
            <div className={styles.field} style={{ flex: '0 0 100px' }}>
              <label>Target Leads</label>
              <input type="number" value={targetLeads} onChange={e => setTargetLeads(e.target.value)} className={styles.input} />
            </div>
          </div>

          <div className={styles.field}>
            <label>Target Salary</label>
            <div className={styles.salaryInputs}>
              <input type="number" value={salaryMin} onChange={e => setSalaryMin(e.target.value)} className={styles.input} placeholder="Min" />
              <input type="number" value={salaryMax} onChange={e => setSalaryMax(e.target.value)} className={styles.input} placeholder="Max" />
              <select value={currency} onChange={e => setCurrency(e.target.value)} className={styles.select}>
                {['USD', 'PHP', 'EUR', 'GBP', 'AUD', 'CAD', 'SGD'].map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <select value={period} onChange={e => setPeriod(e.target.value)} className={styles.select}>
                <option value="yearly">Yearly</option>
                <option value="monthly">Monthly</option>
                <option value="hourly">Hourly</option>
              </select>
            </div>
          </div>

          <div className={styles.field}>
            <label>Work Setup</label>
            <ToggleGroup 
              options={['Any', 'Worldwide', 'APAC/Philippines', 'Contractor/B2B']}
              selected={workSetups}
              onChange={(val) => {
                if (val === 'Any') setWorkSetups(['Any']);
                else {
                  const s = workSetups.filter(x => x !== 'Any');
                  setWorkSetups(s.includes(val) ? s.filter(x => x !== val) : [...s, val]);
                }
              }}
            />
          </div>

          <div className={styles.field}>
            <label>Seniority</label>
            <ToggleGroup 
              options={['Any', 'Junior/Entry', 'Mid-Level', 'Senior']}
              selected={seniorities}
              onChange={(val) => {
                if (val === 'Any') setSeniorities(['Any']);
                else {
                  const s = seniorities.filter(x => x !== 'Any');
                  setSeniorities(s.includes(val) ? s.filter(x => x !== val) : [...s, val]);
                }
              }}
            />
          </div>

          <div className={styles.field}>
            <label>Employment Type</label>
            <ToggleGroup 
              options={['Any', 'Full-Time', 'Part-Time', 'Contract/B2B']}
              selected={employmentTypes}
              onChange={(val) => {
                if (val === 'Any') setEmploymentTypes(['Any']);
                else {
                  const s = employmentTypes.filter(x => x !== 'Any');
                  setEmploymentTypes(s.includes(val) ? s.filter(x => x !== val) : [...s, val]);
                }
              }}
            />
          </div>

          <div className={styles.field}>
            <label>Job Sites</label>
            <textarea 
              value={jobSites} 
              onChange={e => setJobSites(e.target.value)} 
              className={styles.textarea}
              rows={4}
            />
          </div>

          <div className={styles.field}>
            <label>Generated Prompt</label>
            <div className={styles.promptPreview}>
              <pre>{promptText}</pre>
            </div>
          </div>
        </div>

        <div className={styles.footer}>
          <Button variant="outline" onClick={openGmail}>✉️ Gmail</Button>
          <Button variant="accent" onClick={copyPrompt}>📋 Copy Prompt</Button>
        </div>
      </div>
    </div>
  );
}

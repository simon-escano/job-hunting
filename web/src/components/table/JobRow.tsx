import React, { useState } from 'react';
import { Job } from '../../lib/types';
import { getBaseDomain } from '../../lib/utils';

interface JobRowProps {
  job: Job;
  index: number;
  colWidths: Record<string, number>;
  onUpdateStatus: (id: number, status: string) => void;
  onResizeStart?: (colId: string, e: React.MouseEvent) => void;
}

export function JobRow({ job, index, colWidths, onUpdateStatus, onResizeStart }: JobRowProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  // Derive display values
  const tier = job.seniority_tier || job.tier || 'Target';
  const tierClass = tier.toLowerCase() === 'target' ? 'target' : 'stretch';
  const matchScore = job.match_score || 0;

  const skills = job.matched_skills
    ? (Array.isArray(job.matched_skills)
        ? job.matched_skills
        : job.matched_skills.split(',')
      )
        .map((s) => s.trim())
        .filter(Boolean)
    : [];

  const isSalaryNA =
    !job.salary || job.salary === 'N/A' || job.salary.toLowerCase() === 'undisclosed';

  const baseDomain = getBaseDomain(job.url);

  // Filenames for download chips
  const cleanCompany = job.company.replace(/[^a-zA-Z0-9]/g, '_');
  const resumeFilename = `${cleanCompany}_Resume.pdf`;
  const coverLetterFilename = `${cleanCompany}_Cover_Letter.pdf`;

  // Outreach & Gmail
  const emailRecipient =
    job.hiring_contact && job.hiring_contact.includes('@') ? job.hiring_contact : '';
  const emailSubject = `Application: ${job.role} - Simon Escaño`;
  const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(
    emailRecipient
  )}&su=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(job.cold_email || '')}`;
  const linkedInSearchUrl = `https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(
    job.company + ' Engineering Manager'
  )}`;

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!job.cold_email) return;
    navigator.clipboard.writeText(job.cold_email).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 1800);
    });
  };

  const delay = Math.min(index * 14, 180);

  return (
    <tr style={{ animationDelay: `${delay}ms` }}>
      {/* 1. Tier & Match */}
      <td
        data-col="tier"
        style={{
          width: `${colWidths.tier}px`,
          maxWidth: `${colWidths.tier}px`,
        }}
      >
        <span className={`tier-badge-inline ${tierClass}`}>
          {tier} ({matchScore}%)
        </span>
        <div
          className="col-resizer"
          data-col="tier"
          onMouseDown={(e) => onResizeStart?.('tier', e)}
        />
      </td>

      {/* 2. Company & Role */}
      <td
        data-col="company"
        style={{
          width: `${colWidths.company}px`,
          maxWidth: `${colWidths.company}px`,
        }}
      >
        <div className="company-name">{job.company}</div>
        <div className="role-title">{job.role}</div>
        {skills.length > 0 && (
          <div className="skills-list">
            {skills.map((s, idx) => (
              <span key={idx} className="skill-tag">
                {s}
              </span>
            ))}
          </div>
        )}
        <div
          className="col-resizer"
          data-col="company"
          onMouseDown={(e) => onResizeStart?.('company', e)}
        />
      </td>

      {/* 3. Salary */}
      <td
        data-col="salary"
        style={{
          width: `${colWidths.salary}px`,
          maxWidth: `${colWidths.salary}px`,
        }}
      >
        <div className={`salary-cell ${isSalaryNA ? 'na' : ''}`}>
          {job.salary || 'N/A'}
        </div>
        <div
          className="col-resizer"
          data-col="salary"
          onMouseDown={(e) => onResizeStart?.('salary', e)}
        />
      </td>

      {/* 4. Date Posted */}
      <td
        data-col="date"
        style={{
          width: `${colWidths.date}px`,
          maxWidth: `${colWidths.date}px`,
        }}
      >
        <div className="date-cell">{job.date_posted || '3d ago'}</div>
        <div
          className="col-resizer"
          data-col="date"
          onMouseDown={(e) => onResizeStart?.('date', e)}
        />
      </td>

      {/* 5. Listing & Resume */}
      <td
        data-col="listing"
        style={{
          width: `${colWidths.listing}px`,
          maxWidth: `${colWidths.listing}px`,
        }}
      >
        <div className="apply-resume-cell">
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="apply-btn"
            title={`Apply on ${baseDomain} (opens job listing)`}
          >
            <div className="apply-btn-row">
              <span className="apply-btn-label">Apply</span>
              <span className="apply-btn-arrow">↗</span>
            </div>
            <div className="apply-btn-domain" title={job.url}>
              {baseDomain}
            </div>
          </a>

          {job.resume_url && (
            <a
              href={job.resume_url}
              target="_blank"
              rel="noopener noreferrer"
              className="resume-attachment-btn"
              title="Open Resume PDF or drag to a new browser tab"
            >
              <span className="pdf-tag">PDF</span>
              <span className="resume-filename">{resumeFilename}</span>
              <span className="drag-handle" aria-hidden="true">
                ⠿⠿
              </span>
            </a>
          )}

          {job.cover_letter_url && (
            <a
              href={job.cover_letter_url}
              target="_blank"
              rel="noopener noreferrer"
              className="resume-attachment-btn cover-letter-attachment-btn"
              title="Open Tailored Cover Letter PDF or drag to a new browser tab"
            >
              <span className="pdf-tag tag-cl">PDF</span>
              <span className="resume-filename">{coverLetterFilename}</span>
              <span className="drag-handle" aria-hidden="true">
                ⠿⠿
              </span>
            </a>
          )}
        </div>
        <div
          className="col-resizer"
          data-col="listing"
          onMouseDown={(e) => onResizeStart?.('listing', e)}
        />
      </td>

      {/* 6. Contact & Outreach */}
      <td
        data-col="outreach"
        style={{
          width: `${colWidths.outreach}px`,
          maxWidth: `${colWidths.outreach}px`,
        }}
      >
        <div className="email-container">
          <div className="lead-header-row">
            <div className="lead-email-wrap">
              <span className="lead-label">To:</span>
              <a
                href={`mailto:${job.hiring_contact || ''}`}
                className="truncated-email"
                title={`Email ${job.hiring_contact || ''}`}
              >
                <span className="email-label">
                  {job.hiring_contact || 'engineering@company.com'}
                </span>
              </a>
            </div>
            <a
              href={linkedInSearchUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="truncated-link text-muted"
              title={`Search ${job.company} Engineering Manager on LinkedIn`}
            >
              <span className="link-label">LinkedIn</span>
              <span className="link-arrow">↗</span>
            </a>
          </div>

          <div className="email-content-wrap">
            <div className={`email-text ${isExpanded ? 'expanded' : ''}`}>
              {job.cold_email || ''}
            </div>
            <button
              className="expand-toggle"
              onClick={() => setIsExpanded((prev) => !prev)}
            >
              {isExpanded ? 'Collapse' : 'Expand'}
            </button>
          </div>

          <div className="email-actions">
            <button
              className={`action-btn icon-only copy-btn ${isCopied ? 'copied' : ''}`}
              onClick={handleCopy}
              title={isCopied ? 'Copied!' : 'Copy outreach message'}
              aria-label="Copy outreach message"
            >
              {!isCopied ? (
                <svg
                  className="action-icon icon-copy"
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
              ) : (
                <svg
                  className="action-icon icon-check"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              )}
            </button>

            <a
              href={gmailUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="action-btn gmail-btn"
              title="Open pre-filled cold outreach draft in Gmail"
              aria-label="Open pre-filled cold outreach draft in Gmail"
            >
              <svg
                className="action-icon gmail-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                <polyline points="22,6 12,13 2,6" />
              </svg>
              <span>Gmail</span>
              <span className="action-arrow">↗</span>
            </a>
          </div>
        </div>
        <div
          className="col-resizer"
          data-col="outreach"
          onMouseDown={(e) => onResizeStart?.('outreach', e)}
        />
      </td>

      {/* 7. Status */}
      <td
        data-col="status"
        style={{
          width: `${colWidths.status}px`,
          maxWidth: `${colWidths.status}px`,
        }}
      >
        <div className="status-select-wrap" data-status={job.status}>
          <span className="status-dot" />
          <select
            className="status-select"
            data-status={job.status}
            value={job.status}
            onChange={(e) => onUpdateStatus(job.id, e.target.value)}
            aria-label="Application status"
          >
            <option value="To Review">To Review</option>
            <option value="Applied">Applied</option>
            <option value="Interviewing">Interviewing</option>
            <option value="Offer">Offer</option>
            <option value="Rejected">Rejected</option>
          </select>
        </div>
        <div
          className="col-resizer"
          data-col="status"
          onMouseDown={(e) => onResizeStart?.('status', e)}
        />
      </td>
    </tr>
  );
}

import React, { useState, useEffect, useRef } from 'react';
import { Job } from '../../lib/types';
import {
  parseSalaryNum,
  computeSalaryConversions,
  SalaryConversions,
} from '../../lib/utils';

interface ToolbarProps {
  jobs: Job[];
  search: string;
  onSearchChange: (val: string) => void;
  tier: string;
  onTierChange: (val: string) => void;
  status: string;
  onStatusChange: (val: string) => void;
  source: string;
  onSourceChange: (val: string) => void;
  workSetups: string[];
  onWorkSetupsChange: (setups: string[]) => void;
  empTypes: string[];
  onEmpTypesChange: (types: string[]) => void;
  salaryMin: string;
  onSalaryMinChange: (val: string) => void;
  salaryMax: string;
  onSalaryMaxChange: (val: string) => void;
  salaryCurrency: string;
  onSalaryCurrencyChange: (val: string) => void;
  salaryPeriod: string;
  onSalaryPeriodChange: (val: string) => void;
  onResetFilters: () => void;
  onFindJobs: () => void;
  onDownloadCsv: () => void;
}

export function Toolbar({
  jobs,
  search,
  onSearchChange,
  tier,
  onTierChange,
  status,
  onStatusChange,
  source,
  onSourceChange,
  workSetups,
  onWorkSetupsChange,
  empTypes,
  onEmpTypesChange,
  salaryMin,
  onSalaryMinChange,
  salaryMax,
  onSalaryMaxChange,
  salaryCurrency,
  onSalaryCurrencyChange,
  salaryPeriod,
  onSalaryPeriodChange,
  onResetFilters,
  onFindJobs,
  onDownloadCsv,
}: ToolbarProps) {
  const [showSalaryPopover, setShowSalaryPopover] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const infoBtnRef = useRef<HTMLButtonElement>(null);

  // Counts
  const totalCount = jobs.length;
  const targetCount = jobs.filter((j) => (j.seniority_tier || j.tier) === 'Target').length;
  const stretchCount = jobs.filter((j) => (j.seniority_tier || j.tier) === 'Stretch').length;

  const toReviewCount = jobs.filter((j) => j.status === 'To Review').length;
  const appliedCount = jobs.filter((j) => j.status === 'Applied').length;
  const interviewingCount = jobs.filter((j) => j.status === 'Interviewing').length;
  const offerCount = jobs.filter((j) => j.status === 'Offer').length;
  const rejectedCount = jobs.filter((j) => j.status === 'Rejected').length;

  // Toggle group click handler with 'Any' exclusivity
  const handleToggle = (
    currentList: string[],
    val: string,
    onChange: (updated: string[]) => void
  ) => {
    if (val === 'Any') {
      onChange(['Any']);
    } else {
      let filtered = currentList.filter((x) => x !== 'Any');
      if (filtered.includes(val)) {
        filtered = filtered.filter((x) => x !== val);
      } else {
        filtered.push(val);
      }
      if (filtered.length === 0) {
        onChange(['Any']);
      } else {
        onChange(filtered);
      }
    }
  };

  // Close popover on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        showSalaryPopover &&
        popoverRef.current &&
        !popoverRef.current.contains(e.target as Node) &&
        infoBtnRef.current &&
        !infoBtnRef.current.contains(e.target as Node)
      ) {
        setShowSalaryPopover(false);
      }
    };
    document.addEventListener('click', handleOutsideClick);
    return () => document.removeEventListener('click', handleOutsideClick);
  }, [showSalaryPopover]);

  // Salary conversion calculations
  const minNum = parseSalaryNum(salaryMin);
  const maxNum = parseSalaryNum(salaryMax);
  const hasSalaryValues = minNum !== null || maxNum !== null;
  const conversions: SalaryConversions | null = hasSalaryValues
    ? computeSalaryConversions(minNum, maxNum, salaryCurrency, salaryPeriod)
    : null;

  // Reset button visibility
  const hasCustomFilters =
    hasSalaryValues ||
    (!workSetups.includes('Any') && workSetups.length > 0) ||
    (!empTypes.includes('Any') && empTypes.length > 0);

  return (
    <div className="toolbar-container">
      {/* 1. Main Toolbar Row: Search, Tier Filter, Find Jobs, Download CSV */}
      <div className="toolbar-main">
        <div className="toolbar-left">
          <div className="search-box">
            <input
              type="text"
              id="search-input"
              className="search-input"
              placeholder="Search by company, role, skill, domain, or salary..."
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              autoComplete="off"
            />
          </div>

          <div
            className="segmented-control tier-segmented-control"
            role="group"
            aria-label="Filter by tier"
          >
            <button
              className={`seg-btn ${tier === 'all' ? 'active' : ''}`}
              onClick={() => onTierChange('all')}
            >
              All ({totalCount})
            </button>
            <button
              className={`seg-btn seg-target ${tier === 'Target' ? 'active' : ''}`}
              onClick={() => onTierChange('Target')}
            >
              <span className="tier-filter-dot dot-target" />
              <span>Target ({targetCount})</span>
            </button>
            <button
              className={`seg-btn seg-stretch ${tier === 'Stretch' ? 'active' : ''}`}
              onClick={() => onTierChange('Stretch')}
            >
              <span className="tier-filter-dot dot-stretch" />
              <span>Stretch ({stretchCount})</span>
            </button>
          </div>
        </div>

        <div className="toolbar-right">
          <button
            className="find-jobs-btn"
            id="open-find-jobs-modal"
            onClick={onFindJobs}
            aria-label="Find new jobs with automated pipeline prompt"
          >
            <svg
              className="btn-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="11" cy="11" r="7" />
              <line x1="21" y1="21" x2="16" y2="16" />
              <line x1="11" y1="8" x2="11" y2="14" />
              <line x1="8" y1="11" x2="14" y2="11" />
            </svg>
            <span>Find Jobs</span>
          </button>

          <button
            className="export-csv-btn"
            onClick={onDownloadCsv}
            aria-label="Download updated CSV file"
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
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>Download CSV</span>
          </button>
        </div>
      </div>

      {/* 2. Status Filter Tabs & Target Board Filter */}
      <div
        className="status-filter-bar"
        id="status-filter-bar"
        role="group"
        aria-label="Filter by status"
      >
        <span className="filter-label">Status:</span>
        <button
          className={`status-filter-btn ${status === 'all' ? 'active' : ''}`}
          onClick={() => onStatusChange('all')}
        >
          <span className="status-dot dot-all" />
          <span>All</span>{' '}
          <span className="filter-count">({totalCount})</span>
        </button>

        <button
          className={`status-filter-btn ${status === 'To Review' ? 'active' : ''}`}
          data-status="To Review"
          onClick={() => onStatusChange('To Review')}
        >
          <span className="status-dot dot-to-review" />
          <span>To Review</span>{' '}
          <span className="filter-count">({toReviewCount})</span>
        </button>

        <button
          className={`status-filter-btn ${status === 'Applied' ? 'active' : ''}`}
          data-status="Applied"
          onClick={() => onStatusChange('Applied')}
        >
          <span className="status-dot dot-applied" />
          <span>Applied</span>{' '}
          <span className="filter-count">({appliedCount})</span>
        </button>

        <button
          className={`status-filter-btn ${status === 'Interviewing' ? 'active' : ''}`}
          data-status="Interviewing"
          onClick={() => onStatusChange('Interviewing')}
        >
          <span className="status-dot dot-interviewing" />
          <span>Interviewing</span>{' '}
          <span className="filter-count">({interviewingCount})</span>
        </button>

        <button
          className={`status-filter-btn ${status === 'Offer' ? 'active' : ''}`}
          data-status="Offer"
          onClick={() => onStatusChange('Offer')}
        >
          <span className="status-dot dot-offer" />
          <span>Offer</span>{' '}
          <span className="filter-count">({offerCount})</span>
        </button>

        <button
          className={`status-filter-btn ${status === 'Rejected' ? 'active' : ''}`}
          data-status="Rejected"
          onClick={() => onStatusChange('Rejected')}
        >
          <span className="status-dot dot-rejected" />
          <span>Rejected</span>{' '}
          <span className="filter-count">({rejectedCount})</span>
        </button>

        <div className="filter-separator" aria-hidden="true" />

        <span className="filter-label">Board:</span>
        <div className="filter-select-wrap">
          <select
            id="source-filter-select"
            className="filter-select"
            aria-label="Filter by target job board"
            value={source}
            onChange={(e) => onSourceChange(e.target.value)}
          >
            <option value="all">All Portals</option>
            <option value="Himalayas">Himalayas</option>
            <option value="Wellfound">Wellfound</option>
            <option value="Y Combinator">Y Combinator</option>
            <option value="We Work Remotely">We Work Remotely</option>
          </select>
        </div>
      </div>

      {/* 3. Advanced Table Filters: Setup, Type, and Salary Range */}
      <div
        className="table-advanced-filters"
        id="table-advanced-filters"
        role="region"
        aria-label="Table filters"
      >
        {/* Work Setup Toggle Group */}
        <div className="table-filter-item">
          <span className="filter-label">Setup:</span>
          <div className="toggle-group table-toggle-group">
            {[
              { val: 'Any', label: 'Any' },
              { val: 'Worldwide', label: 'Remote (Worldwide)' },
              { val: 'APAC / Philippines', label: 'Remote (APAC / Philippines)' },
              { val: 'Contractor / B2B', label: 'Contractor / B2B / Deel' },
            ].map((opt) => (
              <button
                key={opt.val}
                type="button"
                className={`toggle-btn table-toggle-btn ${
                  workSetups.includes(opt.val) ? 'selected' : ''
                }`}
                onClick={() => handleToggle(workSetups, opt.val, onWorkSetupsChange)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="filter-separator" aria-hidden="true" />

        {/* Employment Type Toggle Group */}
        <div className="table-filter-item">
          <span className="filter-label">Type:</span>
          <div className="toggle-group table-toggle-group">
            {[
              { val: 'Any', label: 'Any' },
              { val: 'Full-Time', label: 'Full-Time' },
              { val: 'Contract / B2B', label: 'Contract / B2B' },
              { val: 'Part-Time', label: 'Part-Time' },
            ].map((opt) => (
              <button
                key={opt.val}
                type="button"
                className={`toggle-btn table-toggle-btn ${
                  empTypes.includes(opt.val) ? 'selected' : ''
                }`}
                onClick={() => handleToggle(empTypes, opt.val, onEmpTypesChange)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="filter-separator" aria-hidden="true" />

        {/* Salary Range Composite Filter */}
        <div className="table-salary-filter-item">
          <span className="filter-label">Salary:</span>
          <div className="salary-range-wrap table-salary-range-wrap">
            <div className="salary-range-inputs table-salary-inputs">
              <input
                type="text"
                id="table-filter-salary-min"
                className="field-input salary-num-input table-salary-input"
                placeholder="Min"
                autoComplete="off"
                aria-label="Table filter minimum salary"
                value={salaryMin}
                onChange={(e) => onSalaryMinChange(e.target.value)}
              />
              <span className="salary-to-label table-salary-to">to</span>
              <input
                type="text"
                id="table-filter-salary-max"
                className="field-input salary-num-input table-salary-input"
                placeholder="Max"
                autoComplete="off"
                aria-label="Table filter maximum salary"
                value={salaryMax}
                onChange={(e) => onSalaryMaxChange(e.target.value)}
              />
            </div>

            <select
              id="table-filter-salary-currency"
              className="field-select salary-select-currency table-salary-select"
              aria-label="Table filter salary currency"
              value={salaryCurrency}
              onChange={(e) => onSalaryCurrencyChange(e.target.value)}
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
              id="table-filter-salary-period"
              className="field-select salary-select-period table-salary-select"
              aria-label="Table filter salary frequency"
              value={salaryPeriod}
              onChange={(e) => onSalaryPeriodChange(e.target.value)}
            >
              <option value="yearly">Yearly (/yr)</option>
              <option value="monthly">Monthly (/mo)</option>
              <option value="hourly">Hourly (/hr)</option>
            </select>

            <button
              ref={infoBtnRef}
              type="button"
              id="table-salary-info-toggle"
              className={`salary-info-btn table-salary-info-btn ${
                showSalaryPopover ? 'active' : ''
              } ${hasSalaryValues ? 'has-values' : ''}`}
              onClick={() => setShowSalaryPopover((prev) => !prev)}
              title="View currency and period conversions"
              aria-label="View currency and period conversions"
            >
              <svg
                width="13"
                height="13"
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

            {hasCustomFilters && (
              <button
                type="button"
                id="table-filters-reset-btn"
                className="table-filters-reset-btn"
                onClick={onResetFilters}
                title="Reset all active table filters"
                aria-label="Reset all active table filters"
              >
                Reset
              </button>
            )}
          </div>

          {/* Expandable Popover for Table Salary Conversions */}
          <div
            ref={popoverRef}
            id="table-salary-conversion-panel"
            className={`salary-conversion-panel table-salary-popover ${
              showSalaryPopover ? 'open' : ''
            }`}
          >
            {!hasSalaryValues ? (
              <>
                <div className="conv-header">
                  <span className="conv-title">Salary Filter Equivalents</span>
                  <span className="conv-rate">1 USD ≈ ₱58.50 PHP</span>
                </div>
                <div
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-sans)',
                    lineHeight: 1.4,
                  }}
                >
                  Enter a Min or Max salary to see real-time FX conversions across USD, PHP, EUR, and GBP.
                </div>
              </>
            ) : conversions ? (
              <>
                <div className="conv-header">
                  <span className="conv-title">Active Salary Filter Equivalents</span>
                  <span className="conv-rate">1 USD ≈ ₱58.50 PHP</span>
                </div>
                <div className="conv-grid">
                  <div className="conv-card highlight">
                    <span className="conv-card-title">USD Annual</span>
                    <span className="conv-val-main">{conversions.usd.annual}</span>
                    <span className="conv-val-sub">
                      {conversions.usd.monthly} | {conversions.usd.hourly}
                    </span>
                  </div>
                  <div className="conv-card">
                    <span className="conv-card-title">PHP (Philippine Peso)</span>
                    <span className="conv-val-main">{conversions.php.annual}</span>
                    <span className="conv-val-sub">{conversions.php.monthly}</span>
                  </div>
                  <div className="conv-card">
                    <span className="conv-card-title">EUR & GBP</span>
                    <span className="conv-val-main">{conversions.eur.annual}</span>
                    <span className="conv-val-sub">{conversions.gbp.annual}</span>
                  </div>
                </div>
              </>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

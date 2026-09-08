import React, { useState, useMemo } from 'react';
import { Header } from './components/layout/Header';
import { Toolbar } from './components/layout/Toolbar';
import { JobTable } from './components/table/JobTable';
import { FindJobsModal } from './components/modals/FindJobsModal';
import { useJobs } from './hooks/useJobs';
import { useTheme } from './hooks/useTheme';
import { Job, SortConfig } from './lib/types';
import {
  toAnnualUsdValue,
  parseSalaryNum,
  parseSalaryValue,
  parseDateValue,
  getBaseDomain,
  exportUpdatedCsv,
} from './lib/utils';

export function App() {
  // Initialize theme tracking
  useTheme();

  // Supabase data hook (real-time sync + optimistic update)
  const { jobs, loading, updateJobStatus } = useJobs();

  // Filter States
  const [search, setSearch] = useState('');
  const [tier, setTier] = useState('all');
  const [status, setStatus] = useState('all');
  const [source, setSource] = useState('all');
  const [workSetups, setWorkSetups] = useState<string[]>(['Any']);
  const [empTypes, setEmpTypes] = useState<string[]>(['Any']);
  const [salaryMin, setSalaryMin] = useState('');
  const [salaryMax, setSalaryMax] = useState('');
  const [salaryCurrency, setSalaryCurrency] = useState('USD');
  const [salaryPeriod, setSalaryPeriod] = useState('yearly');

  // Sorting State
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    column: 'match_score',
    direction: 'desc',
  });

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Filter and Sort Jobs
  const filteredAndSortedJobs = useMemo(() => {
    // 1. Filter
    const filtered = jobs.filter((j) => {
      const jTier = j.seniority_tier || j.tier || 'Target';
      const matchesTier = tier === 'all' || jTier.toLowerCase() === tier.toLowerCase();
      const matchesStatus = status === 'all' || j.status.toLowerCase() === status.toLowerCase();

      // Setup filter
      let matchesSetup = true;
      if (!workSetups.includes('Any') && workSetups.length > 0) {
        matchesSetup = workSetups.some((s) => j.work_setups && j.work_setups.includes(s));
      }

      // Employment Type filter
      let matchesEmpType = true;
      if (!empTypes.includes('Any') && empTypes.length > 0) {
        matchesEmpType = empTypes.includes(j.employment_type);
      }

      // Salary filter
      let matchesSalary = true;
      const minNum = parseSalaryNum(salaryMin);
      const maxNum = parseSalaryNum(salaryMax);
      const minUsd = toAnnualUsdValue(minNum, salaryCurrency, salaryPeriod);
      const maxUsd = toAnnualUsdValue(maxNum, salaryCurrency, salaryPeriod);

      if (minUsd !== null || maxUsd !== null) {
        if (j.min_salary_usd === null && j.max_salary_usd === null) {
          matchesSalary = false;
        } else {
          const jMin = j.min_salary_usd !== null ? j.min_salary_usd : j.max_salary_usd!;
          const jMax = j.max_salary_usd !== null ? j.max_salary_usd : j.min_salary_usd!;
          const minPass = minUsd === null || jMax >= minUsd;
          const maxPass = maxUsd === null || jMin <= maxUsd;
          matchesSalary = minPass && maxPass;
        }
      }

      // Source filter
      let matchesSource = true;
      if (source !== 'all') {
        matchesSource = Boolean(j.source && j.source.toLowerCase().includes(source.toLowerCase()));
      }

      // Search filter
      const q = search.trim().toLowerCase();
      const baseDomain = getBaseDomain(j.url);
      const skillsStr = Array.isArray(j.matched_skills)
        ? j.matched_skills.join(' ')
        : j.matched_skills || '';

      const matchesSearch =
        !q ||
        j.company.toLowerCase().includes(q) ||
        j.role.toLowerCase().includes(q) ||
        skillsStr.toLowerCase().includes(q) ||
        (j.hiring_contact && j.hiring_contact.toLowerCase().includes(q)) ||
        baseDomain.toLowerCase().includes(q) ||
        j.salary.toLowerCase().includes(q) ||
        (j.cover_letter && j.cover_letter.toLowerCase().includes(q));

      return (
        matchesTier &&
        matchesStatus &&
        matchesSetup &&
        matchesEmpType &&
        matchesSalary &&
        matchesSource &&
        matchesSearch
      );
    });

    // 2. Sort
    filtered.sort((a, b) => {
      let valA: any;
      let valB: any;

      if (sortConfig.column === 'match_score') {
        valA = a.match_score || 0;
        valB = b.match_score || 0;
      } else if (sortConfig.column === 'tier') {
        valA = a.seniority_tier || a.tier || '';
        valB = b.seniority_tier || b.tier || '';
      } else if (sortConfig.column === 'company') {
        valA = a.company.toLowerCase();
        valB = b.company.toLowerCase();
      } else if (sortConfig.column === 'salary') {
        valA = parseSalaryValue(a.salary);
        valB = parseSalaryValue(b.salary);
      } else if (sortConfig.column === 'date') {
        valA = parseDateValue(a.date_posted);
        valB = parseDateValue(b.date_posted);
      } else if (sortConfig.column === 'status') {
        valA = a.status.toLowerCase();
        valB = b.status.toLowerCase();
      } else {
        valA = (a as any)[sortConfig.column];
        valB = (b as any)[sortConfig.column];
      }

      if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
      if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [
    jobs,
    search,
    tier,
    status,
    source,
    workSetups,
    empTypes,
    salaryMin,
    salaryMax,
    salaryCurrency,
    salaryPeriod,
    sortConfig,
  ]);

  const handleSortChange = (column: string) => {
    setSortConfig((prev) => {
      if (prev.column === column) {
        return {
          column,
          direction: prev.direction === 'asc' ? 'desc' : 'asc',
        };
      }
      return { column, direction: 'desc' };
    });
  };

  const handleResetFilters = () => {
    setSalaryMin('');
    setSalaryMax('');
    setSalaryCurrency('USD');
    setSalaryPeriod('yearly');
    setWorkSetups(['Any']);
    setEmpTypes(['Any']);
  };

  const handleDownloadCsv = () => {
    exportUpdatedCsv(filteredAndSortedJobs);
  };

  return (
    <>
      <div className="container">
        {/* Sticky Top Control Hierarchy (Pinned while scrolling) */}
        <div className="sticky-top-panel">
          <Header />
          <Toolbar
            jobs={jobs}
            search={search}
            onSearchChange={setSearch}
            tier={tier}
            onTierChange={setTier}
            status={status}
            onStatusChange={setStatus}
            source={source}
            onSourceChange={setSource}
            workSetups={workSetups}
            onWorkSetupsChange={setWorkSetups}
            empTypes={empTypes}
            onEmpTypesChange={setEmpTypes}
            salaryMin={salaryMin}
            onSalaryMinChange={setSalaryMin}
            salaryMax={salaryMax}
            onSalaryMaxChange={setSalaryMax}
            salaryCurrency={salaryCurrency}
            onSalaryCurrencyChange={setSalaryCurrency}
            salaryPeriod={salaryPeriod}
            onSalaryPeriodChange={setSalaryPeriod}
            onResetFilters={handleResetFilters}
            onFindJobs={() => setIsModalOpen(true)}
            onDownloadCsv={handleDownloadCsv}
          />
        </div>

        {/* Data Table with Resizable Sticky Headers */}
        <JobTable
          jobs={filteredAndSortedJobs}
          loading={loading}
          sortConfig={sortConfig}
          onSortChange={handleSortChange}
          onUpdateStatus={updateJobStatus}
        />
      </div>

      {/* Find Jobs Prompt Generator Modal */}
      <FindJobsModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
}

export default App;

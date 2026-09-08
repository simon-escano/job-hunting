import React from 'react';
import { useFilters } from '../../hooks/useFilters';
import { SegmentedControl } from '../ui/SegmentedControl';
import { Button } from '../ui/Button';
import styles from './Toolbar.module.css';
import { Job } from '../../lib/types';

interface Props {
  onFindJobs: () => void;
  filteredJobs: Job[];
}

export function Toolbar({ onFindJobs, filteredJobs }: Props) {
  const { search, setSearch, tier, setTier } = useFilters();

  const handleDownloadCsv = () => {
    const headers = ['Company', 'Role', 'URL', 'Status', 'Date Posted'];
    const csvContent = [
      headers.join(','),
      ...filteredJobs.map(j => `"${j.company}","${j.role}","${j.url}","${j.status}","${j.date_posted}"`)
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', 'jobs.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className={styles.toolbar}>
      <div className={styles.left}>
        <div className={styles.searchWrap}>
          <span className={styles.searchIcon}>🔍</span>
          <input
            type="text"
            placeholder="Search company or role..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={styles.searchInput}
          />
        </div>
        <SegmentedControl
          options={['All', 'Target', 'Stretch']}
          selected={tier}
          onChange={setTier}
        />
      </div>
      <div className={styles.right}>
        <Button variant="outline" onClick={handleDownloadCsv}>Download CSV</Button>
        <Button variant="accent" onClick={onFindJobs}>Find Jobs</Button>
      </div>
    </div>
  );
}

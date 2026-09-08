import React, { useState } from 'react';
import { useFilters } from '../../hooks/useFilters';
import { ToggleGroup } from '../ui/ToggleGroup';
import { SalaryConversionPopover } from '../ui/SalaryConversionPopover';
import { Button } from '../ui/Button';
import { STATUS_OPTIONS } from '../../lib/constants';
import styles from './FilterBar.module.css';

export function FilterBar() {
  const [expanded, setExpanded] = useState(false);
  const filters = useFilters();

  const handleSalaryChange = (field: string, value: string) => {
    let min = filters.salaryMin;
    let max = filters.salaryMax;
    let curr = filters.salaryCurrency;
    let per = filters.salaryPeriod;
    
    if (field === 'min') min = value;
    if (field === 'max') max = value;
    if (field === 'currency') curr = value;
    if (field === 'period') per = value;
    
    filters.setSalaryRange(min, max, curr, per);
  };

  return (
    <div className={styles.filterBar}>
      <div className={styles.mainRow}>
        <div className={styles.statusFilters}>
          {STATUS_OPTIONS.map(status => {
            const isSelected = filters.statuses.includes(status);
            return (
              <button 
                key={status}
                className={`${styles.statusPill} ${isSelected ? styles.active : ''}`}
                onClick={() => filters.toggleStatus(status)}
              >
                {status}
              </button>
            );
          })}
        </div>
        <button className={styles.expandBtn} onClick={() => setExpanded(!expanded)}>
          {expanded ? 'Fewer Filters' : 'More Filters'}
        </button>
      </div>

      {expanded && (
        <div className={styles.expandedArea}>
          <div className={styles.filterGroup}>
            <label>Work Setup</label>
            <ToggleGroup 
              options={['Any', 'Remote', 'Hybrid', 'On-site']} 
              selected={filters.workSetups} 
              onChange={filters.toggleWorkSetup} 
            />
          </div>
          <div className={styles.filterGroup}>
            <label>Employment Type</label>
            <ToggleGroup 
              options={['Any', 'Full-Time', 'Contract', 'Part-Time']} 
              selected={filters.employmentTypes} 
              onChange={filters.toggleEmploymentType} 
            />
          </div>
          <div className={styles.filterGroup}>
            <label>Salary Minimum</label>
            <div className={styles.salaryInputs}>
              <input 
                type="number" 
                placeholder="Min" 
                value={filters.salaryMin} 
                onChange={(e) => handleSalaryChange('min', e.target.value)} 
                className={styles.input}
              />
              <select 
                value={filters.salaryCurrency} 
                onChange={(e) => handleSalaryChange('currency', e.target.value)}
                className={styles.select}
              >
                {['USD', 'PHP', 'EUR', 'GBP', 'AUD', 'CAD', 'SGD'].map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <select 
                value={filters.salaryPeriod} 
                onChange={(e) => handleSalaryChange('period', e.target.value)}
                className={styles.select}
              >
                <option value="yearly">Yearly</option>
                <option value="monthly">Monthly</option>
                <option value="hourly">Hourly</option>
              </select>
              <SalaryConversionPopover 
                min={filters.salaryMin} 
                max={filters.salaryMax} 
                currency={filters.salaryCurrency} 
                period={filters.salaryPeriod} 
              />
            </div>
          </div>
          <div className={styles.filterGroup}>
            <Button variant="ghost" onClick={filters.resetFilters}>Reset Filters</Button>
          </div>
        </div>
      )}
    </div>
  );
}

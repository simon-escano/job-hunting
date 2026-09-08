import React from 'react';
import styles from './Cells.module.css';
import { Job } from '../../../lib/types';

export function SalaryCell({ job }: { job: Job }) {
  const hasSalary = job.salary && job.salary.toLowerCase() !== 'n/a' && job.salary.toLowerCase() !== 'not specified';
  return (
    <div className={styles.cell}>
      <span className={hasSalary ? styles.salaryText : styles.subtext}>
        {hasSalary ? job.salary : 'N/A'}
      </span>
    </div>
  );
}

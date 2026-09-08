import React from 'react';
import styles from './Cells.module.css';
import { Job } from '../../../lib/types';

export function CompanyCell({ job }: { job: Job }) {
  return (
    <div className={styles.cell}>
      <strong className={styles.companyName}>{job.company}</strong>
      <span className={styles.roleTitle}>{job.role}</span>
      {job.matched_skills && job.matched_skills.length > 0 && (
        <div className={styles.tags}>
          {job.matched_skills.slice(0, 3).map(skill => (
            <span key={skill} className={styles.tag}>{skill}</span>
          ))}
          {job.matched_skills.length > 3 && (
            <span className={styles.tag}>+{job.matched_skills.length - 3}</span>
          )}
        </div>
      )}
    </div>
  );
}

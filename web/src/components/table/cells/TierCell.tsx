import React from 'react';
import styles from './Cells.module.css';
import { Job } from '../../../lib/types';

export function TierCell({ job }: { job: Job }) {
  const isTarget = job.seniority_tier === 'Target';
  return (
    <div className={styles.cell}>
      <span className={`${styles.badge} ${isTarget ? styles.badgeTarget : styles.badgeStretch}`}>
        {job.seniority_tier}
      </span>
      {job.match_score > 0 && (
        <span className={styles.subtext}>Match: {job.match_score}%</span>
      )}
    </div>
  );
}

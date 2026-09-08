import React from 'react';
import styles from './Cells.module.css';
import { Job } from '../../../lib/types';

export function DateCell({ job }: { job: Job }) {
  // Simple relative date formatting
  const date = new Date(job.date_posted);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 3600 * 24));
  
  let text = '';
  if (diffDays === 0) text = 'Today';
  else if (diffDays === 1) text = 'Yesterday';
  else if (diffDays < 30) text = `${diffDays}d ago`;
  else text = date.toLocaleDateString();

  return (
    <div className={styles.cell}>
      <span className={styles.subtext}>{text}</span>
    </div>
  );
}

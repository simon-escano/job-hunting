import React from 'react';
import styles from './Cells.module.css';
import { Job } from '../../../lib/types';
import { STATUS_OPTIONS, STATUS_COLORS } from '../../../lib/constants';

interface Props {
  job: Job;
  onUpdate: (id: string, status: string) => void;
}

export function StatusCell({ job, onUpdate }: Props) {
  const bgColor = STATUS_COLORS[job.status] || STATUS_COLORS['To Review'];

  return (
    <div className={styles.cell}>
      <select
        className={styles.statusSelect}
        style={{ backgroundColor: bgColor }}
        value={job.status}
        onChange={(e) => onUpdate(job.id, e.target.value)}
      >
        {STATUS_OPTIONS.map(opt => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  );
}

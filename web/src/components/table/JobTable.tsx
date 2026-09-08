import React, { useState, useRef, useEffect } from 'react';
import { Job } from '../../lib/types';
import { useColumnResize } from '../../hooks/useColumnResize';
import { JobRow } from './JobRow';
import styles from './JobTable.module.css';

interface Props {
  jobs: Job[];
  loading: boolean;
  onUpdateStatus: (id: string, status: string) => void;
}

export function JobTable({ jobs, loading, onUpdateStatus }: Props) {
  const { columns, handleResize } = useColumnResize();
  const [resizing, setResizing] = useState<{ index: number, startX: number, startWidth: number } | null>(null);

  useEffect(() => {
    if (!resizing) return;
    
    const onMouseMove = (e: MouseEvent) => {
      const diff = e.clientX - resizing.startX;
      handleResize(resizing.index, resizing.startWidth + diff);
    };
    
    const onMouseUp = () => setResizing(null);
    
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [resizing, handleResize]);

  if (loading) {
    return <div className={styles.empty}>Loading jobs...</div>;
  }

  if (jobs.length === 0) {
    return <div className={styles.empty}>No jobs found matching your filters.</div>;
  }

  return (
    <div className={styles.tableContainer}>
      <div className={styles.table}>
        <div className={styles.headerRow}>
          {columns.map((col, idx) => (
            <div key={col.key} className={styles.headerCell} style={{ width: col.width, minWidth: col.minWidth }}>
              {col.label}
              <div 
                className={styles.resizer} 
                onMouseDown={(e) => setResizing({ index: idx, startX: e.clientX, startWidth: col.width })}
              />
            </div>
          ))}
        </div>
        <div className={styles.body}>
          {jobs.map(job => (
            <JobRow key={job.id} job={job} columns={columns} onUpdateStatus={onUpdateStatus} />
          ))}
        </div>
      </div>
    </div>
  );
}

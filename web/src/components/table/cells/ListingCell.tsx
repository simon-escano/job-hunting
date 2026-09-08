import React from 'react';
import styles from './Cells.module.css';
import { Job } from '../../../lib/types';
import { Button } from '../../ui/Button';
import { getBaseDomain } from '../../../lib/utils';

export function ListingCell({ job }: { job: Job }) {
  const domain = getBaseDomain(job.url);
  
  return (
    <div className={styles.cell}>
      <Button 
        size="sm" 
        onClick={() => window.open(job.url, '_blank')}
        className={styles.applyBtn}
      >
        Apply
      </Button>
      <span className={styles.domainText}>{domain}</span>
      <div className={styles.chips}>
        {job.resume_url && (
          <a href={job.resume_url} target="_blank" rel="noreferrer" className={styles.chip}>📄 Resume</a>
        )}
        {job.cover_letter_url && (
          <a href={job.cover_letter_url} target="_blank" rel="noreferrer" className={styles.chip}>✉️ Cover</a>
        )}
      </div>
    </div>
  );
}

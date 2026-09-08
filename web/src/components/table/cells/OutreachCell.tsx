import React from 'react';
import styles from './Cells.module.css';
import { Job } from '../../../lib/types';
import { Button } from '../../ui/Button';

export function OutreachCell({ job }: { job: Job }) {
  const handleCopy = () => {
    if (job.cold_email) {
      navigator.clipboard.writeText(job.cold_email);
    }
  };

  const handleGmail = () => {
    // Basic mailto, ideally extracting email from hiring_contact if exists
    let to = '';
    if (job.hiring_contact && job.hiring_contact.includes('@')) {
      const match = job.hiring_contact.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/);
      if (match) to = match[0];
    }
    const subject = encodeURIComponent(`Application for ${job.role} - Simon Escano`);
    const body = encodeURIComponent(job.cold_email || '');
    window.open(`https://mail.google.com/mail/?view=cm&fs=1&to=${to}&su=${subject}&body=${body}`, '_blank');
  };

  return (
    <div className={styles.cell}>
      <span className={styles.contactText}>{job.hiring_contact || 'No contact info'}</span>
      <div className={styles.actionRow}>
        <Button variant="ghost" size="sm" onClick={handleCopy} disabled={!job.cold_email} title="Copy cold email">
          📋
        </Button>
        <Button variant="ghost" size="sm" onClick={handleGmail} disabled={!job.cold_email} title="Compose in Gmail">
          ✉️ Gmail
        </Button>
      </div>
    </div>
  );
}

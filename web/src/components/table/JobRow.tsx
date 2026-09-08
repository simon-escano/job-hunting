import React from 'react';
import { Job, ColumnConfig } from '../../lib/types';
import { TierCell } from './cells/TierCell';
import { CompanyCell } from './cells/CompanyCell';
import { SalaryCell } from './cells/SalaryCell';
import { DateCell } from './cells/DateCell';
import { ListingCell } from './cells/ListingCell';
import { OutreachCell } from './cells/OutreachCell';
import { StatusCell } from './cells/StatusCell';
import styles from './JobTable.module.css';

interface Props {
  job: Job;
  columns: ColumnConfig[];
  onUpdateStatus: (id: string, status: string) => void;
}

export function JobRow({ job, columns, onUpdateStatus }: Props) {
  return (
    <div className={styles.row}>
      {columns.map(col => {
        return (
          <div key={col.key} className={styles.cellWrapper} style={{ width: col.width, minWidth: col.minWidth }}>
            {col.key === 'tier' && <TierCell job={job} />}
            {col.key === 'companyRole' && <CompanyCell job={job} />}
            {col.key === 'salary' && <SalaryCell job={job} />}
            {col.key === 'datePosted' && <DateCell job={job} />}
            {col.key === 'listing' && <ListingCell job={job} />}
            {col.key === 'outreach' && <OutreachCell job={job} />}
            {col.key === 'status' && <StatusCell job={job} onUpdate={onUpdateStatus} />}
          </div>
        );
      })}
    </div>
  );
}

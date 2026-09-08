import React, { useState } from 'react';
import { useSalaryConversion } from '../../hooks/useSalaryConversion';
import styles from './SalaryConversionPopover.module.css';
import { formatSalaryDisplay } from '../../lib/utils';

interface Props {
  min: string;
  max: string;
  currency: string;
  period: string;
}

export function SalaryConversionPopover({ min, max, currency, period }: Props) {
  const [open, setOpen] = useState(false);
  
  const minNum = min ? parseFloat(min) : null;
  const maxNum = max ? parseFloat(max) : null;
  const conversions = useSalaryConversion(minNum, maxNum, currency, period);

  return (
    <div className={styles.wrapper} onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <span className={styles.icon}>ℹ️</span>
      {open && conversions && (
        <div className={styles.popover}>
          <div className={styles.row}>
            <span>USD Annual:</span>
            <strong>{formatSalaryDisplay(conversions.usdAnnual.min, conversions.usdAnnual.max, 'USD', 'yearly')}</strong>
          </div>
          <div className={styles.row}>
            <span>PHP Monthly:</span>
            <strong>{formatSalaryDisplay(conversions.phpMonthly.min, conversions.phpMonthly.max, 'PHP', 'monthly')}</strong>
          </div>
        </div>
      )}
    </div>
  );
}

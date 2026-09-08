import React from 'react';
import styles from './SegmentedControl.module.css';

interface SegmentedControlProps {
  options: string[];
  selected: string;
  onChange: (val: string) => void;
}

export function SegmentedControl({ options, selected, onChange }: SegmentedControlProps) {
  return (
    <div className={styles.container}>
      {options.map((opt) => (
        <button
          key={opt}
          className={`${styles.segment} ${selected === opt ? styles.active : ''}`}
          onClick={() => onChange(opt)}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

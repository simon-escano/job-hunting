import React from 'react';
import styles from './ToggleGroup.module.css';

interface ToggleGroupProps {
  options: string[];
  selected: string[];
  onChange: (value: string) => void;
  hasAny?: boolean;
}

export function ToggleGroup({ options, selected, onChange, hasAny = true }: ToggleGroupProps) {
  return (
    <div className={styles.group}>
      {options.map((opt) => {
        const isSelected = selected.includes(opt);
        return (
          <button
            key={opt}
            className={`${styles.toggle} ${isSelected ? styles.active : ''}`}
            onClick={() => onChange(opt)}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

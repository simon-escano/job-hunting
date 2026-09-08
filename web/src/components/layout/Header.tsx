import React from 'react';
import { ThemeToggle } from '../ui/ThemeToggle';
import styles from './Header.module.css';

export function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <h1>Job Hunting Pipeline</h1>
      </div>
      <div className={styles.actions}>
        <ThemeToggle />
      </div>
    </header>
  );
}

import React from 'react';
import { useTheme } from '../../hooks/useTheme';

export function Header() {
  const { theme, toggleTheme } = useTheme();

  // Determine if dark is currently active
  const isDark =
    theme === 'dark' ||
    (theme === 'system' &&
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches);

  return (
    <header>
      <div className="brand">
        <div className="brand-mark" aria-hidden="true">
          <svg width="16" height="16" viewBox="0 0 32 32" fill="none">
            <path
              d="M10 10 L16 16 L10 22"
              stroke="var(--accent-lime)"
              stroke-width="3"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <line
              x1="17"
              y1="22"
              x2="22"
              y2="22"
              stroke="var(--accent-lemon)"
              stroke-width="3"
              stroke-linecap="round"
            />
          </svg>
        </div>
        <h1>Job Hunting</h1>
      </div>

      <button
        className="theme-toggle-btn"
        id="theme-toggle"
        onClick={toggleTheme}
        title={`Current theme: ${theme}. Click to toggle.`}
        aria-label="Toggle visual theme"
      >
        {isDark ? (
          /* Sun icon (for dark mode) */
          <svg
            id="icon-sun"
            className="btn-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="5" />
            <line x1="12" y1="1" x2="12" y2="3" />
            <line x1="12" y1="21" x2="12" y2="23" />
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
            <line x1="1" y1="12" x2="3" y2="12" />
            <line x1="21" y1="12" x2="23" y2="12" />
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
          </svg>
        ) : (
          /* Moon icon (for light mode) */
          <svg
            id="icon-moon"
            className="btn-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        )}
      </button>
    </header>
  );
}

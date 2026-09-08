import { ColumnConfig } from './types';

export const CURRENCY_RATES: Record<string, number> = {
  USD: 1,
  PHP: 58.5,
  EUR: 0.92,
  GBP: 0.77,
  AUD: 1.51,
  CAD: 1.36,
  SGD: 1.31,
};

export const PERIOD_MULTIPLIERS: Record<string, number> = {
  yearly: 1,
  monthly: 12,
  hourly: 2080,
};

export const STATUS_OPTIONS = [
  'To Review',
  'Applied',
  'Interviewing',
  'Offered',
  'Rejected',
  'Ghosted',
];

export const STATUS_COLORS: Record<string, string> = {
  'To Review': 'var(--status-toreview)',
  'Applied': 'var(--status-applied)',
  'Interviewing': 'var(--status-interviewing)',
  'Offered': 'var(--status-offered)',
  'Rejected': 'var(--status-rejected)',
  'Ghosted': 'var(--status-ghosted)',
};

export const DEFAULT_COLUMNS: ColumnConfig[] = [
  { key: 'tier', label: 'Tier', width: 100, minWidth: 80 },
  { key: 'companyRole', label: 'Company & Role', width: 250, minWidth: 150 },
  { key: 'salary', label: 'Salary', width: 120, minWidth: 80 },
  { key: 'datePosted', label: 'Date Posted', width: 120, minWidth: 80 },
  { key: 'listing', label: 'Listing & Resume', width: 200, minWidth: 150 },
  { key: 'outreach', label: 'Contact & Outreach', width: 200, minWidth: 150 },
  { key: 'status', label: 'Status', width: 150, minWidth: 100 },
];

export const DEFAULT_JOB_SITES = [
  'https://weworkremotely.com/',
  'https://remoteok.com/',
  'https://startup.jobs/'
];

export const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  PHP: '₱',
  EUR: '€',
  GBP: '£',
  AUD: 'A$',
  CAD: 'C$',
  SGD: 'S$'
};

export const BLACKLISTED_DOMAINS = [
  'turing.com',
  'crossover.com',
  'bairesdev.com'
];

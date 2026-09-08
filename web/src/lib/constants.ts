export const CURRENCY_RATES: Record<string, number> = {
  USD: 1.0,
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
  'Offer',
  'Rejected',
];

export const DEFAULT_COL_WIDTHS: Record<string, number> = {
  tier: 140,
  company: 250,
  salary: 155,
  date: 105,
  listing: 195,
  outreach: 290,
  status: 140,
};

export const DEFAULT_JOB_SITES = `https://himalayas.app/jobs?remote_location=Anywhere
https://wellfound.com/jobs
https://www.workatastartup.com/companies
https://weworkremotely.com/categories/remote-back-end-programming-jobs
https://remoteok.com/remote-dev-jobs
https://jobspresso.co/remote-software-jobs/
https://boards.greenhouse.io
https://jobs.lever.co
https://jobs.ashbyhq.com`;

export const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  PHP: '₱',
  EUR: '€',
  GBP: '£',
  AUD: 'A$',
  CAD: 'C$',
  SGD: 'S$',
};

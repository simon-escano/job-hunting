import { CURRENCY_RATES, CURRENCY_SYMBOLS } from './constants';
import { Job } from './types';

export function parseSalaryNum(val: any): number | null {
  if (val === null || val === undefined || val === '') return null;
  const cleaned = String(val).replace(/,/g, '').trim();
  const n = parseFloat(cleaned);
  return isNaN(n) ? null : n;
}

export function parseSalaryValue(salary: string): number {
  if (!salary || salary === 'N/A' || salary.toLowerCase() === 'undisclosed') return 0;
  const nums = salary.match(/\d+(?:,\d+)*(?:\.\d+)?/g);
  if (!nums) return 0;
  const first = parseFloat(nums[0].replace(/,/g, ''));
  return isNaN(first) ? 0 : first;
}

export function toAnnualUsdValue(val: number | null, currency: string, period: string): number | null {
  if (val === null || isNaN(val)) return null;
  const rate = CURRENCY_RATES[currency] || 1.0;
  let annualLocal = val;
  if (period === 'monthly') annualLocal = val * 12;
  if (period === 'hourly') annualLocal = val * 2080;
  return annualLocal / rate;
}

export function formatRangeText(valA: number | null, valB: number | null, symbol: string, suffix: string): string {
  if (valA !== null && valB !== null) {
    if (valA === valB) {
      return `${symbol}${Math.round(valA).toLocaleString('en-US')} ${suffix}`;
    }
    return `${symbol}${Math.round(valA).toLocaleString('en-US')} to ${symbol}${Math.round(valB).toLocaleString('en-US')} ${suffix}`;
  }
  if (valA !== null) {
    return `${symbol}${Math.round(valA).toLocaleString('en-US')}+ ${suffix}`;
  }
  if (valB !== null) {
    return `Up to ${symbol}${Math.round(valB).toLocaleString('en-US')} ${suffix}`;
  }
  return '';
}

export interface SalaryConversions {
  usd: { annual: string; monthly: string; hourly: string };
  php: { annual: string; monthly: string; hourly: string };
  eur: { annual: string };
  gbp: { annual: string };
  aud: { annual: string };
}

export function computeSalaryConversions(
  minVal: number | null,
  maxVal: number | null,
  currency: string,
  period: string
): SalaryConversions | null {
  const rate = CURRENCY_RATES[currency] || 1.0;

  function toAnnualUsd(val: number | null): number | null {
    if (val === null) return null;
    let annualLocal = val;
    if (period === 'monthly') annualLocal = val * 12;
    if (period === 'hourly') annualLocal = val * 2080;
    return annualLocal / rate;
  }

  const minUsd = toAnnualUsd(minVal);
  const maxUsd = toAnnualUsd(maxVal);

  if (minUsd === null && maxUsd === null) return null;

  return {
    usd: {
      annual: formatRangeText(minUsd, maxUsd, '$', '/yr'),
      monthly: formatRangeText(minUsd ? minUsd / 12 : null, maxUsd ? maxUsd / 12 : null, '$', '/mo'),
      hourly: formatRangeText(minUsd ? minUsd / 2080 : null, maxUsd ? maxUsd / 2080 : null, '$', '/hr'),
    },
    php: {
      annual: formatRangeText(minUsd ? minUsd * 58.5 : null, maxUsd ? maxUsd * 58.5 : null, '₱', '/yr'),
      monthly: formatRangeText(minUsd ? (minUsd * 58.5) / 12 : null, maxUsd ? (maxUsd * 58.5) / 12 : null, '₱', '/mo'),
      hourly: formatRangeText(minUsd ? (minUsd * 58.5) / 2080 : null, maxUsd ? (maxUsd * 58.5) / 2080 : null, '₱', '/hr'),
    },
    eur: {
      annual: formatRangeText(minUsd ? minUsd * 0.92 : null, maxUsd ? maxUsd * 0.92 : null, '€', '/yr'),
    },
    gbp: {
      annual: formatRangeText(minUsd ? minUsd * 0.77 : null, maxUsd ? maxUsd * 0.77 : null, '£', '/yr'),
    },
    aud: {
      annual: formatRangeText(minUsd ? minUsd * 1.51 : null, maxUsd ? maxUsd * 1.51 : null, 'A$', '/yr'),
    },
  };
}

export function parseDateValue(dateStr: string): number {
  if (!dateStr) return 0;
  const match = dateStr.match(/(\d+)\s*([dhwmy])/i);
  if (!match) return 999;
  const num = parseInt(match[1], 10);
  const unit = match[2].toLowerCase();
  if (unit === 'd') return num;
  if (unit === 'w') return num * 7;
  if (unit === 'm') return num * 30;
  if (unit === 'y') return num * 365;
  return num;
}

export function getBaseDomain(url: string): string {
  if (!url) return 'listing';
  try {
    const parsed = new URL(url);
    let domain = parsed.hostname.toLowerCase();
    if (domain.startsWith('www.')) {
      domain = domain.substring(4);
    }
    return domain || 'listing';
  } catch {
    return 'listing';
  }
}

export function exportUpdatedCsv(jobs: Job[]) {
  const headers = [
    'Match & Tier',
    'Company & Role',
    'Salary',
    'Date Posted',
    'Live Listing',
    'Contact Lead',
    'Tailored Resume',
    'Cold Email Snippet',
    'Tailored Cover Letter',
    'Cover Letter PDF',
    'Status',
  ];

  function escapeCsvField(val: any): string {
    if (val === null || val === undefined) return '""';
    const str = String(val).replace(/"/g, '""');
    return `"${str}"`;
  }

  const csvRows = [headers.join(',')];

  jobs.forEach((j) => {
    const row = [
      escapeCsvField(`${j.seniority_tier || j.tier || 'Target'} (${j.match_score}%)`),
      escapeCsvField(`${j.company} - ${j.role}`),
      escapeCsvField(j.salary),
      escapeCsvField(j.date_posted),
      escapeCsvField(j.url),
      escapeCsvField(j.hiring_contact || ''),
      escapeCsvField(j.resume_url || ''),
      escapeCsvField(j.cold_email || ''),
      escapeCsvField(j.cover_letter || ''),
      escapeCsvField(j.cover_letter_url || ''),
      escapeCsvField(j.status),
    ];
    csvRows.push(row.join(','));
  });

  const csvString = csvRows.join('\r\n');
  const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', 'pipeline_updated.csv');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

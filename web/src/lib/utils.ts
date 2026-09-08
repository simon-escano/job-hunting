import { CURRENCY_RATES, PERIOD_MULTIPLIERS, CURRENCY_SYMBOLS } from './constants';

export function parseSalaryValue(salary: string): { min: number | null; max: number | null } {
  const nums = salary.match(/\d+(?:,\d+)*(?:\.\d+)?/g);
  if (!nums) return { min: null, max: null };
  const values = nums.map(n => parseFloat(n.replace(/,/g, '')));
  if (values.length === 1) return { min: values[0], max: null };
  return { min: values[0], max: values[1] };
}

export function toAnnualUsd(value: number, currency: string, period: string): number {
  const inUsd = value / (CURRENCY_RATES[currency] || 1);
  const annual = inUsd * (PERIOD_MULTIPLIERS[period] || 1);
  return annual;
}

export function formatSalaryDisplay(min: number | null, max: number | null, currency: string, period: string): string {
  const sym = CURRENCY_SYMBOLS[currency] || currency;
  const p = period === 'yearly' ? '/yr' : period === 'monthly' ? '/mo' : '/hr';
  if (min !== null && max !== null) return `${sym}${min.toLocaleString()} - ${sym}${max.toLocaleString()}${p}`;
  if (min !== null) return `${sym}${min.toLocaleString()}${p}`;
  return 'N/A';
}

export function parseDateValue(dateStr: string): number {
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? 0 : d.getTime();
}

export function getBaseDomain(url: string): string {
  try {
    const { hostname } = new URL(url);
    return hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
}

export function slugify(text: string): string {
  return text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]+/g, '');
}

export function computeSalaryConversions(min: number | null, max: number | null, currency: string, period: string) {
  if (min === null) return null;
  const annualUsdMin = toAnnualUsd(min, currency, period);
  const annualUsdMax = max ? toAnnualUsd(max, currency, period) : null;
  
  return {
    usdAnnual: { min: annualUsdMin, max: annualUsdMax },
    phpMonthly: { 
      min: (annualUsdMin * CURRENCY_RATES.PHP) / 12, 
      max: annualUsdMax ? (annualUsdMax * CURRENCY_RATES.PHP) / 12 : null 
    }
  };
}

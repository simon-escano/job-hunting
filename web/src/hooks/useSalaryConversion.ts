import { computeSalaryConversions } from '../lib/utils';

export function useSalaryConversion(min: number | null, max: number | null, currency: string, period: string) {
  return computeSalaryConversions(min, max, currency, period);
}

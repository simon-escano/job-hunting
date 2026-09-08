import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { FilterState, Job } from '../lib/types';
import { toAnnualUsd } from '../lib/utils';

interface FiltersStore extends FilterState {
  setSearch: (search: string) => void;
  setTier: (tier: string) => void;
  toggleStatus: (status: string) => void;
  toggleWorkSetup: (setup: string) => void;
  toggleEmploymentType: (type: string) => void;
  setSalaryRange: (min: string, max: string, currency: string, period: string) => void;
  setSource: (source: string) => void;
  resetFilters: () => void;
}

const initialState: FilterState = {
  search: '',
  tier: 'All',
  statuses: [],
  workSetups: ['Any'],
  employmentTypes: ['Any'],
  salaryMin: '',
  salaryMax: '',
  salaryCurrency: 'USD',
  salaryPeriod: 'yearly',
  source: 'All'
};

export const useFilters = create<FiltersStore>()(
  persist(
    (set) => ({
      ...initialState,
      setSearch: (search) => set({ search }),
      setTier: (tier) => set({ tier }),
      toggleStatus: (status) => set((state) => ({
        statuses: state.statuses.includes(status)
          ? state.statuses.filter((s) => s !== status)
          : [...state.statuses, status]
      })),
      toggleWorkSetup: (setup) => set((state) => {
        if (setup === 'Any') return { workSetups: ['Any'] };
        const newSetups = state.workSetups.filter(s => s !== 'Any');
        const finalSetups = newSetups.includes(setup) 
          ? newSetups.filter(s => s !== setup) 
          : [...newSetups, setup];
        return { workSetups: finalSetups.length === 0 ? ['Any'] : finalSetups };
      }),
      toggleEmploymentType: (type) => set((state) => {
        if (type === 'Any') return { employmentTypes: ['Any'] };
        const newTypes = state.employmentTypes.filter(t => t !== 'Any');
        const finalTypes = newTypes.includes(type)
          ? newTypes.filter(t => t !== type)
          : [...newTypes, type];
        return { employmentTypes: finalTypes.length === 0 ? ['Any'] : finalTypes };
      }),
      setSalaryRange: (min, max, currency, period) => set({
        salaryMin: min, salaryMax: max, salaryCurrency: currency, salaryPeriod: period
      }),
      setSource: (source) => set({ source }),
      resetFilters: () => set(initialState)
    }),
    { name: 'job-filters' }
  )
);

export function useFilteredJobs(jobs: Job[]) {
  const filters = useFilters();

  return jobs.filter((job) => {
    // Search
    if (filters.search) {
      const q = filters.search.toLowerCase();
      if (!job.company.toLowerCase().includes(q) && !job.role.toLowerCase().includes(q)) {
        return false;
      }
    }

    // Tier
    if (filters.tier !== 'All' && job.seniority_tier !== filters.tier) {
      return false;
    }

    // Status
    if (filters.statuses.length > 0 && !filters.statuses.includes(job.status)) {
      return false;
    }

    // Work Setup
    if (!filters.workSetups.includes('Any')) {
      if (!job.work_setups || !job.work_setups.some(s => filters.workSetups.includes(s))) {
        return false;
      }
    }

    // Employment Type
    if (!filters.employmentTypes.includes('Any')) {
      if (!job.employment_type || !job.employment_type.some(t => filters.employmentTypes.includes(t))) {
        return false;
      }
    }

    // Salary (Check against job.min_salary_usd / max_salary_usd)
    // If user specified min salary filter:
    if (filters.salaryMin || filters.salaryMax) {
      const filterMinNum = parseFloat(filters.salaryMin) || 0;
      const filterMinUsdAnnual = toAnnualUsd(filterMinNum, filters.salaryCurrency, filters.salaryPeriod);
      // Simplify logic: check if job max is >= filter min
      if (job.max_salary_usd && job.max_salary_usd < filterMinUsdAnnual) {
        return false;
      }
    }

    // Source
    if (filters.source !== 'All' && job.source !== filters.source) {
      return false;
    }

    return true;
  });
}

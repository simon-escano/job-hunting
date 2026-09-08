export interface Job {
  id: string;
  job_hash: string;
  company: string;
  role: string;
  url: string;
  source: string;
  seniority_tier: string;
  match_score: number;
  matched_skills: string[];
  hiring_contact: string | null;
  cold_email: string | null;
  salary: string;
  date_posted: string;
  cover_letter: string | null;
  status: string;
  work_setups: string[];
  employment_type: string[];
  min_salary_usd: number | null;
  max_salary_usd: number | null;
  resume_url: string | null;
  cover_letter_url: string | null;
  created_at: string;
}

export interface FilterState {
  search: string;
  tier: string;
  statuses: string[];
  workSetups: string[];
  employmentTypes: string[];
  salaryMin: string;
  salaryMax: string;
  salaryCurrency: string;
  salaryPeriod: string;
  source: string;
}

export interface SortConfig {
  column: string;
  direction: 'asc' | 'desc';
}

export interface ColumnConfig {
  key: string;
  label: string;
  width: number;
  minWidth: number;
}

export type Theme = 'light' | 'dark' | 'system';

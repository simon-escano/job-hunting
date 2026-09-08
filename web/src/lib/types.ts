export interface Job {
  id: number;
  job_hash: string;
  company: string;
  role: string;
  url: string;
  source: string;
  seniority_tier: 'Target' | 'Stretch' | string;
  tier?: 'Target' | 'Stretch' | string;
  match_score: number;
  matched_skills: string;
  hiring_contact: string | null;
  cold_email: string | null;
  salary: string;
  date_posted: string;
  cover_letter: string | null;
  status: 'To Review' | 'Applied' | 'Interviewing' | 'Offer' | 'Rejected' | string;
  work_setups: string[];
  employment_type: string;
  min_salary_usd: number | null;
  max_salary_usd: number | null;
  resume_url: string | null;
  cover_letter_url: string | null;
  created_at: string;
}

export interface FilterState {
  search: string;
  tier: string;
  status: string;
  source: string;
  workSetups: string[];
  employmentTypes: string[];
  salaryMin: string;
  salaryMax: string;
  salaryCurrency: string;
  salaryPeriod: string;
}

export interface SortConfig {
  column: string;
  direction: 'asc' | 'desc';
}

export type Theme = 'light' | 'dark' | 'system';

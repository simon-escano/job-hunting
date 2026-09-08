import { useEffect, useState } from 'react';
import { supabase, isSupabaseConfigured } from '../lib/supabase';
import { Job } from '../lib/types';

export function useJobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isSupabaseConfigured) {
      setLoading(false);
      setError('Supabase credentials not configured in .env.local. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to connect.');
      return;
    }

    fetchJobs();

    const channel = supabase
      .channel('jobs_changes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'jobs' }, (payload) => {
        if (payload.eventType === 'INSERT') {
          setJobs((prev) => [payload.new as Job, ...prev]);
        } else if (payload.eventType === 'UPDATE') {
          setJobs((prev) => prev.map((j) => (j.id === payload.new.id ? (payload.new as Job) : j)));
        } else if (payload.eventType === 'DELETE') {
          setJobs((prev) => prev.filter((j) => j.id !== payload.old.id));
        }
      })
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  async function fetchJobs() {
    if (!isSupabaseConfigured) return;
    try {
      setLoading(true);
      const { data, error: err } = await supabase
        .from('jobs')
        .select('*')
        .order('created_at', { ascending: false });
      
      if (err) throw err;
      setJobs(data || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function updateJobStatus(id: string, status: string) {
    // Optimistic update
    setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, status } : j)));
    
    const { error: err } = await supabase
      .from('jobs')
      .update({ status })
      .eq('id', id);
      
    if (err) {
      // Revert on error (for simplicity just refetch, or we can leave it)
      fetchJobs();
      throw err;
    }
  }

  return { jobs, loading, error, updateJobStatus };
}

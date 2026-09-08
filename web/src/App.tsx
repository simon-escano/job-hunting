import React, { useState } from 'react';
import { Header } from './components/layout/Header';
import { Toolbar } from './components/layout/Toolbar';
import { FilterBar } from './components/layout/FilterBar';
import { JobTable } from './components/table/JobTable';
import { FindJobsModal } from './components/modals/FindJobsModal';
import { useJobs } from './hooks/useJobs';
import { useFilteredJobs } from './hooks/useFilters';
import { useTheme } from './hooks/useTheme';

function App() {
  // Initialize theme
  useTheme();
  
  const { jobs, loading, updateJobStatus } = useJobs();
  const filteredJobs = useFilteredJobs(jobs);
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <Header />
      <Toolbar onFindJobs={() => setIsModalOpen(true)} filteredJobs={filteredJobs} />
      <FilterBar />
      <JobTable jobs={filteredJobs} loading={loading} onUpdateStatus={updateJobStatus} />
      <FindJobsModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  );
}

export default App;

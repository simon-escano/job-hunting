import React, { useState, useEffect, useRef } from 'react';
import { Job, SortConfig } from '../../lib/types';
import { DEFAULT_COL_WIDTHS } from '../../lib/constants';
import { JobRow } from './JobRow';

const STORAGE_KEY_WIDTHS = 'job_hunting_column_widths';

interface JobTableProps {
  jobs: Job[];
  loading: boolean;
  sortConfig: SortConfig;
  onSortChange: (column: string) => void;
  onUpdateStatus: (id: number, status: string) => void;
}

export function JobTable({
  jobs,
  loading,
  sortConfig,
  onSortChange,
  onUpdateStatus,
}: JobTableProps) {
  // Load saved column widths or use defaults
  const [colWidths, setColWidths] = useState<Record<string, number>>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_WIDTHS);
      if (saved) return { ...DEFAULT_COL_WIDTHS, ...JSON.parse(saved) };
    } catch {}
    return { ...DEFAULT_COL_WIDTHS };
  });

  // Column drag resizing state
  const activeResizeRef = useRef<{
    colId: string;
    startX: number;
    startWidth: number;
  } | null>(null);

  const handleResizeStart = (colId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const currentWidth = colWidths[colId] || DEFAULT_COL_WIDTHS[colId] || 150;
    activeResizeRef.current = {
      colId,
      startX: e.clientX,
      startWidth: currentWidth,
    };
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!activeResizeRef.current) return;
      const { colId, startX, startWidth } = activeResizeRef.current;
      const diff = moveEvent.clientX - startX;
      const newWidth = Math.max(80, startWidth + diff);
      setColWidths((prev) => {
        const next = { ...prev, [colId]: newWidth };
        try {
          localStorage.setItem(STORAGE_KEY_WIDTHS, JSON.stringify(next));
        } catch {}
        return next;
      });
    };

    const handleMouseUp = () => {
      activeResizeRef.current = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const columns = [
    { id: 'tier', label: 'Tier & Match', sortKey: 'match_score' },
    { id: 'company', label: 'Company & Role', sortKey: 'company' },
    { id: 'salary', label: 'Salary', sortKey: 'salary' },
    { id: 'date', label: 'Date Posted', sortKey: 'date' },
    { id: 'listing', label: 'Listing & Resume', sortKey: null },
    { id: 'outreach', label: 'Contact & Outreach', sortKey: null },
    { id: 'status', label: 'Status', sortKey: 'status' },
  ];

  return (
    <div className="table-container" id="table-container">
      <table id="pipeline-table">
        <thead id="table-head">
          <tr>
            {columns.map((col, idx) => {
              const width = colWidths[col.id] || DEFAULT_COL_WIDTHS[col.id] || 150;
              const isSorted = col.sortKey && sortConfig.column === col.sortKey;
              const isLast = idx === columns.length - 1;

              return (
                <th
                  key={col.id}
                  data-col={col.id}
                  className={isSorted ? 'sorted' : ''}
                  style={{ width: `${width}px`, maxWidth: `${width}px` }}
                  onClick={() => col.sortKey && onSortChange(col.sortKey)}
                  title={col.sortKey ? `Click to sort by ${col.label}` : undefined}
                >
                  <div className="th-content">
                    <span className="col-title">{col.label}</span>
                    {col.sortKey && (
                      <span className="sort-arrow">
                        {isSorted
                          ? sortConfig.direction === 'asc'
                            ? '▲'
                            : '▼'
                          : '▼'}
                      </span>
                    )}
                  </div>
                  {!isLast && (
                    <div
                      className="col-resizer"
                      data-col={col.id}
                      onMouseDown={(e) => handleResizeStart(col.id, e)}
                    />
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody id="table-body">
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="empty-row">
                Loading pipeline listings from Supabase...
              </td>
            </tr>
          ) : jobs.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="empty-row">
                No application leads match the selected criteria.
              </td>
            </tr>
          ) : (
            jobs.map((job, idx) => (
              <JobRow
                key={job.id}
                job={job}
                index={idx}
                colWidths={colWidths}
                onUpdateStatus={onUpdateStatus}
                onResizeStart={handleResizeStart}
              />
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

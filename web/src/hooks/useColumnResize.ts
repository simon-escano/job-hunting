import { useState, useCallback, useEffect } from 'react';
import { ColumnConfig } from '../lib/types';
import { DEFAULT_COLUMNS } from '../lib/constants';

export function useColumnResize() {
  const [columns, setColumns] = useState<ColumnConfig[]>(() => {
    const saved = localStorage.getItem('table-columns');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Merge with defaults in case of missing columns
        return DEFAULT_COLUMNS.map(def => {
          const found = parsed.find((p: any) => p.key === def.key);
          return found ? { ...def, width: found.width } : def;
        });
      } catch {
        return DEFAULT_COLUMNS;
      }
    }
    return DEFAULT_COLUMNS;
  });

  useEffect(() => {
    localStorage.setItem('table-columns', JSON.stringify(columns));
  }, [columns]);

  const handleResize = useCallback((index: number, newWidth: number) => {
    setColumns(prev => {
      const next = [...prev];
      const col = next[index];
      next[index] = { ...col, width: Math.max(col.minWidth, newWidth) };
      return next;
    });
  }, []);

  return { columns, handleResize };
}

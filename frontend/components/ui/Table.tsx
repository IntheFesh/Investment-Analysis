import { ReactNode } from 'react';
import clsx from 'clsx';

export interface Column<T> {
  key: string;
  header: ReactNode;
  align?: 'left' | 'right' | 'center';
  width?: string;
  render: (row: T, index: number) => ReactNode;
  className?: string;
  headerClassName?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  getRowKey: (row: T, index: number) => string | number;
  dense?: boolean;
  className?: string;
  empty?: ReactNode;
}

export function DataTable<T>({
  columns,
  rows,
  getRowKey,
  dense,
  className,
  empty,
}: DataTableProps<T>) {
  if (!rows.length && empty) {
    return <div className={clsx('w-full', className)}>{empty}</div>;
  }

  return (
    <div className={clsx('w-full overflow-auto', className)}>
      <table className="w-full text-body-sm tabular">
        <thead>
          <tr className="border-b border-border text-text-tertiary text-caption uppercase tracking-wide">
            {columns.map((col) => (
              <th
                key={col.key}
                style={{ width: col.width, textAlign: col.align ?? 'left' }}
                className={clsx(
                  'font-medium py-2 px-3 first:pl-0 last:pr-0',
                  col.headerClassName
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={getRowKey(row, i)}
              className={clsx(
                'border-b border-border-subtle last:border-b-0 transition-colors hover:bg-surface-sunken/60'
              )}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  style={{ textAlign: col.align ?? 'left' }}
                  className={clsx(
                    dense ? 'py-1.5 px-3' : 'py-2.5 px-3',
                    'first:pl-0 last:pr-0',
                    col.className
                  )}
                >
                  {col.render(row, i)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

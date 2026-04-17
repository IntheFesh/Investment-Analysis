import { DataTable } from '@/components/ui/Table';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { formatCompact } from '@/utils/format';
import type { FundImportEntry } from '@/services/importService';

interface Props {
  rows: FundImportEntry[];
  onChange: (next: FundImportEntry[]) => void;
  showConfidence?: boolean;
  confidences?: Record<string, number>;
}

export function CalibrationTable({ rows, onChange, showConfidence, confidences }: Props) {
  const update = (idx: number, patch: Partial<FundImportEntry>) => {
    const next = rows.map((row, i) => (i === idx ? { ...row, ...patch } : row));
    onChange(next);
  };
  const remove = (idx: number) => onChange(rows.filter((_, i) => i !== idx));

  return (
    <DataTable
      dense
      columns={[
        {
          key: 'code',
          header: '代码',
          render: (row) => (
            <Input
              size="sm"
              value={row.code}
              onChange={(e) =>
                update(rows.indexOf(row), { code: e.target.value.trim() })
              }
            />
          ),
        },
        {
          key: 'name',
          header: '名称',
          render: (row) => (
            <Input
              size="sm"
              value={row.name ?? ''}
              onChange={(e) => update(rows.indexOf(row), { name: e.target.value })}
            />
          ),
        },
        {
          key: 'shares',
          header: '份额',
          align: 'right',
          render: (row) => (
            <Input
              size="sm"
              type="number"
              value={row.shares ?? 0}
              onChange={(e) =>
                update(rows.indexOf(row), { shares: Number(e.target.value) })
              }
            />
          ),
        },
        {
          key: 'market_value',
          header: '市值',
          align: 'right',
          render: (row) => (
            <div className="flex flex-col gap-1">
              <Input
                size="sm"
                type="number"
                value={row.market_value ?? 0}
                onChange={(e) =>
                  update(rows.indexOf(row), { market_value: Number(e.target.value) })
                }
              />
              <span className="text-caption text-text-tertiary text-right tabular">
                {formatCompact(row.market_value)}
              </span>
            </div>
          ),
        },
        ...(showConfidence
          ? [
              {
                key: 'confidence',
                header: 'OCR 置信度',
                align: 'right' as const,
                render: (row: FundImportEntry) => {
                  const c = confidences?.[row.code] ?? 1;
                  return (
                    <Badge tone={c >= 0.85 ? 'up' : c >= 0.6 ? 'warn' : 'down'} size="xs">
                      {Math.round(c * 100)}%
                    </Badge>
                  );
                },
              },
            ]
          : []),
        {
          key: 'actions',
          header: '',
          align: 'right',
          render: (row) => (
            <button
              type="button"
              className="text-body-sm text-text-tertiary hover:text-danger"
              onClick={() => remove(rows.indexOf(row))}
            >
              删除
            </button>
          ),
        },
      ]}
      rows={rows}
      getRowKey={(r, i) => `${r.code}-${i}`}
    />
  );
}
